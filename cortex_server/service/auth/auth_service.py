import jwt
import os
from datetime import datetime, timedelta, timezone

# Allow scope changes (e.g. if 'phone' is not granted)
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

from typing import Optional, Dict, Any
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from cortex_cm.utility.config import env
from cortex_cm.redis.redis_client import redis_client
from cortex_cm.pg.models import User
from cortex_cm.pg.req import crud
from sqlmodel import Session
from cortex_cm.pg import engine

class AuthService:
    def __init__(self):
        self.client_config = {
            "web": {
                "client_id": env.GOOGLE_CLIENT_ID,
                "client_secret": env.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [env.GOOGLE_REDIRECT_URI],
            }
        }
        self.scopes = [
            "openid",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
            # "https://www.googleapis.com/auth/calendar",
            # "https://www.googleapis.com/auth/tasks",
        ]

    def get_google_auth_url(self) -> str:
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self.scopes,
            redirect_uri=env.GOOGLE_REDIRECT_URI
        )
        authorization_url, state = flow.authorization_url(
            access_type='offline',
            prompt='consent'
        )
        # Store code_verifier in Redis using state as key
        if hasattr(flow, 'code_verifier'):
            redis_client.set(f"pkce:verifier:{state}", flow.code_verifier, ttl=600)
            
        return authorization_url

    async def handle_google_callback(self, code: str, state: str = None) -> Dict[str, Any]:
        flow = Flow.from_client_config(
            self.client_config,
            scopes=self.scopes,
            redirect_uri=env.GOOGLE_REDIRECT_URI
        )
        
        # Retrieve code_verifier from Redis
        if state:
            code_verifier = redis_client.get(f"pkce:verifier:{state}")
            if code_verifier:
                flow.fetch_token(code=code, code_verifier=code_verifier)
                redis_client.delete(f"pkce:verifier:{state}")
            else:
                flow.fetch_token(code=code)
        else:
            flow.fetch_token(code=code)
            
        credentials = flow.credentials

        # Verify ID Token
        id_info = id_token.verify_oauth2_token(
            credentials.id_token, google_requests.Request(), env.GOOGLE_CLIENT_ID
        )

        google_id = id_info['sub']
        email = id_info['email']
        full_name = id_info.get('name', '')
        profile_picture = id_info.get('picture', '')

        with Session(engine) as session:
            user = crud.get_one(session, User, google_id=google_id)
            if not user:
                user = User(
                    google_id=google_id,
                    email=email,
                    full_name=full_name,
                    profile_picture=profile_picture,
                    google_refresh_token=credentials.refresh_token # TODO: Encrypt
                )
                user = crud.create_one(session, user)
            else:
                if credentials.refresh_token:
                    user.google_refresh_token = credentials.refresh_token # TODO: Encrypt
                    user = crud.update_one(session, user, {"google_refresh_token": user.google_refresh_token})

            user_id = str(user.user_id)

        # Cache access token in Redis
        redis_client.set_access_token(user_id, credentials.token, ttl=3500)

        # Generate local JWT
        local_token = self.create_jwt(user_id)
        
        return {
            "access_token": local_token,
            "user_id": user_id
        }

    def create_jwt(self, user_id: str) -> str:
        payload = {
            "sub": user_id,
            "exp": datetime.now(timezone.utc) + timedelta(days=7),
            "iat": datetime.now(timezone.utc)
        }
        return jwt.encode(payload, env.JWT_SECRET, algorithm=env.JWT_ALGORITHM)

    def verify_jwt(self, token: str) -> Optional[str]:
        try:
            payload = jwt.decode(token, env.JWT_SECRET, algorithms=[env.JWT_ALGORITHM])
            return payload.get("sub")
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None

auth_service = AuthService()
