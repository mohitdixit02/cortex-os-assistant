"""
Config for overall main server and its child services
"""

import os
from dotenv import load_dotenv

print("Loading configuration for server...")
load_dotenv()
cache_dir = os.getenv("HF_CACHE_DIR", "./hf_cache")
os.environ['HF_HOME'] = cache_dir
os.environ['TRANSFORMERS_CACHE'] = cache_dir
os.environ['HF_DATASETS_CACHE'] = cache_dir
os.environ["SENTENCE_TRANSFORMERS_HOME"] = cache_dir
os.makedirs(cache_dir, exist_ok=True)
print(f"Configuration loaded. Cache directory set to: {cache_dir}")
