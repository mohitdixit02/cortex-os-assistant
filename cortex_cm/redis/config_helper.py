import json
from uuid import UUID
from typing import Dict, Any, Optional
from cortex_cm.redis.redis_client import RedisClient, RedisModeType
from cortex_cm.pg import engine, UserConfig
from cortex_cm.pg.req.crud import get_by_id
from sqlmodel import Session

def get_user_config_from_redis(user_id: UUID) -> Optional[Dict[str, Any]]:
    """Fetch user configuration from Redis DB:0 (TOKEN/Config)."""
    redis_client = RedisClient.get_client(RedisModeType.TOKEN)
    key = f"cortex:config:{user_id}"
    
    cached_config = redis_client.client.get(key)
    if cached_config:
        try:
            return json.loads(cached_config)
        except (json.JSONDecodeError, TypeError):
            return None
    return None

def get_reminder_window_minutes(user_id: UUID) -> int:
    """
    Get the user's reminder window in minutes.
    Prioritizes Redis, falls back to DB, then to a default of 5.
    """
    # 1. Try Redis
    config = get_user_config_from_redis(user_id)
    if config and "reminder_minutes_before_trigger_time" in config:
        return int(config["reminder_minutes_before_trigger_time"])
    
    # 2. Try DB
    try:
        with Session(engine) as session:
            db_config = get_by_id(session, UserConfig, user_id)
            if db_config:
                return db_config.reminder_minutes_before_trigger_time
    except Exception as e:
        print(f"Error fetching reminder window from DB: {e}")
        
    # 3. Default
    return 5
