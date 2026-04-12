from cortex.memory import MemoryClient
from cortex.manager import ManagerClient
from langgraph.graph import StateGraph, START, END
from cortex.main.orchestrator import Orchestrator
from cortex.graph.state import ConversationState, MemoryState
from db import engine
from PIL import Image
import io

orchestrator = Orchestrator()
memory_client = MemoryClient(engine=engine)
manager_client = ManagerClient()

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

# Main Graph for the conversation workflow
main_graph = StateGraph(ConversationState)

main_graph.add_node("fetch_stm", memory_client.fetch_relevant_stm)
main_graph.add_node("fetch_emotional_profile", memory_client.fetch_emotional_profile)
main_graph.add_node("plan_main_orchestration", orchestrator.build_main_orchestration_plan)
main_graph.add_node("fetch_user_knowledge_base", memory_client.fetch_relevant_knowledge_base)
main_graph.add_node("fetch_message_history", memory_client.fetch_relevant_message_history)
main_graph.add_node("plan_evaluation", orchestrator.evaluate_plan)
main_graph.add_node("final_response_generation", orchestrator.generate_final_response)
main_graph.add_node("final_response_alignment", orchestrator.align_final_response)
main_graph.add_node("execute_tools_manager", manager_client.execute_tools)
main_graph.add_node("summarize_tool_result", manager_client.summarize_tool_results)

main_graph.add_edge(START, "fetch_stm")
main_graph.add_edge(START, "fetch_emotional_profile")
main_graph.add_edge("fetch_stm", "plan_main_orchestration")
main_graph.add_edge("fetch_emotional_profile", "plan_main_orchestration")
main_graph.add_edge("plan_main_orchestration", "fetch_user_knowledge_base")
main_graph.add_edge("plan_main_orchestration", "fetch_message_history")
main_graph.add_edge("plan_main_orchestration", "execute_tools_manager")
main_graph.add_edge("execute_tools_manager", "summarize_tool_result")
main_graph.add_edge(["fetch_user_knowledge_base", "fetch_message_history", "summarize_tool_result"], "plan_evaluation")
main_graph.add_conditional_edges(
    "plan_evaluation", 
    orchestrator.route_condition_orchestration_evaluation,
    {
        "plan_main_orchestration": "plan_main_orchestration",
        "final_response_generation": "final_response_generation",
    },
)
main_graph.add_edge("final_response_generation", "final_response_alignment")
main_graph.add_conditional_edges(
    "final_response_alignment",
    orchestrator.route_condition_final_response_evaluation,
    {
        "final_response_generation": "final_response_generation",
        "terminate": END,
    },
)

main_workflow = main_graph.compile()

# print(main_workflow.get_graph(xray=True).draw_ascii())
def display_workflow_graph(worflow):
    image_data = worflow.get_graph(xray=True).draw_mermaid_png()
    img = Image.open(io.BytesIO(image_data))
    img.show()

# display_workflow_graph(main_workflow)
# display_workflow_graph(build_memory_workflow)

# test workflow
test_graph = StateGraph(ConversationState)
# test_graph_2 = StateGraph(MemoryState)
test_graph.add_node("orchestrator_plan", orchestrator.build_main_orchestration_plan)
test_graph.add_node("ukb", memory_client.fetch_relevant_knowledge_base)
test_graph.add_node("evaluate_plan", orchestrator.evaluate_plan)
test_graph.add_edge(START, "orchestrator_plan")
test_graph.add_edge("orchestrator_plan", "ukb")
test_graph.add_edge("ukb", "evaluate_plan")
test_graph.add_conditional_edges(
    "evaluate_plan", 
    orchestrator.route_condition_orchestration_evaluation,
    {
        "plan_main_orchestration": "orchestrator_plan",
        "final_response_generation": END,
    },
)
# test_graph.add_edge(START, "ukb")
# test_graph.add_edge("ukb", END)

# test_graph_2.add_node("build_stm", memory_client.build_stm)
# test_graph_2.add_edge(START, "build_stm")
# test_graph_2.add_edge("build_stm", END)

test_workflow = test_graph.compile()
# test_workflow_2 = test_graph_2.compile()

display_workflow_graph(test_workflow)
# display_workflow_graph(test_workflow_2)

__all__ = [
    "main_workflow",
    "build_memory_workflow",
    "test_workflow",
    # "test_workflow_2",
]

