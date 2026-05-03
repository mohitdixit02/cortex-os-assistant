import asyncio
import threading
import time
from cortex_core.memory.embedding import EmbeddingModel
from cortex_cm.utility.logger import get_logger
from dataclasses import dataclass, field
from typing import Any, Dict, Literal, Optional
from cortex_cm.utility.cortex.config import task_queue_config
from cortex_core.memory.saver import MemorySaver
from cortex_cm.pg import (
    engine,
    User,
    ChatSession,
)

def create_new_session():
    """Create a new database session."""
    return ""
