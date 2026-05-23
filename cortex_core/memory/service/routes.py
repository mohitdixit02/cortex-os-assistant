from cortex_core.graph.state import MemoryState
from typing import Literal
from cortex_cm.utility.logger import get_logger

class MemoryRouter:
    def __init__(self):
        self.logger = get_logger("CORTEX_MEMORY")
        
    def route_build_stm_required(self, state: MemoryState) -> Literal["build_stm", "build_emotional_profile", "build_user_knowledge_base"]:
        """
        Determine if building STM is required based on the current memory state. \n
        **Input:** `MemoryState` object \n
        **Output:** Boolean indicating whether to route to build STM or not \n
        """
        if state.stm_start_update_timestamp:
            self.logger.info("Routing to build STM: STM update timestamp is set")
            return "build_stm"
        self.logger.info("No need to route to build STM: No new non-summarized messages found.")
        return ["build_emotional_profile", "build_user_knowledge_base"]
        
__all__ = [
    "MemoryRouter"
]
