from db.models import Task
from db.req import crud
from sqlmodel import Session
from db import engine
from typing import List, Optional

class TaskService:
    def list_tasks(self, offset: int = 0, limit: int = 20, task_type: Optional[str] = None) -> List[Task]:
        with Session(engine) as session:
            # Note: models.py doesn't have task_type, but it has task_name.
            # Assuming task_type refers to task_name or a similar filter.
            filters = {}
            if task_type:
                filters['task_name'] = task_type
            return crud.get_many(session, Task, offset=offset, limit=limit, **filters)

task_service = TaskService()
