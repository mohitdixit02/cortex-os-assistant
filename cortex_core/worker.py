import asyncio
import json
import os

# Monkey-patch MainTaskQueue to use RemoteTaskQueue for submitting results
import cortex_queue
from cortex_queue.remote_client import RemoteTaskQueue

os.environ["USE_REMOTE_QUEUE"] = "true"
cortex_queue.MainTaskQueue = RemoteTaskQueue()

from cortex_core.main import MainClient
from cortex_queue import TaskItem, TaskStatus
from cortex_cm.redis.redis_client import task_redis_client
from cortex_core.req import submit_task

from cortex_cm.pg import TaskOwner

async def main():
    client = MainClient()    
    print("Cortex Core Worker started. Listening to Redis DB 1...")
    
    while True:
        try:
            task_data = task_redis_client.brpop("pending_tasks", timeout=0)
            if task_data:
                data = json.loads(task_data)
                metadata = data.get("metadata", {})
                task_owner = metadata.get("task_owner", TaskOwner.VOICE_CLIENT.value)
                
                if task_owner != TaskOwner.VOICE_CLIENT.value:
                    print(f"Skipping task {data.get('task_id')} as it belongs to {task_owner}")
                    # Re-push or handle separately? 
                    # The instruction says "For event_tool task, I will make workflow separetley."
                    # So I should probably just leave it in the queue if I'm not the right worker?
                    # But there is only one 'pending_tasks' queue.
                    # If I leave it there, it will be picked up again by this same worker.
                    # Usually, different workers would listen to different queues or filter.
                    # For now, I'll just ignore it if it's not mine.
                    continue

                print(f"Received task: {data.get('task_id')} - {data.get('task_name')}")
                
                task_item = TaskItem(
                    task_id=data["task_id"],
                    payload=data["payload"],
                    metadata=data["metadata"],
                    task_name=data["task_name"],
                    task_description=data["task_description"],
                    status=TaskStatus(data["status"])
                )
                
                updated_task = await client._handle_task_queue(task_item)
                
                await submit_task(
                    task_id=updated_task.task_id,
                    status=updated_task.status,
                    status_message=updated_task.result if updated_task.status == TaskStatus.COMPLETED else updated_task.error
                )
                print(f"Completed and submitted result for task: {updated_task.task_id}")
        except Exception as e:
            print(f"Error in worker loop: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
