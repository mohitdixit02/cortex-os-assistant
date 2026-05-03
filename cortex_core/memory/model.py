from langchain_huggingface import HuggingFaceEndpointEmbeddings, ChatHuggingFace, HuggingFaceEndpoint
from cortex_core.memory.prompts import get_memory_client_prompts
from cortex_cm.utility.huggingface.config import models
from cortex_cm.utility.config import env
from cortex_core.graph.state import ConversationState, UserSTM, MemoryEmotionalProfile, MemoryState, MemoryUserKnowledgeList
import json
import re
from cortex_cm.utility.models import MAIN_MODEL, HEAVY_PLANNER_MODEL

class MemoryModel:
    def __init__(self):
        self.model = MAIN_MODEL
        self.heavy_plan_model = HEAVY_PLANNER_MODEL
    
    def build_stm(self, state: MemoryState):
        """
        ### Build Short Term Memory (STM) based on the provided conversation state \n
        **Input:** `MemoryState` object \n
        Must include:
        - query
        - query_emotion
        - previous STM memory (if available) \n
        **Output:** \n
        Updated `UserSTM` object
        - Include new `STM summary` and `session preferences` \n
        """
        query = state.query
        user_emotion = state.query_emotion
        prev_stm = state.short_term_memory        
        formatted_prompt, parser = get_memory_client_prompts(
            type="build_stm",
        )
        chain = formatted_prompt | self.model | parser
        res = chain.invoke({
            "user_query": query,
            "user_emotion": user_emotion,
            "previous_stm_memory": prev_stm.stm_summary if prev_stm else "",
            "previous_session_preferences": prev_stm.session_preferences if prev_stm else {},
            "recent_conversation": prev_stm.recent_conversation if prev_stm else "",
        })
        state.short_term_memory = UserSTM(
            stm_summary=res.stm_summary,
            session_preferences=res.session_preferences,
            recent_conversation=prev_stm.recent_conversation if prev_stm else "" # keep recent conversation same
        )
        return state.short_term_memory

    def build_emotional_profile(self, state: MemoryState):
        """
        ### Build Emotional Profile based on the provided conversation state \n
        **Input:** `ConversationState` object \n
        Must include:
        - query
        - query_emotion \n
        - previous STM memory (if available)
        **Output:** \n
        Updated `EmotionalProfile` object
        - Include new `mood_type`, `time_behavior`, `emotional_level`, `logical_level`, `social_level` \n
        """
        query = state.query
        user_emotion = state.query_emotion
        prev_stm = state.short_term_memory
        time_of_day = state.query_time

        formatted_prompt, parser = get_memory_client_prompts(
            type="build_emotional_profile",
        )
        chain = formatted_prompt | self.model | parser
        res = chain.invoke({
            "user_query": query,
            "user_emotion": user_emotion,
            "user_time_of_day": time_of_day,
            "recent_conversation": prev_stm.recent_conversation if prev_stm else "",
            "previous_emotional_profile": state.emotional_profile.model_dump_json() if state.emotional_profile else ""
        })
        return res
    
    def build_user_knowledge_base(self, state: MemoryState):
        """
        Build the user's knowledge base based on the historical interactions and context. \n
        """
        query = state.query
        prev_stm = state.short_term_memory
        user_emotion = state.query_emotion

        formatted_prompt, parser = get_memory_client_prompts(
            type="build_user_knowledge"
        )
        chain = formatted_prompt | self.heavy_plan_model | parser
        res = chain.invoke({
            "user_query": query,
            "user_emotion": user_emotion,
            "user_time_of_day": state.query_time,
            "previous_user_knowledge": state.older_knowledge_base if state.older_knowledge_base else "",
            "recent_conversation": prev_stm.recent_conversation if prev_stm else "",
        })
        return res
