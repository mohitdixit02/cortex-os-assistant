import json
from typing import List, Dict, Any, Optional
from cortex_cm.redis.redis_client import event_redis_client

def save_event_to_redis(event_id: str, trigger_time: str, event_data: Dict[str, Any]):
    """
    Saves an event to Redis.
    Key pattern: event_tool:{event_id}:{event_trigger_time}
    
    Args:
        event_id (str): The unique ID of the event.
        trigger_time (str): The trigger time in ISO format or timestamp.
        event_data (Dict[str, Any]): The event data to save.
    """
    key = f"event_tool:{event_id}:{trigger_time}"
    event_redis_client.set(key, json.dumps(event_data))

def delete_event_from_redis(event_id: str, trigger_time: str):
    """
    Deletes an event from Redis.
    
    Args:
        event_id (str): The unique ID of the event.
        trigger_time (str): The trigger time associated with the event.
    """
    key = f"event_tool:{event_id}:{trigger_time}"
    event_redis_client.delete(key)

def get_event_from_redis(event_id: str, trigger_time: str) -> Optional[Dict[str, Any]]:
    """
    Fetches an event from Redis.
    
    Args:
        event_id (str): The unique ID of the event.
        trigger_time (str): The trigger time associated with the event.
        
    Returns:
        Optional[Dict[str, Any]]: The event data if found, else None.
    """
    key = f"event_tool:{event_id}:{trigger_time}"
    data = event_redis_client.get(key)
    return json.loads(data) if data else None

def list_all_events_from_redis() -> List[Dict[str, Any]]:
    """
    Lists all events currently stored in Redis db 4.
    
    Returns:
        List[Dict[str, Any]]: A list of event data dictionaries.
    """
    keys = event_redis_client.client.keys("event_tool:*")
    events = []
    for key in keys:
        data = event_redis_client.get(key)
        if data:
            events.append(json.loads(data))
    return events

def get_event_keys() -> List[str]:
    """
    Returns all event keys from Redis.
    
    Returns:
        List[str]: A list of keys matching 'event_tool:*'.
    """
    return event_redis_client.client.keys("event_tool:*")
