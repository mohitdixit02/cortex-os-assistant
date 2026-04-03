from cortex.graph.state import ConversationState, EmotionalProfile, UserKnowledge, UserSTM, MessageHistory
from cortex.memory.model import MemoryModel
from sqlalchemy.engine import Engine
from sqlmodel import Session
from logger import logger
from db.req import (
    get_one,
    get_similar
)
from db import (
    UserShortTermMemory,
    UserEmotionalProfile,
    UserKnowledgeBase,
    TimeOfDay,
    Message
)

class MemoryClient:
    def __init__(self, engine: Engine):
        self.engine = engine
        self.model = MemoryModel()
        
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
    
    # ******************** Build Memory State Functions ********************
    def build_stm(
        self,
        state: ConversationState
    ):
        """
        Build the Short Term Memory (STM) based on the recent interactions and context. \n
        """
        # query = "I like drinking Tea!"
        state.final_response = "Oh, nice, I also enjoy a good cup of tea. Do you have a favorite type or flavor?"
        short_term_memory = self.model.build_stm(
            state=state
        )
        logger.info(f"Built STM: {short_term_memory}")
        return {
            "final_response": state.final_response,
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
        emotional_profile = self.model.build_emotional_profile(
            state=state
        )
        logger.info(f"Built Emotional Profile: {emotional_profile}")
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
        knowledge_base = self.model.build_user_knowledge_base(
            state=state
        )
        logger.info(f"Built User Knowledge Base: {knowledge_base}")
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
                session.add(UserShortTermMemory(
                    user_id=state.user_id,
                    session_id=state.session_id,
                    stm_summary=state.short_term_memory.stm_summary,
                    session_preferences=state.short_term_memory.session_preferences
                ))
            if state.emotional_profile:
                print(f"Persisting Emotional Profile to DB: {state.emotional_profile}")
                session.add(UserEmotionalProfile(
                    user_id=state.user_id,
                    session_id=state.session_id,
                    mood_type=state.emotional_profile.mood_type,
                    time_behavior=state.emotional_profile.time_behavior,
                    emotional_level=state.emotional_profile.emotional_level,
                    logical_level=state.emotional_profile.logical_level,
                    social_level=state.emotional_profile.social_level,
                    context_summary=state.emotional_profile.context_summary
                ))
            if state.knowledge_base:
                for item in state.knowledge_base:
                    session.add(UserKnowledgeBase(
                        user_id=state.user_id,
                        category=item.category,
                        strictness=item.strictness,
                        content=item.content,
                        is_active=True,
                        embedding=self.model.generate_embeddings(item.content)
                    ))
            session.commit()
            
    def persist_message_history(
        self,
        state: ConversationState
    ):
        """
        Persist the relevant message history to the database for long-term storage and future retrieval. \n
        """
        with Session(self.engine) as session:
            if state.message_history:
                for message in state.message_history.messages:
                    session.add(Message(
                        user_id=state.user_id,
                        session_id=state.session_id,
                        role=message["role"],
                        content=message["content"],
                        timestamp=message["timestamp"],
                        embedding=self.model.generate_embeddings(message["content"])
                    ))
            session.commit()


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
        print(f"Fetched STM from DB: {res}")
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
                user_id=state.user_id,
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
            "emotional_profile": state.emotional_profile,
        }
    
    def fetch_relevant_knowledge_base(
        self,
        state: ConversationState
    ):
        """
        Fetch relevant Long Term Memory (LTM) based on the historical interactions and context. \n
        """
        
        #/pending/ Have to make sure the use of Category in the concept
        user_id = state.user_id
        query_embedding = self.model.generate_embeddings(state.query)
        with Session(self.engine) as session:
            res = get_similar(
                session=session,
                model=UserKnowledgeBase,
                query_embedding=query_embedding,
                top_k=5,
                user_id=user_id
            )
        state.knowledge_base = [
            UserKnowledge(
                category=item.category,
                strictness=item.strictness,
                content=item.content,
                score=score
            ) for item, score in res
        ] if res else None
        return {
            "knowledge_base": state.knowledge_base,
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
        query_embedding = self.model.generate_embeddings(state.query)
        with Session(self.engine) as session:
            res = get_similar(
                session=session,
                model=Message,
                query_embedding=query_embedding,
                top_k=5,
                user_id=user_id,
                session_id=session_id
            )
        res = [{
                "role": item.role,
                "content": item.content,
                "timestamp": item.timestamp
            } for item, score in res
        ] if res else None
        state.message_history = MessageHistory(messages=res) if res else None
        return {
            "message_history": state.message_history,
        }
    
__all__ = [
    "MemoryClient"
]