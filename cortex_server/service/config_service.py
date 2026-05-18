import json
from uuid import UUID
from cortex_cm.pg import engine, UserConfig
from cortex_cm.pg.req.crud import get_by_id, create_one, update_one
from cortex_cm.redis.redis_client import RedisClient, RedisModeType
from sqlmodel import Session
from typing import Dict, Any, Optional

class ConfigService:
    def get_user_config(self, user_id: UUID) -> UserConfig:
        with Session(engine) as session:
            config = get_by_id(session, UserConfig, user_id)
            if not config:
                # Create default config if not exists
                config = self.create_default_config(user_id)
            return config

    def create_default_config(self, user_id: UUID) -> UserConfig:
        with Session(engine) as session:
            config = UserConfig(user_id=user_id)
            create_one(session, config)
            # Sync to Redis (DB:0 - Core/Config)
            self.sync_to_redis(user_id, config)
            return config

    def update_user_config(self, user_id: UUID, config_data: Dict[str, Any]) -> UserConfig:
        with Session(engine) as session:
            config = get_by_id(session, UserConfig, user_id)
            if not config:
                config = UserConfig(user_id=user_id)
                create_one(session, config)
            
            # Update only provided fields
            updated_config = update_one(session, config, config_data)
            
            # Sync to Redis (DB:0 - Core/Config)
            self.sync_to_redis(user_id, updated_config)
            
            return updated_config

    def sync_to_redis(self, user_id: UUID, config: UserConfig):
        # Redis DB:0 is typically for Core configuration/state
        redis_client = RedisClient.get_client(RedisModeType.TOKEN)
        key = f"cortex:config:{user_id}"

        config_payload = {
            "voice_client_timeout_seconds": config.voice_client_timeout_seconds,
            "force_open_websocket": config.force_open_websocket,
            "reminder_minutes_before_trigger_time": config.reminder_minutes_before_trigger_time,
            "timezone": config.timezone,
            "timezone_mode": config.timezone_mode
        }

        redis_client.client.set(key, json.dumps(config_payload))

    def get_voice_client_timeout(self, user_id: UUID) -> int:
        """Fetch voice_client_timeout_seconds from Redis, fallback to DB if not found."""
        redis_client = RedisClient.get_client(RedisModeType.TOKEN)
        key = f"cortex:config:{user_id}"

        cached_config = redis_client.client.get(key)
        if cached_config:
            try:
                config_data = json.loads(cached_config)
                return config_data.get("voice_client_timeout_seconds", 3)
            except (json.JSONDecodeError, TypeError):
                pass

        # Fallback to DB
        config = self.get_user_config(user_id)
        # Re-sync to Redis
        self.sync_to_redis(user_id, config)
        return config.voice_client_timeout_seconds


config_service = ConfigService()
