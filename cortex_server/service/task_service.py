from cortex_cm.pg.enums import TaskOwner
from cortex_cm.pg.models import Task
from cortex_cm.pg.req import crud
from sqlmodel import Session
from cortex_cm.pg import engine
from typing import List, Optional

class TaskService:
    def list_tasks(self, offset: int = 0, limit: int = 20, task_type: Optional[str] = None) -> List[Task]:
        with Session(engine) as session:
            # Note: models.py doesn't have task_type, but it has task_name.
            # Assuming task_type refers to task_name or a similar filter.
            filters = {}
            task_owner = None
            if task_type == "tool_execution":
                task_owner = TaskOwner.EVENT_TOOL.value
            elif task_type == "query":
                task_owner = TaskOwner.VOICE_CLIENT.value

            if task_owner:
                filters['task_owner'] = task_owner

            return crud.get_many(session, Task, offset=offset, limit=limit, **filters)

task_service = TaskService()
