import asyncio
import httpx
from uuid import UUID
from cortex_cm.utility.config import env
from cortex_event_tool.main import get_due_events, remove_event_from_worker_queue
from cortex_cm.pg import EventStatus, TaskOwner

async def process_due_events():
    """
    Background worker loop that periodically checks for due events in Redis
    and submits them to the central task queue for execution.
    """
    print(f"Cortex Event Tool Worker started. Monitoring for due events...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            try:
                # Check for events due within the next 5 minutes using Redis ZSET
                due_events = get_due_events(time_window_minutes=5)
                
                for event in due_events:
                    # Filter for only CREATED events if Redis returns others
                    if event.get("status") != EventStatus.CREATED.value:
                        continue

                    print(f"Found due event: {event['id']} - {event['name']}. Submitting to queue.")
                    
                    # Prepare the task payload
                    payload = {
                        "event_id": event['id'],
                        "name": event['name'],
                        "event_info": event.get('event_info'),
                        "event_description": event.get('event_description'),
                        "trigger_time": event['trigger_time']
                    }
                    
                    # Prepare metadata for task queue routing and ownership
                    metadata = {
                        "user_id": event['user_id'],
                        "session_id": event['session_id'],
                        "task_type": "tool_execution",
                        "task_owner": TaskOwner.EVENT_TOOL.value
                    }
                    
                    # Add task to the central queue via direct HTTP call
                    try:
                        response = await client.post(
                            f"{env.CORTEX_QUEUE_URL}/add_task",
                            json={
                                "payload": payload,
                                "task_name": f"EVENT_{event['name']}",
                                "task_description": event.get('event_description') or event['name'],
                                "metadata": metadata
                            }
                        )
                        response.raise_for_status()
                        
                        # Once submitted, delete from redis worker queue immediately
                        # Task Queue will later update PG status via its own callback
                        remove_event_from_worker_queue(event['id'])
                        print(f"Successfully submitted and cleared from worker queue: {event['id']}")
                        
                    except Exception as sub_err:
                        print(f"Failed to submit task for event {event['id']}: {sub_err}")
                
            except Exception as e:
                print(f"Error in event worker loop: {e}")
                
            # Wait for 60 seconds before the next check
            await asyncio.sleep(60)

if __name__ == "__main__":
    try:
        asyncio.run(process_due_events())
    except KeyboardInterrupt:
        print("Event worker stopped by user.")
