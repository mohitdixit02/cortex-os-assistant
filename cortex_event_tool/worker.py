import asyncio
import httpx
from uuid import UUID
from cortex_cm.utility.config import env
from cortex_event_tool.main import get_due_events, remove_event
from cortex_cm.pg import EventStatus, TaskOwner
from datetime import datetime, timedelta, timezone
from dateutil import tz
from crontab import CronTab

from cortex_cm.utility.logger import get_logger
logger = get_logger("EVENT_TOOL_WORKER")

SUBMIT_TASK_URL = f"{env.CORTEX_QUEUE_URL}/api/queue/add_task"
TIME_WINDOW_MINUTES = 5

async def check_and_process_events(client: httpx.AsyncClient):
    """
    Core logic to check for due events and submit them to the queue.
    """
    try:
        # Logging with explicit UTC and Local distinction
        now_utc = datetime.now(timezone.utc)
        local_tz = tz.tzlocal()
        now_local = datetime.now(local_tz)
        
        offset = now_local.utcoffset()
        if offset == timedelta(0):
            timestamp_str = f"[System Time (UTC): {now_utc.strftime('%Y-%m-%d %H:%M:%S')}]"
        else:
            timestamp_str = f"[Local: {now_local.strftime('%Y-%m-%d %H:%M:%S %z %Z')}, UTC: {now_utc.strftime('%Y-%m-%d %H:%M:%S %Z')}]"
        
        logger.info(f"Worker run at: {timestamp_str} - Checking for events due within the next {TIME_WINDOW_MINUTES} minutes.")
        
        # Check for events due within the next 5 minutes using Redis ZSET
        due_events = get_due_events(time_window_minutes=TIME_WINDOW_MINUTES)
        
        if not due_events:
            logger.info("No due events found at this time.")
            return

        for event in due_events:
            if event.get("status") != EventStatus.CREATED.value:
                continue

            logger.info(f"Found due event: {event['id']} - {event['name']}. Submitting to queue.")
            
            payload = {
                "event_id": event['id'],
                "name": event['name'],
                "event_description": event.get('event_description'),
                "trigger_time": event['trigger_time']
            }
            
            metadata = {
                "message_id": str(event['message_id']),
                "task_owner": TaskOwner.EVENT_TOOL.value
            }
            
            try:
                response = await client.post(
                    SUBMIT_TASK_URL,
                    json={
                        "payload": payload,
                        "task_name": f"EVENT_{event['name']}",
                        "task_description": event.get('event_description') or event['name'],
                        "metadata": metadata
                    }
                )
                response.raise_for_status()
                remove_event(event['id'])
                logger.info(f"Successfully submitted and cleared from worker queue: {event['id']}")
                
            except Exception as sub_err:
                logger.error(f"Failed to submit task for event {event['id']}: {sub_err}")
                
    except Exception as e:
        logger.error(f"Error in event worker task: {e}")

async def process_due_events():
    """
    Background worker loop using python-crontab for precise scheduling.
    """
    logger.info("Cortex Event Tool Worker started with python-crontab. Monitoring for due events...")
    
    # CronTab's scheduler - calculate the wait time until the next minute.
    entry = CronTab().new(command='')
    # (* * * * * = every minute)
    entry.setall('* * * * *')
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            # Calculate seconds until the next run
            next_run = entry.schedule().get_next()
            wait_time = (next_run - datetime.now()).total_seconds()
            await asyncio.sleep(max(wait_time, 0.1))
            
            # Execute the task
            await check_and_process_events(client)

if __name__ == "__main__":
    try:
        asyncio.run(process_due_events())
    except KeyboardInterrupt:
        logger.info("Event worker stopped by keyboard interrupt.")
