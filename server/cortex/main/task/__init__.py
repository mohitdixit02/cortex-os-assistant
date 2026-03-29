import asyncio
import threading
import time
from logger import logger
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional
from utility.cortex.config import task_queue_config
from enum import Enum

class TaskStatus(Enum):
    """Enumeration for Task Statuses in the Task Queue."""
    INITIALIZED = "initialized"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class TaskItem:
    """
    ### Task Queue Item
    Represents a Single Task Item in the Task Queue
    
    **Key Parameters**: \n
    `task_id:` Unique identifier for the task. If not provided, a UUID will be generated. \n
    `payload:` The actual data or parameters associated with the task\n
    `status:` Current status of the task, which can be "queued", "processing", "completed", or "failed". \n
    `result:` The output or result produced by the worker after processing the task. \
    `error:` If the task fails, this field can store the error message or exception details. \n
    `metadata:` Store any additional information related to the task
    """
    task_id: str
    payload: Any
    task_name: Optional[str] = None
    status: TaskStatus = TaskStatus.INITIALIZED
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    finished_at: Optional[float] = None


class TaskQueue:
    """
    ## Task Queue
    A Thread-Safe Task Queue implementation that allows asynchronous producers to submit tasks and asynchronous consumers (workers) to pick and process tasks concurrently. \n
    Implemented to keep the Producer responsive while Consumer handle complex tasks in background.
    
    ### For Producers: \n
    `add_task` - Add a new task to the queue with optional metadata. \n
    `wait_completed_task` - Wait for a task to be completed (either successfully or failed) and retrieve its result. \n
    
    ### For Consumers: \n
    `pick_task` - Pick the next available task from the queue for processing, with optional timeout. \n
    `submit_task` - After processing a task, submit the result back to the queue, marking it as completed or failed. \n
    
    ### Additional Utilities: \n
    `get_task_snapshot` - Retrieve the current state and information of a specific task using its unique identifier. \n
    `is_active` - Check if the internal event loop thread is alive and running. \n
    `exit` - Shut down the task queue, stopping the internal event loop and thread. \n
    
    **For more details on each method, please refer to the respective function documentation**
    """

    # //pending// queue max size move in config
    def __init__(self):
        self.maxsize = max(1, task_queue_config.get("max_queue_size")) # setting 0 will make it infinite
        self.loop = asyncio.new_event_loop()
        self._ready = threading.Event()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._ready.wait() # Flag for Queues and Loop are ready or not
        logger.info("TaskQueue initialized...")

    def _run_loop(self) -> None:
        """
        Callback for Thread function to start loop and create queues when thread is launched.
        """
        asyncio.set_event_loop(self.loop)
        self._pending_queue: asyncio.Queue[TaskItem] = asyncio.Queue(maxsize=self.maxsize)
        self._completed_queue: asyncio.Queue[TaskItem] = asyncio.Queue(maxsize=self.maxsize)
        self._tasks: Dict[str, TaskItem] = {}
        self._ready.set()
        self.loop.run_forever()

    async def is_active(self) -> bool:
        """Check if the internal event loop thread is alive and running."""
        return self._thread.is_alive() and self.loop.is_running()

    async def _add_task_to_queue(self, task: TaskItem) -> TaskItem:
        """Internal utility to submit a new task to the pending queue."""
        self._tasks[task.task_id] = task
        await self._pending_queue.put(task)
        return task

    # Since every task is independent, we can't block thread using fut.result() (blocking function)
    # so we use wrap_future to await it, making it non-blocking
    async def add_task(
        self, 
        payload: Any, 
        task_id: Optional[str] = None, 
        task_name: Optional[str] = None, 
        **metadata: Any
        ) -> TaskItem:
        """
        ### Add New Task
        **Utility for Producer**:
        Add a new task to the pending queue, for the consumer to pick and process. \n
        
        **Input Parameters**: \n
        - `payload`: The actual data or parameters associated with the task which the consumer will process. \n
        - `task_id`: Optional unique identifier for the task. If not provided, a UUID will be generated automatically. \n
        - `metadata`: Additional key-value pairs that can be associated with the task for tracking or processing purposes. \n
        - `task_name`: An optional human-readable name for the task \n
        """
        item = TaskItem(
            task_id=task_id or str(uuid.uuid4()),
            payload=payload,
            metadata=dict(metadata),
            task_name=task_name,
            status=TaskStatus.QUEUED
        )
        fut = asyncio.run_coroutine_threadsafe(self._add_task_to_queue(item), self.loop)
        return await asyncio.wrap_future(fut)

    async def _pick_task(self, timeout: Optional[float]) -> Optional[TaskItem]:
        """Internal Utility to pick next task with optional timeout."""
        # Wait till a task is available
        if timeout is None:
            task = await self._pending_queue.get()
        else:
        # Wait till a task is available or timeout occurs
            try:
                task = await asyncio.wait_for(self._pending_queue.get(), timeout=timeout)
            except asyncio.TimeoutError:
                return None

        task.status = TaskStatus.PROCESSING
        task.started_at = time.time()
        return task

    async def pick_task(self, timeout: Optional[float] = None) -> Optional[TaskItem]:
        """
        ### Pick Next task
        **Utility for Consumer**:
        Pick the next available task from the pending queue for processing. \n
        
        `Timeout` is optional
        - If not provided, it will wait until a task is available. \n
        - If provided, it will wait for the specified time and return None if no task is available within that time frame. \n
        """
        fut = asyncio.run_coroutine_threadsafe(self._pick_task(timeout), self.loop)
        return await asyncio.wrap_future(fut)

    async def _finalize_task(
        self,
        task_id: str,
        status: TaskStatus,
        result: Any = None,
        error: Optional[str] = None,
    ) -> TaskItem:
        """Internal Utility to submit task result and move it to completed queue."""
        task = self._tasks.get(task_id)
        if task is None:
            raise KeyError(f"Task not found: {task_id}")

        task.status = status
        task.result = result
        task.error = error
        task.finished_at = time.time()
        await self._completed_queue.put(task)
        return task
    
    async def submit_task(
        self,
        task_id: str,
        status: TaskStatus,
        status_message: Optional[str] = None,
    ) -> TaskItem:
        """
        ### Submit Task Result
        **Utility for Consumer**:
        After processing a task, the consumer can submit the result back to the queue, marking it as completed or failed. \n
        
        **Input Parameters**: \n
        - `task_id`: The unique identifier of the task being submitted. \n
        - `status`: The final status of the task, which can be either "completed" or "failed". \n
        - `status_message`: An optional message providing additional information about the task result or failure reason. \n
        
        **Returns**: \n
        - The updated TaskItem with the new status and result/error information.
        """
        if status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            raise ValueError("Status must be either 'completed' or 'failed'")
        
        fut = asyncio.run_coroutine_threadsafe(
            self._finalize_task(
                task_id=task_id, 
                status=status, 
                result=status_message if status == TaskStatus.COMPLETED else None, 
                error=status_message if status == TaskStatus.FAILED else None
            ), self.loop
        )
        return await asyncio.wrap_future(fut)

    async def _wait_completed(self, timeout: Optional[float]) -> Optional[TaskItem]:
        if timeout is None:
            return await self._completed_queue.get()
        try:
            return await asyncio.wait_for(self._completed_queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            return None

    async def wait_completed_task(self, timeout: Optional[float] = None) -> Optional[TaskItem]:
        """
        ### Wait for Completed Task
        **Utility for Producer**:
        Wait for a task to be completed (can be successful or failed) and retrieve its result. \n
        `Timeout` is optional
        - If not provided, it will wait until a completed task is available. \n
        - If provided, it will wait for the specified time and return None if no completed task is available within that time frame. \n
        """
        fut = asyncio.run_coroutine_threadsafe(self._wait_completed(timeout), self.loop)
        return await asyncio.wrap_future(fut)

    async def get_task_snapshot(self, task_id: str) -> Optional[TaskItem]:
        """
        ### Get Task by ID
        **Utility for Producer/Consumer**:
        Retrieve the current state and information of a specific task using its unique identifier. \n
        """

        async def _get() -> Optional[TaskItem]:
            return self._tasks.get(task_id)

        fut = asyncio.run_coroutine_threadsafe(_get(), self.loop)
        return await asyncio.wrap_future(fut)

    def exit(self) -> None:
        """
        ### Exit the Task Queue
        It will close the internal Task Queue loop and Thread
        
        **Note**:
        Calling this will lead to loss of all pending tasks and should be `used with caution`, typically during application shutdown.
        """
        if self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self._thread.is_alive():
            self._thread.join(timeout=2)

MainTaskQueue = TaskQueue()
