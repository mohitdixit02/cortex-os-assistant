from cortex.memory import MemoryClient
from langgraph.graph import StateGraph, START, END
from cortex.graph.state import MemoryState
from db import engine
from PIL import Image
import io

memory_client = MemoryClient(engine=engine)

# Build Memory for the conversation
memory_graph = StateGraph(MemoryState)

memory_graph.add_node("persist_ai_response", memory_client.persist_ai_response)
memory_graph.add_node("retrieve_unsummarized_messages", memory_client.retrieve_unsummarized_messages)
memory_graph.add_node("build_stm", memory_client.build_stm)
memory_graph.add_node("build_emotional_profile", memory_client.build_emotional_profile)
memory_graph.add_node("build_user_knowledge_base", memory_client.build_user_knowledge_base)
memory_graph.add_node("persist_memory_state", memory_client.persist_memory_state)

memory_graph.add_edge(START, "persist_ai_response")
memory_graph.add_edge("persist_ai_response", "retrieve_unsummarized_messages")
memory_graph.add_conditional_edges("retrieve_unsummarized_messages", memory_client.route_build_stm_required)
memory_graph.add_edge("build_stm", "build_emotional_profile")
memory_graph.add_edge("build_stm", "build_user_knowledge_base")
memory_graph.add_edge(["build_emotional_profile", "build_user_knowledge_base"], "persist_memory_state")
memory_graph.add_edge("persist_memory_state", END)

build_memory_workflow = memory_graph.compile()

def display_workflow_graph(worflow):
    image_data = worflow.get_graph(xray=True).draw_mermaid_png()
    img = Image.open(io.BytesIO(image_data))
    img.show()

display_workflow_graph(build_memory_workflow)

__all__ = [
    "memory_client",
    "build_memory_workflow",
]