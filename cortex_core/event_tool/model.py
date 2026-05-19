from cortex_core.graph.state import EventToolState
from cortex_cm.utility.logger import get_logger
from cortex_cm.utility.models import get_main_model
from cortex_core.event_tool.prompts import EventReminderOutput, get_event_tool_prompt

from datetime import datetime, timezone
UTC_NOW = lambda: datetime.now(timezone.utc)

class EventToolModel:
    def __init__(self):
        self.logger = get_logger("CORTEX_EVENT_TOOL")
        self.model = get_main_model()

    def build_final_reminder(self, state: EventToolState) -> EventReminderOutput:
        formatted_prompt, parser = get_event_tool_prompt(
            type="build_reminder",
        )
        chain = formatted_prompt | self.model | parser
                
        res = chain.invoke({
            "event_name": state.event_name,
            "event_description": state.event_description,
            "user_name": state.user_name if state.user_name else "",
            "time_left": state.time_left,
            "time_of_query": state.time_of_query if state.time_of_query else "",
        })
        return res
