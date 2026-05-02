from fastapi import APIRouter, Depends, HTTPException, Query, Response
from service.auth.auth_service import auth_service
from service.auth.auth_dependency import get_current_user_id
from utility.redis_client import redis_client
from controller.requestModels import TokenResponse
from db import engine, User
from db.req import crud
from sqlmodel import Session

router = APIRouter(prefix="/v1/auth", tags=["Auth"])

@router.get("/me")
async def get_me(user_id: str = Depends(get_current_user_id)):
    """Get current user profile."""
    with Session(engine) as session:
        user = crud.get_by_id(session, User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "user_id": str(user.user_id),
            "email": user.email,
            "full_name": user.full_name,
            "profile_picture": user.profile_picture
        }

@router.get("/google/authorize")
async def authorize():
    """Generate and return the Google OAuth2 authorization URL."""
    url = auth_service.get_google_auth_url()
    return {"url": url}

@router.post("/google/callback", response_model=TokenResponse)
async def callback(code: str = Query(...), state: str = Query(None)):
    """Handle the redirection from Google."""
    result = await auth_service.handle_google_callback(code, state)
    return TokenResponse(access_token=result["access_token"])

@router.post("/logout")
async def logout(user_id: str = Depends(get_current_user_id)):
    """Clear the user session."""
    redis_client.delete_access_token(user_id)
    return {"message": "Logged out successfully"}
