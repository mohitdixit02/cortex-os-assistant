from cortex.memory import MemoryClient
from langgraph.graph import StateGraph, START, END
from .state import ConversationState
from db import engine

memory_client = MemoryClient(
    engine=engine
)

# Main Graph for the conversation workflow
main_graph = StateGraph(ConversationState)

main_graph.add_node("fetch_stm", memory_client.fetch_relevant_stm)
main_graph.add_node("fetch_emotional_profile", memory_client.fetch_emotional_profile)
main_graph.add_node("fetch_user_knowledge_base", memory_client.fetch_relevant_knowledge_base)

main_graph.add_edge(START, "fetch_stm")
main_graph.add_edge(START, "fetch_emotional_profile")
main_graph.add_edge(START, "fetch_user_knowledge_base")
main_graph.add_edge("fetch_stm", END)
main_graph.add_edge("fetch_emotional_profile", END)
main_graph.add_edge("fetch_user_knowledge_base", END)

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

main_workflow = main_graph.compile()
build_memory_workflow = memory_graph.compile()

__all__ = [
    "main_workflow",
    "build_memory_workflow"
]
