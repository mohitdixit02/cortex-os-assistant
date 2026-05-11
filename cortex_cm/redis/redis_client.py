import redis
from cortex_cm.utility.config import env
from enum import Enum

class RedisClientService:
    def __init__(
        self, 
        db: int,
        HOST: str,
        PORT: int
    ):
        self.client = redis.Redis(
            host=HOST,
            port=PORT,
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

class RedisModeType(str, Enum):
    """
    #### TOKEN
    For Google tokens and verifier related service
    #### TASK
    For submitting tasks which will be listened by cortex_core
    #### RESULT
    For submitting results which will be listened by cortex_server
    #### EVENT
    For saving events which will be listened by cortex_event_worker
    """
    TOKEN = 0
    TASK = 1
    RESULT = 2
    EVENT = 3

class RedisClient:
    _mode_cache = {}

    @staticmethod
    def get_client(
        mode: RedisModeType,
        is_docker_enabled: bool = True
    ):
        cache_key = (mode.value, bool(is_docker_enabled))
        if cache_key in RedisClient._mode_cache:
            return RedisClient._mode_cache[cache_key]

        if is_docker_enabled:
            host = env.REDIS_HOST
            port = env.REDIS_PORT
        else:
            host = "localhost"
            port = env.REDIS_PORT

        if mode == RedisModeType.TOKEN:
            client = RedisClientService(db=0, HOST=host, PORT=port)
        elif mode == RedisModeType.TASK:
            client = RedisClientService(db=1, HOST=host, PORT=port)
        elif mode == RedisModeType.RESULT:
            client = RedisClientService(db=2, HOST=host, PORT=port)
        elif mode == RedisModeType.EVENT:
            client = RedisClientService(db=3, HOST=host, PORT=port)
        else:
            raise ValueError("Invalid Redis Mode: {}. Valid options are TOKEN, TASK, RESULT, EVENT.".format(mode))

        RedisClient._mode_cache[cache_key] = client
        return client
