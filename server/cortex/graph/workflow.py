from cortex.memory import MemoryClient
from langgraph.graph import StateGraph, START, END
from .state import ConversationState
from db import session

memory_client = MemoryClient(
    session=session
)

# /pending/ - Main graph for orchestrating the workflow of processing pending tasks

# Build Memory for the conversation
memory_graph = StateGraph(ConversationState)

memory_graph.add_node("build_stm", memory_client.build_stm)
memory_graph.add_node("build_emotional_profile", memory_client.build_emotional_profile)
memory_graph.add_node("build_user_knowledge_base", memory_client.build_user_knowledge_base)
memory_graph.add_node("persist_memory_state", memory_client.persist_memory_state)

memory_graph.add_edge(START, "build_stm")
memory_graph.add_edge("build_stm", "build_emotional_profile")
memory_graph.add_edge("build_stm", "build_user_knowledge_base")
memory_graph.add_edge("build_emotional_profile", "persist_memory_state")
memory_graph.add_edge("build_user_knowledge_base", "persist_memory_state")
memory_graph.add_edge("persist_memory_state", END)

build_memory_workflow = memory_graph.compile()

__all__ = [
    "build_memory_workflow"
]
