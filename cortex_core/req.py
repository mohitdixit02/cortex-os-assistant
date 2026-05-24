import os
from dataclasses import asdict
import httpx
from typing import Any, Dict
from cortex_queue.dto import TaskItem

QUEUE_URL = os.getenv("CORTEX_QUEUE_URL")
SUBMIT_QUEUE_URL = f"{QUEUE_URL}/api/queue/submit_task"

async def submit_task(
    task_item: TaskItem,
) -> Dict[str, Any]:
	"""Submit a task to the remote Cortex Task Queue service (/submit_task).

	Returns the parsed JSON response from the queue service.
	"""
	try:
		async with httpx.AsyncClient(timeout=30.0) as client:
			resp = await client.post(
				SUBMIT_QUEUE_URL,
				json=asdict(task_item)
			)
			resp.raise_for_status()
			return resp.json()
	except Exception as e:
		print(f"[CORTEX_CORE] Failed to submit task {task_item.task_id} to queue: {e}")
		return {"status": "error", "message": str(e)}

