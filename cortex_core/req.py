import os
import httpx
from typing import Any, Dict, Optional
from cortex_cm.pg.enums import TaskStatus
from cortex_queue.dto import TaskItem

DEFAULT_QUEUE_URL = os.getenv("CORTEX_QUEUE_URL", "http://localhost:8001")

async def submit_task(
    task_item: TaskItem,
) -> Dict[str, Any]:
	"""Submit a task to the remote Cortex Task Queue service (/submit_task).

	Returns the parsed JSON response from the queue service.
	"""
	url = (DEFAULT_QUEUE_URL).rstrip("/") + "/submit_task"
	async with httpx.AsyncClient(timeout=30.0) as client:
		resp = await client.post(
			url,
			json=task_item.dict()
		)
		resp.raise_for_status()
		return resp.json()

