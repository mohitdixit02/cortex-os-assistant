from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from utility.redis_client import redis_client
from utility.config import env
from db.models import User
from db.req import crud
from sqlmodel import Session
from db import engine
from typing import Optional

class GoogleServiceBuilder:
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.access_token = redis_client.get_access_token(user_id)
        self.refresh_token = self._get_refresh_token_from_db()

    def _get_refresh_token_from_db(self) -> Optional[str]:
        with Session(engine) as session:
            user = crud.get_by_id(session, User, self.user_id)
            if user:
                return user.google_refresh_token # TODO: Decrypt
        return None

    def _get_credentials(self) -> Credentials:
        creds = Credentials(
            token=self.access_token,
            refresh_token=self.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=env.GOOGLE_CLIENT_ID,
            client_secret=env.GOOGLE_CLIENT_SECRET,
            scopes=[
                "https://www.googleapis.com/auth/calendar",
                "https://www.googleapis.com/auth/tasks",
            ]
        )

        if not creds.valid:
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Update Redis with new access token
                redis_client.set_access_token(self.user_id, creds.token, ttl=3500)
            else:
                raise Exception("Google credentials are invalid and cannot be refreshed.")
        
        return creds

    def build_calendar_service(self):
        creds = self._get_credentials()
        return build('calendar', 'v3', credentials=creds)

    def build_tasks_service(self):
        creds = self._get_credentials()
        return build('tasks', 'v1', credentials=creds)

class GoogleCalendarService:
    def __init__(self, builder: GoogleServiceBuilder):
        self.service = builder.build_calendar_service()

    async def list_events(self, days: int = 7):
        from datetime import datetime, timedelta, timezone
        now = datetime.now(timezone.utc).isoformat()
        later = (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()
        
        events_result = self.service.events().list(
            calendarId='primary', timeMin=now, timeMax=later,
            singleEvents=True, orderBy='startTime'
        ).execute()
        return events_result.get('items', [])

    async def create_event(self, summary: str, start_time: str, end_time: str, description: str = None, reminders: list = None):
        if reminders is None:
            reminders = {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            }
        
        event = {
            'summary': summary,
            'description': description,
            'start': {'dateTime': start_time},
            'end': {'dateTime': end_time},
            'reminders': reminders,
        }
        return self.service.events().insert(calendarId='primary', body=event).execute()

    async def delete_event(self, event_id: str):
        self.service.events().delete(calendarId='primary', eventId=event_id).execute()

class GoogleTasksService:
    def __init__(self, builder: GoogleServiceBuilder):
        self.service = builder.build_tasks_service()

    async def create_reminder(self, title: str, notes: str = None, due: str = None):
        task = {
            'title': title,
            'notes': notes,
            'due': due
        }
        return self.service.tasks().insert(tasklist='@default', body=task).execute()
