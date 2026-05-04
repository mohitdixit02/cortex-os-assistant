import redis
import json
from cortex_cm.utility.config import env

class RedisClient:
    def __init__(self, db: int = None):
        self.client = redis.Redis(
            host=env.REDIS_HOST,
            port=env.REDIS_PORT,
            db=db if db is not None else env.REDIS_DB,
            decode_responses=True
        )

    def set_access_token(self, user_id: str, token: str, ttl: int = 3500):
        key = f"token:access:{user_id}"
        self.client.setex(key, ttl, token)

    def get_access_token(self, user_id: str):
        key = f"token:access:{user_id}"
        return self.client.get(key)

    def delete_access_token(self, user_id: str):
        key = f"token:access:{user_id}"
        self.client.delete(key)

    def set(self, key: str, value: str, ttl: int = None):
        if ttl:
            self.client.setex(key, ttl, value)
        else:
            self.client.set(key, value)

    def get(self, key: str):
        return self.client.get(key)

    def delete(self, key: str):
        self.client.delete(key)

    def lpush(self, key: str, value: str):
        self.client.lpush(key, value)

    def brpop(self, key: str, timeout: int = 0):
        result = self.client.brpop(key, timeout)
        return result[1] if result else None

# Default client
redis_client = RedisClient()

# Specialized clients as per instructions
# DB:0 - Google tokens and verifier related service
token_redis_client = RedisClient(db=0)
# DB:1 - Submitting tasks which will be listened by cortex_core
task_redis_client = RedisClient(db=1)
# DB:2 - Submitting results which will be listened by cortex_server
result_redis_client = RedisClient(db=2)
