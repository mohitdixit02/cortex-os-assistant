from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from service.auth.auth_dependency import get_current_user_id
from service.task_service import task_service
from controller.requestModels import TaskResponse

router = APIRouter(prefix="/v1/tasks", tags=["Tasks"])

@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    user_id: str = Depends(get_current_user_id),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    task_type: Optional[str] = Query(None)
):
    """Retrieve all executed tasks/tools with pagination."""
    offset = (page - 1) * limit
    tasks = task_service.list_tasks(offset=offset, limit=limit, task_type=task_type)
    return tasks
