from cortex.graph.state import ConversationState, EmotionalProfile, UserKnowledge, UserSTM, MessageHistory
from sqlmodel import Session
from db.req import (
    get_one
)
from db import (
    UserShortTermMemory,
    UserEmotionalProfile,
    UserKnowledgeBase,
    TimeOfDay
)

class MemoryClient:
    def __init__(self, session: Session):
        self.session = session
        
    def _get_time_behavior(self, timestamp) -> TimeOfDay:
        """
        Helper function to determine the time behavior (e.g., morning, afternoon, evening) based on the timestamp. \n
        Can be used for tuning the response generation to be more contextually relevant based on the time of day. \n
        """
        hour = timestamp.hour
        if 5 <= hour < 12:
            return TimeOfDay.MORNING
        elif 12 <= hour < 17:
            return TimeOfDay.AFTERNOON
        elif 17 <= hour < 21:
            return TimeOfDay.EVENING
        else:
            return TimeOfDay.NIGHT
    
    def build_stm(
        self,
        state: ConversationState
    ):
        """
        Build the Short Term Memory (STM) based on the recent interactions and context. \n
        """
        return state
    
    def build_ltm(
        self,
        state: ConversationState
    ):
        """
        Build the Long Term Memory (LTM) based on the historical interactions and context. \n
        """
        return
       
    def fetch_relevant_stm(
        self,
        state: ConversationState
    ):
        """
        Fetch relevant Short Term Memory (STM) based on the current conversation context and recent interactions. \n
        """
        user_id = state.user_id
        session_id = state.session_id
        res = get_one(
            session=self.session,
            model=UserShortTermMemory,
            user_id=user_id,
            session_id=session_id,
        )
        print(f"Fetched STM from DB: {res}")
        state.short_term_memory = UserSTM(
            stm_summary=res.stm_summary,
            session_preferences=res.session_preferences
        ) if res else None
        return state.short_term_memory
    
    def fetch_emotional_profile(
        self,
        state: ConversationState
    ):
        """
        Fetch the emotional profile of the user based on the recent interactions and context. \n
        Can be used for tuning the response generation to be more emotionally aware. \n
        """
        user_id = state.user_id
        session_id = state.session_id
        time_behaviour = self._get_time_behavior(state.query_timestamp)
        mood = state.query_emotion
        res = get_one(
            session=self.session,
            model=UserEmotionalProfile,
            user_id=state.user_id,
            session_id=session_id,
            mood_type=mood,
            time_behaviour=time_behaviour
        )
        state.emotional_profile = EmotionalProfile(
            mood_type=res.mood_type,
            time_behavior=res.time_behaviour,
            emotional_level=res.emotional_level,
            logical_level=res.logical_level,
            social_level=res.social_level,
            context_summary=res.context_summary
        ) if res else None
        return state.emotional_profile
    def fetch_relevant_ltm(
        self,
        state: ConversationState
    ):
        """
        Fetch relevant Long Term Memory (LTM) based on the historical interactions and context. \n
        """
        user_id = state.user_id
        res = self.session.exec(
        return
    def fetch_relevant_message_history(
        self,
        state: ConversationState
    ):
        """
        Fetch the relevant message history based on the current conversation context. \n
        """
        return
    
__all__ = [
    "MemoryClient"
]