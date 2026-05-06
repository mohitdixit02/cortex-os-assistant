import asyncio
from cortex_cm.utility.config import env
from cortex_event_tool.main import get_due_events_pg, update_event_status
from cortex_cm.pg import EventStatus, TaskOwner
from cortex_queue.remote_client import RemoteTaskQueue

# Initialize the remote task queue client
queue = RemoteTaskQueue(base_url=env.CORTEX_QUEUE_URL)

async def process_due_events():
    """
    Background worker loop that periodically checks for due events in PostgreSQL
    and submits them to the central task queue for execution.
    """
    print(f"Cortex Event Tool Worker started. Monitoring for due events...")
    while True:
        try:
            # Check for events due within the next 5 minutes
            due_events = get_due_events_pg(time_window_minutes=5)
            
            for event in due_events:
                print(f"Found due event: {event.id} - {event.name}. Submitting to queue.")
                
                # Prepare the task payload
                payload = {
                    "event_id": str(event.id),
                    "name": event.name,
                    "event_info": event.event_info,
                    "event_description": event.event_description,
                    "trigger_time": event.trigger_time.isoformat()
                }
                
                # Prepare metadata for task queue routing and ownership
                metadata = {
                    "user_id": str(event.user_id),
                    "session_id": str(event.session_id),
                    "task_type": "tool_execution",
                    "task_owner": TaskOwner.EVENT_TOOL.value
                }
                
                # Add task to the central queue
                try:
                    await queue.add_task(
                        payload=payload,
                        task_name=f"EVENT_{event.name}",
                        task_description=event.event_description or event.name,
                        **metadata
                    )
                    
                    # If submission is successful, update status to QUEUED in PG and Redis
                    update_event_status(event.id, EventStatus.QUEUED)
                    print(f"Successfully queued event: {event.id}")
                    
                except Exception as sub_err:
                    print(f"Failed to submit task for event {event.id}: {sub_err}")
                
        except Exception as e:
            print(f"Error in event worker loop: {e}")
            
        # Wait for 60 seconds before the next check to avoid excessive DB load
        await asyncio.sleep(60)

if __name__ == "__main__":
    try:
        asyncio.run(process_due_events())
    except KeyboardInterrupt:
        print("Event worker stopped by user.")
