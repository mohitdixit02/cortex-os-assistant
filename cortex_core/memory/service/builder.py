from cortex_core.graph.state import (
    UserSTM,
    MemoryState
)
from cortex_core.memory.model import MemoryModel
from sqlmodel import Session, select
from sqlalchemy.engine import Engine
from cortex_cm.utility.logger import get_logger
from cortex_cm.pg import (
    Message,
    RoleType,
)
from cortex_cm.utility.time_utils import UTC_NOW

class MemoryBuilder:
    def __init__(self, engine: Engine, model: MemoryModel):
        self.engine = engine
        self.model = model
        self.logger = get_logger("CORTEX_MEMORY")
    
    def build_stm(
        self,
        state: MemoryState
    ):
        """
        Build the Short Term Memory (STM) based on the recent interactions and context. \n
        """
        
        constrains = (
            Message.user_id == state.user_id,
            Message.session_id == state.session_id,
            Message.is_summarized == False,
        )
        
        if state.stm_start_update_timestamp:
            constrains += (Message.created_at >= state.stm_start_update_timestamp,)
        if state.stm_end_update_timestamp:
            constrains += (Message.created_at < state.stm_end_update_timestamp,)
        else:
            constrains += (Message.created_at < UTC_NOW(),)
        
        with Session(self.engine) as session:
            recent_conversations = list(session.exec(
                select(Message)
                .where(*constrains)
                .order_by(Message.created_at.asc())
            ).all())
        
        res = ""
        for msg in recent_conversations:
            if msg.role == RoleType.USER:
                res += f"USER: {msg.content}\n"
            elif msg.role == RoleType.AI:   
                res += f"AI: {msg.content}\n"
        
        if state.short_term_memory:
            state.short_term_memory.recent_conversation = res.strip()
        else:
            state.short_term_memory = UserSTM(
                stm_summary=None,
                session_preferences=None,
                recent_conversation=res.strip()
            )
        self.logger.info(f"Built recent conversation for STM: {state.short_term_memory.recent_conversation}")
        
        short_term_memory = self.model.build_stm(state=state)
        self.logger.info(f"Built STM: {short_term_memory}")
        return {
            "short_term_memory": short_term_memory,
        }
    
    def build_emotional_profile(
        self,
        state: MemoryState
    ):
        """
        Build the Emotional Profile based on the historical interactions and context. \n
        """
        res = self.model.build_emotional_profile(state=state)
        self.logger.info(f"Built Emotional Profile: {res}")
        return {
            "emotional_profile": res,
        }
    
    def build_user_knowledge_base(
        self,
        state: MemoryState
    ):
        """
        Build the user's knowledge base based on the historical interactions and context. \n
        """
        res = self.model.build_user_knowledge_base(state=state)
        self.logger.info(f"Built User Knowledge Base: {res}")
        return {
            "knowledge_items": res,
        }

__all__ = [
    "MemoryBuilder"
]
