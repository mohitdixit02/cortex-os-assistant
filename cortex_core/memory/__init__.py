from cortex_core.graph.state import (
    ConversationState,
    MemoryState
)
from typing import Literal
from cortex_core.memory.model import MemoryModel
from cortex_core.memory.embedding import EmbeddingModel
from sqlalchemy.engine import Engine
from cortex_cm.utility.logger import get_logger

from cortex_core.memory.service.builder import MemoryBuilder
from cortex_core.memory.service.persist import MemoryPersister
from cortex_core.memory.service.retriever import MemoryRetriever
from cortex_core.memory.service.routes import MemoryRouter
from cortex_core.memory.service.saver import MemorySaver

class MemoryClient:
    def __init__(self, engine: Engine):
        self.engine = engine
        self.model = MemoryModel()
        self.embd_model = EmbeddingModel()
        self.logger = get_logger("CORTEX_MEMORY")
        self.memory_saver = MemorySaver(engine=engine, model=self.embd_model)
        
        self.builder = MemoryBuilder(engine=self.engine, model=self.model)
        self.persister = MemoryPersister(
            engine=engine,
            model=self.model,
            embd_model=self.embd_model,
            memory_saver=self.memory_saver
        )
        self.retriever = MemoryRetriever(
            engine=engine,
            model=self.model,
            embd_model=self.embd_model
        )
        self.routes = MemoryRouter()
        self.saver = MemorySaver(
            engine=engine,
            model=self.model
        )

    def retrieve_unsummarized_messages(self, state: MemoryState) -> MemoryState:
        return self.retriever.retrieve_unsummarized_messages(state)
    
    # ******************** Build Memory State Functions ********************
    def route_build_stm_required(self, state: MemoryState) -> Literal["build_stm", "build_emotional_profile", "build_user_knowledge_base"]:
        return self.routes.route_build_stm_required(state)
        
    def build_stm(self, state: MemoryState):
        return self.builder.build_stm(state)
    
    def build_emotional_profile(self, state: MemoryState):
        return self.builder.build_emotional_profile(state)
    
    def build_user_knowledge_base(self, state: MemoryState):
        return self.builder.build_user_knowledge_base(state)
        
    def persist_memory_state(self, state: MemoryState):
        return self.persister.persist_memory_state(state)
                    
    def persist_ai_response(self, state: MemoryState):
        return self.persister.persist_ai_response(state)

    # ******************** Fetch Memory State Functions ********************
    def fetch_relevant_stm(self, state: ConversationState):
        return self.retriever.fetch_relevant_stm(state)
    
    def fetch_emotional_profile(self, state: ConversationState):
        return self.retriever.fetch_emotional_profile(state)
    
    def fetch_relevant_knowledge_base(self, state: ConversationState):
        return self.retriever.fetch_relevant_knowledge_base(state)
    
    def fetch_relevant_message_history(self, state: ConversationState):
        return self.retriever.fetch_relevant_message_history(state)
    
__all__ = [
    "MemoryClient"
]
