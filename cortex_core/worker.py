import asyncio
import json

from cortex_queue.dto import TaskItem, TaskStatus
from cortex_cm.redis.redis_client import RedisClient, RedisModeType
from cortex_core.req import submit_task
from cortex_cm.utility.cortex import warmup_all_models

async def main():
    # Eagerly load all models into memory at startup
    warmup_all_models()
    
    # Deferred import to ensure global initializations happen inside the active event loop
    from cortex_core.main import MainClient
    client = MainClient()    
    
    print("Cortex Core Worker started. Listening to Redis DB 1...")
    redis_client = RedisClient.get_client(RedisModeType.TASK)
    
    while True:
        try:
            task_data = redis_client.brpop("pending_tasks", timeout=0)
            if task_data:
                data = json.loads(task_data)
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
                
                await submit_task(task_item=task_item)
                print(f"Completed and submitted result for task: {updated_task.task_id}")
        except Exception as e:
            print(f"Error in worker loop: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
