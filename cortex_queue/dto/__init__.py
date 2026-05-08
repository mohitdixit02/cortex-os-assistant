from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from pydantic import BaseModel
from cortex_cm.pg import TaskStatus
import time

@dataclass
class TaskItem:
    """
    ### Task Queue Item
    Represents a Single Task Item in the Task Queue
    
    **Key Parameters**: \n
    `task_id:` Unique identifier for the task. If not provided, a UUID will be generated. \n
    `payload:` The actual data or parameters associated with the task\n
    `status:` Current status of the task, which can be "queued", "processing", "completed", or "failed". \n
    `result:` The output or result produced by the worker after processing the task. \n
    `error:` If the task fails, this field can store the error message or exception details. \n
    `metadata:` Store any additional information related to the task
    """
    task_id: str
    payload: Any
    task_name: Optional[str] = None
    task_description: Optional[str] = None
    status: TaskStatus = TaskStatus.INITIALIZED
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None

class AddTaskRequest(BaseModel):
    payload: Any
    task_name: str
    task_description: str
    metadata: Dict[str, Any]

__all__ = [
    "TaskItem", 
    "AddTaskRequest", 
]