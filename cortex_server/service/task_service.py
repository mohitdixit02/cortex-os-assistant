from cortex_cm.pg.enums import TaskOwner
from cortex_cm.pg.models import Task, Message
from cortex_cm.pg.req import crud
from sqlmodel import Session, select
from cortex_cm.pg import engine
from typing import List, Optional
from uuid import UUID

class TaskService:
    def list_tasks(self, user_id: str, offset: int = 0, limit: int = 20, task_type: Optional[str] = None, session_id: Optional[str] = None) -> List[Task]:
        with Session(engine) as session:
            filters = {}
            if task_type == "tool_execution":
                filters['task_owner'] = TaskOwner.EVENT_TOOL.value
            elif task_type == "query":
                filters['task_owner'] = TaskOwner.VOICE_CLIENT.value

            statement = select(Task).join(Message).where(Message.user_id == UUID(user_id))
            
            if session_id:
                statement = statement.where(Message.session_id == UUID(session_id))
            
            if filters:
                statement = statement.filter_by(**filters)
                
            statement = statement.order_by(Task.created_at.desc()).offset(offset).limit(limit)
            return list(session.exec(statement).all())

task_service = TaskService()
