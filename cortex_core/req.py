import os
import httpx
from typing import Any, Dict, Optional
from cortex_cm.pg.enums import TaskStatus

DEFAULT_QUEUE_URL = os.getenv("CORTEX_QUEUE_URL", "http://localhost:8001")

async def submit_task(
    task_id: str,
    status: TaskStatus,
    status_message: Optional[str] = None,
) -> Dict[str, Any]:
	"""Submit a task to the remote Cortex Task Queue service (/submit_task).

	Returns the parsed JSON response from the queue service.
	"""
	url = (DEFAULT_QUEUE_URL).rstrip("/") + "/submit_task"
	status_value = status.value if hasattr(status, "value") else str(status)
	async with httpx.AsyncClient(timeout=30.0) as client:
		resp = await client.post(
			url,
			json={
				"task_id": task_id,
				"status": status_value,
				"status_message": status_message,
			},
		)
		resp.raise_for_status()
		return resp.json()

