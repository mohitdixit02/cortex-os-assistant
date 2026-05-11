import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from cortex_cm.redis.redis_client import RedisClient, RedisModeType

event_redis_client = RedisClient.get_client(RedisModeType.EVENT)

def save_event_to_redis(user_id: str, event_id: str, trigger_time: datetime, event_data: Dict[str, Any], is_test: bool = False):
    """
    Saves an event to Redis using ZSET for sorting and HASH for data storage.
    
    Args:
        user_id (str): The ID of the user.
        event_id (str): The unique ID of the event.
        trigger_time (datetime): The trigger time of the event.
        event_data (Dict[str, Any]): The full event data.
        is_test (bool): Whether the event is a test event. Test events can be used for testing worker functionality using `req.test.py`.
    """
    timestamp = trigger_time.timestamp()
    
    redis_client = None
    if is_test:
        redis_client = RedisClient.get_client(RedisModeType.EVENT, is_docker_enabled=False)
    else:
        redis_client = event_redis_client
    
    # 1. Global ZSET (for worker)
    redis_client.client.zadd("events:all", {event_id: timestamp})
    # 2. Full Data - Hash
    redis_client.client.hset("events:data", event_id, json.dumps(event_data))

def delete_event_from_redis(event_id: str):
    """
    Removes an event from Redis.
    
    Args:
        user_id (str): The ID of the user.
        event_id (str): The unique ID of the event.
    """
    event_redis_client.client.zrem("events:all", event_id)
    event_redis_client.client.hdel("events:data", event_id)

def get_due_events_from_redis(time_window_seconds: int = 300) -> List[Dict[str, Any]]:
    """
    Fetches events that are due within the time window from the global ZSET.
    
    Args:
        time_window_seconds (int): Window from now in seconds (default 5 mins).
        
    Returns:
        List[Dict[str, Any]]: List of due event data dictionaries.
    """
    now = datetime.now().timestamp()
    future_limit = now + time_window_seconds
    
    # Get IDs of events due between -inf and now + window
    event_ids = event_redis_client.client.zrangebyscore("events:all", "-inf", future_limit)
    
    if not event_ids:
        return []
    
    # Fetch full data from Hash
    data_list = event_redis_client.client.hmget("events:data", event_ids)
    
    return [json.loads(d) for d in data_list if d]

def remove_event_from_worker_queue(event_id: str):
    """
    Removes an event from the global worker ZSET.
    """
    event_redis_client.client.zrem("events:all", event_id)

def update_redis_event_status(event_id: str, status: str):
    """
    Updates the status of an event in the Redis data Hash.
    """
    data_str = event_redis_client.client.hget("events:data", event_id)
    if data_str:
        data = json.loads(data_str)
        data["status"] = status
        event_redis_client.client.hset("events:data", event_id, json.dumps(data))
