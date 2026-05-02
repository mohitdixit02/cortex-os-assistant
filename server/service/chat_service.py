from db.models import ChatSession, Message, User
from db.req import crud
from sqlmodel import Session, select
from db import engine
from uuid import UUID
from typing import List

class ChatService:
    def create_thread(self, user_id: str) -> ChatSession:
        with Session(engine) as session:
            new_session = ChatSession(user_id=UUID(user_id))
            return crud.create_one(session, new_session)

    def list_threads(self, user_id: str, offset: int = 0, limit: int = 20) -> List[ChatSession]:
        with Session(engine) as session:
            return crud.get_many(session, ChatSession, offset=offset, limit=limit, user_id=UUID(user_id))

    def get_messages(self, thread_id: str) -> List[Message]:
        with Session(engine) as session:
            return crud.get_many(session, Message, session_id=UUID(thread_id))

    def delete_thread(self, thread_id: str) -> bool:
        with Session(engine) as session:
            return crud.delete_by_id(session, ChatSession, UUID(thread_id))

chat_service = ChatService()
