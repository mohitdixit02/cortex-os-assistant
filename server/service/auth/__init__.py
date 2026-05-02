import asyncio
import threading
import time
from cortex.memory.embedding import EmbeddingModel
from utility.logger import get_logger
from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional
from utility.cortex.config import task_queue_config
from cortex.memory.saver import MemorySaver
from db import (
    engine,
    User,
    ChatSession,
)

def create_new_session():
    """Create a new database session."""
    return ""

