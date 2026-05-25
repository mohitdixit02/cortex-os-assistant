from cortex_cm.pg.models import UserEvent, Message
from sqlmodel import Session, select
from cortex_cm.pg import engine
from typing import List, Optional, Dict
from uuid import UUID

class EventService:
    def list_events(self, user_id: UUID, offset: int = 0, limit: int = 20, session_id: Optional[str] = None) -> List[UserEvent]:
        with Session(engine) as session:
            statement = select(UserEvent).join(Message).where(Message.user_id == user_id)
            
            if session_id:
                statement = statement.where(Message.session_id == UUID(session_id))
            
            statement = statement.order_by(UserEvent.trigger_time.desc(), UserEvent.created_at.desc()).offset(offset).limit(limit)
            return list(session.exec(statement).all())

    def get_event_counts(self, user_id: UUID) -> Dict[str, int]:
        from sqlalchemy import func
        from datetime import datetime, timezone
        from cortex_cm.pg.enums import EventStatus
        
        with Session(engine) as session:
            # Total reminders created
            total_stmt = select(func.count(UserEvent.id)).join(Message).where(Message.user_id == user_id)
            total_count = session.exec(total_stmt).one()
            
            # Upcoming reminders
            now = datetime.now(timezone.utc)
            upcoming_stmt = (
                select(func.count(UserEvent.id))
                .join(Message)
                .where(Message.user_id == user_id)
                .where(UserEvent.trigger_time > now)
                .where(UserEvent.status == EventStatus.CREATED)
            )
            upcoming_count = session.exec(upcoming_stmt).one()
            
            return {
                "total_reminders": total_count,
                "upcoming_reminders": upcoming_count
            }

event_service = EventService()
