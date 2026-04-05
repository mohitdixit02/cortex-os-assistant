from langchain_huggingface import HuggingFaceEndpointEmbeddings, ChatHuggingFace, HuggingFaceEndpoint
from cortex.memory.prompts import get_memory_client_prompts
from utility.huggingface.config import models
from utility.config import env
from cortex.graph.state import ConversationState, UserSTM, MemoryEmotionalProfile

class MemoryModel:
    def __init__(self):
        model_config = models.get("main", {})
        self.model = ChatHuggingFace(llm=HuggingFaceEndpoint(
            repo_id=model_config.get("name"),
            task=model_config.get("task", "conversational"),
            max_new_tokens=model_config.get("max_new_tokens", 200),
            temperature=model_config.get("temperature", 0.2)
        ))
    
    def build_stm(self, state: ConversationState):
        """
        ### Build Short Term Memory (STM) based on the provided conversation state \n
        **Input:** `ConversationState` object \n
        Must include:
        - query
        - final_response
        - query_emotion
        - previous STM memory (if available) \n
        **Output:** \n
        Updated `UserSTM` object
        - Include new `STM summary` and `session preferences` \n
        """
        query = state.query
        final_response = state.final_response.response
        user_emotion = state.query_emotion
        prev_stm = state.short_term_memory        
        formatted_prompt, parser = get_memory_client_prompts(
            type="build_stm",
        )
        chain = formatted_prompt | self.model | parser
        res = chain.invoke({
            "user_query": query,
            "ai_response": final_response,
            "user_emotion": user_emotion,
            "previous_stm_memory": prev_stm.stm_summary if prev_stm else "",
            "previous_session_preferences": prev_stm.session_preferences if prev_stm else {}
        })
        state.short_term_memory = UserSTM(
            stm_summary=res.stm_summary,
            session_preferences=res.session_preferences
        )
        return state.short_term_memory

    def build_emotional_profile(self, state: ConversationState):
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
        
        if state.emotional_profile:
            prev_emotional_profile = MemoryEmotionalProfile(
                emotional_level=state.emotional_profile.emotional_level,
                logical_level=state.emotional_profile.logical_level,
                social_level=state.emotional_profile.social_level,
                context_summary=state.emotional_profile.context_summary
            )
        else:
            prev_emotional_profile = None

        formatted_prompt, parser = get_memory_client_prompts(
            type="build_emotional_profile",
        )
        chain = formatted_prompt | self.model | parser
        res = chain.invoke({
            "user_query": query,
            "user_emotion": user_emotion,
            "stm_summary": prev_stm.stm_summary if prev_stm else "",
            "session_preferences": prev_stm.session_preferences if prev_stm else {},
            "user_time_of_day": time_of_day,
            "previous_emotional_profile": prev_emotional_profile.model_dump_json() if prev_emotional_profile else ""
        })
        return res
    
    def build_user_knowledge_base(self, state: ConversationState):
        """
        Build the user's knowledge base based on the historical interactions and context. \n
        """
        query = state.query
        prev_stm = state.short_term_memory
        user_emotion = state.query_emotion

        formatted_prompt, parser = get_memory_client_prompts(
            type="build_user_knowledge"
        )
        chain = formatted_prompt | self.model | parser
        res = chain.invoke({
            "user_query": query,
            "stm_summary": prev_stm.stm_summary if prev_stm else "",
            "session_preferences": prev_stm.session_preferences if prev_stm else {},
            "user_emotion": user_emotion
        })
        return res
