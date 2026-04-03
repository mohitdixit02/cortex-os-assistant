from cortex.graph.state import CortexTool

web_search_tool = CortexTool(
    tool_id="web_search_01",
    tool_name="web_search",
    tool_description="Use this tool to search the web for up-to-date information. Input should be a search query. Output will be a list of relevant search results.",
)

email_tool = CortexTool(
        tool_id="email_02",
        tool_name="email",
        tool_description="Use this tool to send emails. Input should be the recipient, subject, and body of the email.",
    )

calendar_tool = CortexTool(
    tool_id="calendar_03",
    tool_name="calendar",
    tool_description="Use this tool to manage calendar events. Input should specify the action (create, update, delete) and the event details.",
)

AVAILABLE_TOOLS = [
    web_search_tool,
    email_tool,
    calendar_tool
]