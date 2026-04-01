from cortex.memory import MemoryClient
from db import session

memory_client = MemoryClient(
    session=session
)

