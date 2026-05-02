"""
Config for overall main server and its child services
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv
from enum import Enum

print("Loading configuration for server...")
load_dotenv()
cache_dir = os.getenv("HF_CACHE_DIR", "./hf_cache")
# os.environ['HF_HOME'] = cache_dir
# os.environ['TRANSFORMERS_CACHE'] = cache_dir
# os.environ['HF_DATASETS_CACHE'] = cache_dir
# os.environ["SENTENCE_TRANSFORMERS_HOME"] = cache_dir
# os.makedirs(cache_dir, exist_ok=True)
print(f"Configuration loaded. Cache directory set to: {cache_dir}")

@dataclass(frozen=True)
class EnvProvider:
    HF_TOKEN: str = os.getenv("HF_TOKEN")
    HF_CACHE_DIR: str = os.getenv("HF_CACHE_DIR")
    DB_URL: str = os.getenv("DB_URL")
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI")
    
    # Redis
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB: int = int(os.getenv("REDIS_DB", 0))
    
    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "your-secret-key")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")

env = EnvProvider()
__all__ = ["env"]