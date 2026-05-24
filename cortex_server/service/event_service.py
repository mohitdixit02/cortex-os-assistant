from cortex_cm.pg.models import UserEvent, Message
from sqlmodel import Session, select
from cortex_cm.pg import engine
from typing import List, Optional
from uuid import UUID

class EventService:
    def list_events(self, user_id: UUID, offset: int = 0, limit: int = 20, session_id: Optional[str] = None) -> List[UserEvent]:
        with Session(engine) as session:
            statement = select(UserEvent).join(Message).where(Message.user_id == user_id)
            
            if session_id:
                statement = statement.where(Message.session_id == UUID(session_id))
            
            statement = statement.order_by(UserEvent.trigger_time.desc(), UserEvent.created_at.desc()).offset(offset).limit(limit)
            return list(session.exec(statement).all())

event_service = EventService()
