from cortex_core.event_tool import EventToolClient
from langgraph.graph import StateGraph, START, END
from cortex_core.graph.state import EventToolState
from cortex_cm.pg import engine
from PIL import Image
import io

event_tool_client = EventToolClient()

# Tool Execution Workflow
event_tool_graph = StateGraph(EventToolState)
event_tool_graph.add_node("build_pre_reminder_info", event_tool_client.build_pre_reminder_info)
event_tool_graph.add_node("build_final_reminder", event_tool_client.build_final_reminder)

event_tool_graph.add_edge(START, "build_pre_reminder_info")
event_tool_graph.add_edge("build_pre_reminder_info", "build_final_reminder")
event_tool_graph.add_edge("build_final_reminder", END)

event_tool_workflow = event_tool_graph.compile()

# def display_workflow_graph(worflow):
#     image_data = worflow.get_graph(xray=True).draw_mermaid_png()
#     img = Image.open(io.BytesIO(image_data))
#     img.show()
    
# display_workflow_graph(event_tool_workflow)

__all__ = [
    "event_tool_workflow",
]
