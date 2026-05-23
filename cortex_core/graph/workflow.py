from langgraph.graph import StateGraph, START, END
from cortex_core.main.orchestrator import Orchestrator
from cortex_core.graph.state import ConversationState
from cortex_core.graph.memory import memory_client

orchestrator = Orchestrator()

# Main Graph for the conversation workflow
main_graph = StateGraph(ConversationState)

main_graph.add_node("fetch_stm", memory_client.fetch_relevant_stm)
main_graph.add_node("fetch_emotional_profile", memory_client.fetch_emotional_profile)
main_graph.add_node("main_orchestration", orchestrator.main_orchestration)
main_graph.add_node("build_knowledge_plan", orchestrator.build_knowledge_plan)
main_graph.add_node("build_messages_plan", orchestrator.build_messages_plan)
main_graph.add_node("build_tools_plan", orchestrator.build_tools_plan)
main_graph.add_node("evaluate_knowledge_plan", orchestrator.evaluate_knowledge_plan)
main_graph.add_node("evaluate_messages_plan", orchestrator.evaluate_messages_plan)
main_graph.add_node("evaluate_tools_plan", orchestrator.evaluate_tools_plan)
main_graph.add_node("evaluation_aggregator", orchestrator.evaluation_aggregator)
main_graph.add_node("fetch_user_knowledge_base", memory_client.fetch_relevant_knowledge_base)
main_graph.add_node("fetch_message_history", memory_client.fetch_relevant_message_history)
main_graph.add_node("execute_tools_manager", orchestrator.execute_tools)
main_graph.add_node("final_response_generation", orchestrator.generate_final_response)
main_graph.add_node("final_response_alignment", orchestrator.align_final_response)

main_graph.add_edge(START, "fetch_stm")
main_graph.add_edge(START, "fetch_emotional_profile")
main_graph.add_edge(["fetch_stm", "fetch_emotional_profile"], "main_orchestration")

main_graph.add_edge("main_orchestration", "build_knowledge_plan")
main_graph.add_edge("main_orchestration", "build_messages_plan")
main_graph.add_edge("main_orchestration", "build_tools_plan")

main_graph.add_conditional_edges(
    "build_knowledge_plan",
    orchestrator.route_condition_fetch_knowledge,
    {
        "fetch_user_knowledge_base": "fetch_user_knowledge_base",
        "skip_knowledge_retrieval": "evaluate_knowledge_plan",
    }
)
main_graph.add_edge("fetch_user_knowledge_base", "evaluate_knowledge_plan")
main_graph.add_conditional_edges(
    "build_messages_plan",
    orchestrator.route_condition_fetch_messages,
    {
        "fetch_message_history": "fetch_message_history",
        "skip_message_retrieval": "evaluate_messages_plan",
    }
)
main_graph.add_edge("fetch_message_history", "evaluate_messages_plan")
main_graph.add_edge("build_tools_plan", "evaluate_tools_plan")
main_graph.add_edge(
    ["evaluate_knowledge_plan", "evaluate_messages_plan", "evaluate_tools_plan"],
    "evaluation_aggregator",
)

main_graph.add_conditional_edges(
    "evaluation_aggregator",
    orchestrator.route_condition_orchestration_evaluation,
    {
        "plan_main_orchestration": "main_orchestration",
        "route_execute_tools": "execute_tools_manager",
    },
)
main_graph.add_edge("execute_tools_manager", "final_response_generation")
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

__all__ = [
    "main_workflow",
]
