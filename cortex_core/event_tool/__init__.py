from cortex_core.graph.state import EventToolState
from cortex_core.event_tool.model import EventToolModel
from cortex_cm.utility.logger import get_logger
from cortex_cm.pg.enums import TimeOfDay
from cortex_cm.pg import engine, Session
from cortex_cm.pg.models import Message, User
from cortex_cm.pg.req import get_by_id

from datetime import datetime, timezone
UTC_NOW = lambda: datetime.now(timezone.utc)

class EventToolClient():
    """
    Client for executing the Tool Event
    """
    def __init__(self):
        self.logger = get_logger("CORTEX_EVENT_TOOL")
        self.model = EventToolModel()
        
    def _get_time_behavior(self, timestamp) -> TimeOfDay:
        """
        Helper function to determine the time behavior (e.g., morning, afternoon, evening) based on the timestamp. \n
        Can be used for tuning the response generation to be more contextually relevant based on the time of day. \n
        """
        
        # converting timestamp to local time if it's in UTC
        if timestamp.tzinfo is not None and timestamp.tzinfo.utcoffset(timestamp) is not None:
            local_timestamp = timestamp.astimezone()
        else:
            local_timestamp = timestamp
        
        hour = local_timestamp.hour
        if 5 <= hour < 12:
            return TimeOfDay.MORNING
        elif 12 <= hour < 17:
            return TimeOfDay.AFTERNOON
        elif 17 <= hour < 21:
            return TimeOfDay.EVENING
        else:
            return TimeOfDay.NIGHT
        
    def build_pre_reminder_info(self, state: EventToolState):
        try:
            message_id = state.message_id
            user_name = ""
            with Session(engine) as session:
                message = get_by_id(session, Message, message_id)
                if message:
                    user = get_by_id(session, User, message.user_id)
                    if user:
                        user_name = user.full_name
            
            # Time of Query - Local Time stamp in User Config - Pending Implementation
            time_of_query = self._get_time_behavior(UTC_NOW())
            
            return {
                "user_name": user_name,
                "time_of_query": time_of_query
            }
        except Exception as e:
            self.logger.error(f"Error in build_pre_reminder_info: {e}")
            return {
                "user_name": "",
                "time_of_query": ""
            }
            
    def build_final_reminder(self, state: EventToolState):
        try:
            res = self.model.build_final_reminder(state)
            return {
                "final_reminder": res.reminder_message
            }
        except Exception as e:
            self.logger.error(f"Error in build_final_reminder: {e}")
            # Fallback reminder message in case of any error
            fallback_message = f"Hi, this is a reminder that '{state.event_name}' is coming up soon"
            return {
                "final_reminder": fallback_message
            }
