import os
import httpx
from typing import Any, Dict, Optional
from dataclasses import asdict
from cortex_queue.dto import TaskItem

QUEUE_URL = os.getenv("CORTEX_QUEUE_URL")
ADD_TASK_URL = f"{QUEUE_URL}/api/queue/add_task"

async def add_task(
	payload: Any,
	task_name: str,
	task_description: str,
	metadata: Dict[str, Any],
) -> Dict[str, Any]:
	"""Submit a task to the remote Cortex Task Queue service (/add_task).

	Returns the parsed JSON response from the queue service.
	"""
	async with httpx.AsyncClient(timeout=30.0) as client:
		resp = await client.post(
			ADD_TASK_URL,
			json={
				"payload": payload,
				"task_name": task_name,
				"task_description": task_description,
				"metadata": metadata,
			},
		)
		resp.raise_for_status()
		return resp.json()

async def submit_task(
	task_item: TaskItem,
) -> Dict[str, Any]:
	"""Submit a task result to the remote Cortex Task Queue service (/submit_task).

	Returns the parsed JSON response from the queue service.
	"""
	url = QUEUE_URL.rstrip("/") + "/api/queue/submit_task"
	async with httpx.AsyncClient(timeout=30.0) as client:
		resp = await client.post(
			url,
			json=asdict(task_item)
		)
		resp.raise_for_status()
		return resp.json()

async def get_task_result(
	task_id: str,
) -> Optional[Dict[str, Any]]:
	"""Retrieve the result of a task from the remote Cortex Task Queue service."""
	url = QUEUE_URL.rstrip("/") + f"/api/queue/get_result/{task_id}"
	async with httpx.AsyncClient(timeout=30.0) as client:
		resp = await client.get(url)
		if resp.status_code == 404:
			return None
		resp.raise_for_status()
		return resp.json()
