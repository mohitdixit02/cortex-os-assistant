from cortex_cm.pg.models import ChatSession, Message, User, Task
from cortex_cm.pg.enums import RoleType
from cortex_cm.pg.req import crud
from sqlmodel import Session, select
from cortex_cm.pg import engine
from uuid import UUID
from typing import List, Any, Dict

class ChatService:
    def create_thread(self, user_id: str) -> Dict[str, Any]:
        with Session(engine) as session:
            new_session = ChatSession(user_id=UUID(user_id))
            db_session = crud.create_one(session, new_session)
            res = db_session.model_dump()
            res["display_title"] = "New Conversation"
            return res

    def list_threads(self, user_id: str, offset: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        with Session(engine) as session:
            threads = crud.get_many(session, ChatSession, offset=offset, limit=limit, user_id=UUID(user_id))
            
            results = []
            for thread in threads:
                thread_data = thread.model_dump()
                
                if thread.summary:
                    thread_data["display_title"] = thread.summary
                else:
                    task_stmt = (
                        select(Task.task_name)
                        .join(Message, Task.message_id == Message.message_id)
                        .where(Message.session_id == thread.session_id)
                        .order_by(Task.created_at.asc())
                        .limit(1)
                    )
                    first_task = session.exec(task_stmt).first()
                    
                    if first_task:
                        thread_data["display_title"] = f"Task: {first_task}"
                    else:
                        msg_stmt = (
                            select(Message.content)
                            .where(Message.session_id == thread.session_id, Message.role == RoleType.USER)
                            .order_by(Message.created_at.asc())
                            .limit(1)
                        )
                        first_msg = session.exec(msg_stmt).first()
                        
                        if first_msg:
                            snippet = first_msg[:40] + ("..." if len(first_msg) > 40 else "")
                            thread_data["display_title"] = snippet
                        else:
                            thread_data["display_title"] = "New Conversation"
                        
                results.append(thread_data)
            return results

    def get_messages(self, thread_id: str) -> List[Message]:
        with Session(engine) as session:
            statement = select(Message).where(Message.session_id == UUID(thread_id)).order_by(Message.created_at.asc())
            return list(session.exec(statement).all())

    def delete_thread(self, thread_id: str) -> bool:
        with Session(engine) as session:
            return crud.delete_by_id(session, ChatSession, UUID(thread_id))

    def update_thread_summary(self, thread_id: str, summary: str) -> Dict[str, Any]:
        with Session(engine) as session:
            thread = crud.get_by_id(session, ChatSession, UUID(thread_id))
            if not thread:
                return None
            
            thread.summary = summary
            session.add(thread)
            session.commit()
            session.refresh(thread)
            
            thread_data = thread.model_dump()
            thread_data["display_title"] = summary
            return thread_data

    def get_session_count(self, user_id: str) -> int:
        from sqlalchemy import func
        with Session(engine) as session:
            statement = select(func.count(ChatSession.session_id)).where(ChatSession.user_id == UUID(user_id))
            return session.exec(statement).one()

chat_service = ChatService()
