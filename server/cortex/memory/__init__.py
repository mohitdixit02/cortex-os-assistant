from cortex.graph.state import (
    ConversationState,
    EmotionalProfile,
    UserKnowledge,
    UserSTM,
    MessageHistory,
    MessageState,
    MessageStateList,
)
from cortex.memory.model import MemoryModel
from cortex.memory.embedding import EmbeddingModel
from cortex.memory.saver import MemorySaver
from sqlalchemy.engine import Engine
from sqlmodel import Session
from utility.logger import get_logger
from db.req import (
    get_one,
    get_similar,
    create_one,
    create_many,
    update_one
)
from db import (
    UserShortTermMemory,
    UserEmotionalProfile,
    UserKnowledgeBase,
    TimeOfDay,
    Message,
    RoleType,
    AIClientType
)

class MemoryClient:
    def __init__(self, engine: Engine):
        self.engine = engine
        self.model = MemoryModel()
        self.embd_model = EmbeddingModel()
        self.logger = get_logger("CORTEX_MEMORY")
        self.memory_saver = MemorySaver(engine=engine, model=self.embd_model)
        
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

    def _extract_final_response_text(self, final_response) -> str:
        """Normalize final response state/model/string into plain text."""
        if final_response is None:
            return ""
        response_text = getattr(final_response, "response", None)
        if isinstance(response_text, str):
            return response_text
        if isinstance(final_response, str):
            return final_response
        return str(final_response)
    
    # ******************** Build Memory State Functions ********************
    def build_stm(
        self,
        state: ConversationState
    ):
        """
        Build the Short Term Memory (STM) based on the recent interactions and context. \n
        """
        if not self._extract_final_response_text(state.final_response):
            self.logger.error("Final response is None, STM will not be built without a valid final response.")
            raise ValueError("Final response is None, cannot build STM without a valid final response.")
        
        short_term_memory = self.model.build_stm(
            state=state
        )
        self.logger.info(f"Built STM: {short_term_memory}")
        return {
            "short_term_memory": short_term_memory,
        }
    
    def build_emotional_profile(
        self,
        state: ConversationState
    ):
        """
        Build the Emotional Profile based on the historical interactions and context. \n
        """
        state.query_time = self._get_time_behavior(state.query_timestamp)
        res = self.model.build_emotional_profile(state=state)
        emotional_profile=EmotionalProfile(
            mood_type=state.query_emotion,
            time_behavior=state.query_time,
            emotional_level=res.emotional_level,
            logical_level=res.logical_level,
            social_level=res.social_level,
            context_summary=res.context_summary
        )
        self.logger.info(f"Built Emotional Profile: {emotional_profile}")
        return {
            "query_time": state.query_time,
            "emotional_profile": emotional_profile,
        }
    
    def build_user_knowledge_base(
        self,
        state: ConversationState
    ):
        """
        Build the user's knowledge base based on the historical interactions and context. \n
        """
        res = self.model.build_user_knowledge_base(state=state)
        knowledge_base = [
            UserKnowledge(
                category=item.category,
                strictness=item.strictness,
                content=item.content,
            ) for item in res.root
        ] if res and res.root else None
        self.logger.info(f"Built User Knowledge Base: {knowledge_base}")
        return {
            "knowledge_base": knowledge_base,
        }
        
    def persist_memory_state(
        self,
        state: ConversationState
    ):
        """
        Persist the relevant memory states (STM, Emotional Profile, Knowledge Base) to the database for long-term storage and future retrieval. \n
        """
        with Session(self.engine) as session:
            if state.short_term_memory:
                updated_user_stm = {}
                if state.short_term_memory.session_preferences:
                    updated_user_stm["session_preferences"] = state.short_term_memory.session_preferences
                if state.short_term_memory.stm_summary:
                    updated_user_stm["stm_summary"] = state.short_term_memory.stm_summary
                db_obj = get_one(
                    session=session,
                    model=UserShortTermMemory,
                    user_id=state.user_id,
                    session_id=state.session_id
                )
                if db_obj:
                    update_one(
                        session=session,
                        db_obj=db_obj,
                        obj_in=updated_user_stm,
                        commit=True
                    )
                else:
                    create_one(
                        session=session,
                        obj_in=UserShortTermMemory(
                            user_id=state.user_id,
                            session_id=state.session_id,
                            stm_summary=state.short_term_memory.stm_summary or "",
                            session_preferences=state.short_term_memory.session_preferences,
                        ),
                        commit=True,
                    )
            if state.emotional_profile:
                self.logger.info(f"Persisting Emotional Profile to DB: {state.emotional_profile}")
                updated_emotional_profile = {}
                if state.emotional_profile.context_summary:
                    updated_emotional_profile["context_summary"] = state.emotional_profile.context_summary
                if state.emotional_profile.emotional_level is not None:
                    updated_emotional_profile["emotional_level"] = state.emotional_profile.emotional_level
                if state.emotional_profile.logical_level is not None:
                    updated_emotional_profile["logical_level"] = state.emotional_profile.logical_level
                if state.emotional_profile.social_level is not None:
                    updated_emotional_profile["social_level"] = state.emotional_profile.social_level

                db_obj = get_one(
                    session=session,
                    model=UserEmotionalProfile,
                    user_id=state.user_id,
                    session_id=state.session_id,
                    mood_type=state.emotional_profile.mood_type,
                    time_behavior=state.emotional_profile.time_behavior
                )
                if db_obj:
                    update_one(
                        session=session,
                        db_obj=db_obj,
                        obj_in=updated_emotional_profile,
                        commit=True
                    )
                else:
                    create_one(
                        session=session,
                        obj_in=UserEmotionalProfile(
                            user_id=state.user_id,
                            session_id=state.session_id,
                            mood_type=state.emotional_profile.mood_type,
                            time_behavior=state.emotional_profile.time_behavior,
                            emotional_level=state.emotional_profile.emotional_level,
                            logical_level=state.emotional_profile.logical_level,
                            social_level=state.emotional_profile.social_level,
                            context_summary=state.emotional_profile.context_summary,
                        ),
                        commit=True,
                    )
            if state.knowledge_base:
                user_knowledge_items = []
                for item in state.knowledge_base:
                    user_knowledge_items.append(
                        UserKnowledgeBase(
                            user_id=state.user_id,
                            category=item.category,
                            strictness=item.strictness,
                            content=item.content,
                            is_active=True,
                            embedding=self.embd_model.generate_embeddings(item.content)
                        )
                    )
                create_many(
                    session=session,
                    objects=user_knowledge_items,
                    commit=True
                )
            if state.final_response:
                final_response_text = self._extract_final_response_text(state.final_response)
                self.logger.info(f"Persisting Final Response to DB: {final_response_text}")
                self.memory_saver.save_message(
                    session_id=state.session_id,
                    user_id=state.user_id,
                    content=final_response_text,
                    role=RoleType.AI,
                    ai_client=AIClientType.CORTEX_MAIN_CLIENT
                )


    # ******************** Fetch Memory State Functions ********************
    def fetch_relevant_stm(
        self,
        state: ConversationState
    ):
        """
        Fetch relevant Short Term Memory (STM) based on the current conversation context and recent interactions. \n
        """
        user_id = state.user_id
        session_id = state.session_id
        with Session(self.engine) as session:
            res = get_one(
                session=session,
                model=UserShortTermMemory,
                user_id=user_id,
                session_id=session_id,
            )
        self.logger.info(f"Fetched STM from DB: {res}")
        state.short_term_memory = UserSTM(
            stm_summary=res.stm_summary,
            session_preferences=res.session_preferences
        ) if res else None
        return {
            "short_term_memory": state.short_term_memory,
        }
    
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
        time_behavior = self._get_time_behavior(state.query_timestamp)
        mood = state.query_emotion
        with Session(self.engine) as session:
            res = get_one(
                session=session,
                model=UserEmotionalProfile,
                user_id=user_id,
                session_id=session_id,
                mood_type=mood,
                time_behavior=time_behavior
            )
        state.emotional_profile = EmotionalProfile(
            mood_type=res.mood_type,
            time_behavior=res.time_behavior,
            emotional_level=res.emotional_level,
            logical_level=res.logical_level,
            social_level=res.social_level,
            context_summary=res.context_summary
        ) if res else None
        return {
            "query_time": time_behavior,
            "emotional_profile": state.emotional_profile,
        }
    
    def fetch_relevant_knowledge_base(
        self,
        state: ConversationState
    ):
        """
        Fetch relevant Long Term Memory (LTM) based on the historical interactions and context. \n
        """
        user_id = state.user_id
        query_embedding = self.embd_model.generate_embeddings(state.query)
        if state.orchestration_state and state.orchestration_state.user_knowledge_retrieval_keywords:
            categories = state.orchestration_state.user_knowledge_retrieval_keywords.split()
        else:
            categories = []
        
        knowledge_base = []
        for category in categories:            
            with Session(self.engine) as session:
                res = get_similar(
                    session=session,
                    model=UserKnowledgeBase,
                    query_embedding=query_embedding,
                    top_k=5,
                    user_id=user_id,
                    category=category
                )
            knowledge_base.extend(res)
        
        knowledge_base = [
            UserKnowledge(
                category=item.category,
                strictness=item.strictness,
                content=item.content,
                score=score
            ) for item, score in knowledge_base
        ] if knowledge_base else None

        return {
            "knowledge_base": knowledge_base,
        }
    
    def fetch_relevant_message_history(
        self,
        state: ConversationState
    ):
        """
        Fetch the relevant message history based on the current conversation context. \n
        """
        user_id = state.user_id
        session_id = state.session_id
        if state.orchestration_state and state.orchestration_state.referred_message_keywords:
            keywords = state.orchestration_state.referred_message_keywords.split()
        else:
            keywords = []

        if not keywords:
            return {
                "message_history": None,
            }

        keyword_text = keywords if isinstance(keywords, str) else " ".join(keywords)
        keyword_embedding = self.embd_model.generate_embeddings(keyword_text)
        messages = []
        with Session(self.engine) as session:
            res = get_similar(
                session=session,
                model=Message,
                query_embedding=keyword_embedding,
                top_k=5,
                user_id=user_id,
                session_id=session_id
            )
            messages.extend(res)

        message_states = [
            MessageState(
                message_id=str(item.message_id),
                session_id=str(item.session_id),
                user_id=str(item.user_id),
                content=item.content,
                role=item.role,
                ai_client=item.ai_client,
            )
            for item, _score in messages
        ] if messages else None

        message_history = MessageStateList(root=message_states) if message_states else None

        return {
            "message_history": message_history,
        }
    
__all__ = [
    "MemoryClient"
]