from cortex_core.manager import ManagerClient
from langgraph.graph import StateGraph, START, END
from cortex_core.graph.state import ToolManagerState
from cortex_cm.pg import engine
from PIL import Image
import io

manager_client = ManagerClient()

# Tool Execution Workflow
tool_manager_graph = StateGraph(ToolManagerState)
tool_manager_graph.add_node("tools_manager", manager_client.tools_manager)
tool_manager_graph.add_node("web_search_tool", manager_client.web_search_tool)
tool_manager_graph.add_node("summarize_tool_results", manager_client.summarize_tool_results)
tool_manager_graph.add_node("task_retriever_tool", manager_client.task_retriever_tool)
tool_manager_graph.add_node("tool_result_aggregator", manager_client.tool_result_aggregator)

tool_manager_graph.add_edge(START, "tools_manager")
tool_manager_graph.add_conditional_edges(
    "tools_manager",
    manager_client.execute_tools_route,
    {
        "web_search_tool": "web_search_tool",
        "task_retriever_tool": "task_retriever_tool",
        "tool_result_aggregator": "tool_result_aggregator",
    }
)
tool_manager_graph.add_edge("web_search_tool", "summarize_tool_results")
tool_manager_graph.add_edge(["summarize_tool_results", "task_retriever_tool"], "tool_result_aggregator")
tool_manager_graph.add_edge("tool_result_aggregator", END)

tool_manager_workflow = tool_manager_graph.compile()

# def display_workflow_graph(worflow):
#     image_data = worflow.get_graph(xray=True).draw_mermaid_png()
#     img = Image.open(io.BytesIO(image_data))
#     img.show()
    
# display_workflow_graph(tool_manager_workflow)

__all__ = [
    "tool_manager_workflow",
]