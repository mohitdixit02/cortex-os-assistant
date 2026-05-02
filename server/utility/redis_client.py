import redis
from utility.config import env

class RedisClient:
    def __init__(self):
        self.client = redis.Redis(
            host=env.REDIS_HOST,
            port=env.REDIS_PORT,
            db=env.REDIS_DB,
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

redis_client = RedisClient()
