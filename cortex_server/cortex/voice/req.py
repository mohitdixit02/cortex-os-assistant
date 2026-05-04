import os
import httpx
from typing import Any, Dict, Optional

DEFAULT_QUEUE_URL = os.getenv("CORTEX_QUEUE_URL", "http://localhost:8001")

async def add_task(
	payload: Any,
	task_name: str,
	task_description: str,
	metadata: Dict[str, Any],
	base_url: Optional[str] = None,
) -> Dict[str, Any]:
	"""Submit a task to the remote Cortex Task Queue service (/add_task).

	Returns the parsed JSON response from the queue service.
	"""
	url = (base_url or DEFAULT_QUEUE_URL).rstrip("/") + "/add_task"
	async with httpx.AsyncClient(timeout=30.0) as client:
		resp = await client.post(
			url,
			json={
				"payload": payload,
				"task_name": task_name,
				"task_description": task_description,
				"metadata": metadata,
			},
		)
		resp.raise_for_status()
		return resp.json()

