from cortex_cm.pg.models import UserEvent, Message
from sqlmodel import Session, select
from cortex_cm.pg import engine
from typing import List
from uuid import UUID

class EventService:
    def list_events(self, user_id: UUID, offset: int = 0, limit: int = 20) -> List[UserEvent]:
        with Session(engine) as session:
            # Join with Message to filter by user_id
            statement = select(UserEvent).join(Message).where(Message.user_id == user_id)
            statement = statement.order_by(UserEvent.trigger_time.desc()).offset(offset).limit(limit)
            return list(session.exec(statement).all())

event_service = EventService()
