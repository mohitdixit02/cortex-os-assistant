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
os.environ['HF_HOME'] = cache_dir
os.environ['TRANSFORMERS_CACHE'] = cache_dir
os.environ['HF_DATASETS_CACHE'] = cache_dir
os.environ["SENTENCE_TRANSFORMERS_HOME"] = cache_dir
os.makedirs(cache_dir, exist_ok=True)
print(f"Configuration loaded. Cache directory set to: {cache_dir}")

@dataclass(frozen=True)
class EnvProvider:
    HF_TOKEN: str = os.getenv("HF_TOKEN")
    HF_CACHE_DIR: str = os.getenv("HF_CACHE_DIR")
    DB_URL: str = os.getenv("DB_URL")

env = EnvProvider()
__all__ = ["env"]