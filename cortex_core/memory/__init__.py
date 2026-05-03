from cortex_core.graph.state import (
    ConversationState,
    EmotionalProfile,
    UserKnowledge,
    UserSTM,
    MessageHistory,
    MessageState,
    MessageStateList,
    MemoryState
)
from typing import Literal, Optional
from cortex_core.memory.model import MemoryModel
from cortex_core.memory.embedding import EmbeddingModel
from cortex_core.memory.saver import MemorySaver
from sqlalchemy import func
from sqlalchemy.engine import Engine
from sqlmodel import Session, select
from cortex_cm.utility.logger import get_logger
from cortex_cm.pg.req import (
    get_one,
    get_similar,
    create_one,
    create_many,
    update_one,
    get_many,
)
from cortex_cm.pg import (
    UserShortTermMemory,
    UserEmotionalProfile,
    UserKnowledgeBase,
    TimeOfDay,
    Message,
    RoleType,
    AIClientType,
    Task,
)
from datetime import datetime, timezone
UTC_NOW = lambda: datetime.now(timezone.utc)

# Recheck knowledge base retrival - update fetch effeciency and relevance imporvement
# External Tools Integration
# Qwen Model Intergration for Routing

# Self reference: value x means x complete conversations (user query + ai response) in the message history
MINIMUM_CONVERSATION_HISTORY_COUNT = 2 # Must be less than what is going to summarize
CONVERSATION_HISTORY_SUMMARIZATION_THRESHOLD = 5 # Can't be zero as summarization is must (>= 1)

MESSAGES_REJECTION_THRESHOLD = 0.1 # Messages only similar more than 10% will be kept.
MESSAGES_MAX_LIMIT = 15 # Max messages to send to Cortex

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

    def _get_recent_conversation_stm(
        self,
        session: Session,
        user_id: str,
        session_id: str,
    ) -> str:
        """
        Returns recent conversation text for STM building. \n
        """
        recent_user_messages = list(session.exec(
            select(Message.created_at)
            .where(
                Message.user_id == user_id,
                Message.session_id == session_id,
                Message.is_summarized == False,
                Message.role == RoleType.USER,
            )
            .order_by(Message.created_at.asc())
            .limit(1)
        ).all())

        if not recent_user_messages:
            return ""
                
        recent_conversations = list(session.exec(
            select(Message)
            .where(
                Message.user_id == user_id,
                Message.session_id == session_id,
                Message.is_summarized == False,
                Message.created_at >= recent_user_messages[0]
            )
            .order_by(Message.created_at.asc())
        ).all())
        
        res = ""
        for msg in recent_conversations:
            if msg.role == RoleType.USER:
                res += f"USER: {msg.content}\n"
            elif msg.role == RoleType.AI:   
                res += f"AI: {msg.content}\n"
        
        return res.strip()
    
    def retrieve_unsummarized_messages(self, state: MemoryState) -> MemoryState:
        if (CONVERSATION_HISTORY_SUMMARIZATION_THRESHOLD - MINIMUM_CONVERSATION_HISTORY_COUNT) <= 0:
            self.logger.error("Invalid configuration: CONVERSATION_HISTORY_SUMMARIZATION_THRESHOLD must be strictly greater than MINIMUM_CONVERSATION_HISTORY_COUNT.")
            raise ValueError("Invalid configuration: CONVERSATION_HISTORY_SUMMARIZATION_THRESHOLD must be strictly greater than MINIMUM_CONVERSATION_HISTORY_COUNT.")

        with Session(self.engine) as session:
            non_summarized_messages = list(session.exec(
                select(Message.created_at)
                .where(
                    Message.user_id == state.user_id,
                    Message.session_id == state.session_id,
                    Message.is_summarized == False,
                    Message.role == RoleType.USER,
                )
                .order_by(Message.created_at.asc())
            ).all())
            
        if len(non_summarized_messages) >= CONVERSATION_HISTORY_SUMMARIZATION_THRESHOLD:
            state.stm_start_update_timestamp = non_summarized_messages[0]
            last_index = len(non_summarized_messages) - MINIMUM_CONVERSATION_HISTORY_COUNT
            state.stm_end_update_timestamp = non_summarized_messages[last_index] if last_index >= 0 else UTC_NOW()
            self.logger.info(f"Threshold exceeded for building STM: Found {len(non_summarized_messages)} non-summarized user messages")
        else:
            state.stm_start_update_timestamp = None
            state.stm_end_update_timestamp = None
            self.logger.info(f"No need to build STM: Found only {len(non_summarized_messages)} non-summarized user messages")
        return {
            "stm_start_update_timestamp": state.stm_start_update_timestamp,
            "stm_end_update_timestamp": state.stm_end_update_timestamp
        }
    
    # ******************** Build Memory State Functions ********************
    def route_build_stm_required(self, state: MemoryState) -> Literal["build_stm", "build_emotional_profile", "build_user_knowledge_base"]:
        """
        Determine if building STM is required based on the current memory state. \n
        **Input:** `MemoryState` object \n
        **Output:** Boolean indicating whether to route to build STM or not \n
        """
        if state.stm_start_update_timestamp:
            self.logger.info("Routing to build STM: STM update timestamp is set")
            return "build_stm"
        self.logger.info("No need to route to build STM: No new non-summarized messages found.")
        return ["build_emotional_profile", "build_user_knowledge_base"]
        
    def build_stm(
        self,
        state: MemoryState
    ):
        """
        Build the Short Term Memory (STM) based on the recent interactions and context. \n
        """
        
        constrains = (
            Message.user_id == state.user_id,
            Message.session_id == state.session_id,
            Message.is_summarized == False,
        )
        
        if state.stm_start_update_timestamp:
            constrains += (Message.created_at >= state.stm_start_update_timestamp,)
        if state.stm_end_update_timestamp:
            constrains += (Message.created_at < state.stm_end_update_timestamp,)
        else:
            constrains += (Message.created_at < UTC_NOW(),)
        
        with Session(self.engine) as session:
            recent_conversations = list(session.exec(
                select(Message)
                .where(*constrains)
                .order_by(Message.created_at.asc())
            ).all())
        
        res = ""
        for msg in recent_conversations:
            if msg.role == RoleType.USER:
                res += f"USER: {msg.content}\n"
            elif msg.role == RoleType.AI:   
                res += f"AI: {msg.content}\n"
        
        if state.short_term_memory:
            state.short_term_memory.recent_conversation = res.strip()
        else:
            state.short_term_memory = UserSTM(
                stm_summary=None,
                session_preferences=None,
                recent_conversation=res.strip()
            )
        self.logger.info(f"Built recent conversation for STM: {state.short_term_memory.recent_conversation}")
        
        short_term_memory = self.model.build_stm(state=state)
        self.logger.info(f"Built STM: {short_term_memory}")
        return {
            "short_term_memory": short_term_memory,
        }
    
    def build_emotional_profile(
        self,
        state: MemoryState
    ):
        """
        Build the Emotional Profile based on the historical interactions and context. \n
        """
        res = self.model.build_emotional_profile(state=state)
        self.logger.info(f"Built Emotional Profile: {res}")
        return {
            "emotional_profile": res,
        }
    
    def build_user_knowledge_base(
        self,
        state: MemoryState
    ):
        """
        Build the user's knowledge base based on the historical interactions and context. \n
        """
        res = self.model.build_user_knowledge_base(state=state)
        self.logger.info(f"Built User Knowledge Base: {res}")
        return {
            "knowledge_items": res,
        }
        
    def persist_memory_state(
        self,
        state: MemoryState
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
                    mood_type=state.query_emotion,
                    time_behavior=state.query_time
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
                            mood_type=state.query_emotion,
                            time_behavior=state.query_time,
                            emotional_level=state.emotional_profile.emotional_level,
                            logical_level=state.emotional_profile.logical_level,
                            social_level=state.emotional_profile.social_level,
                            context_summary=state.emotional_profile.context_summary,
                        ),
                        commit=True,
                    )
                    
            if state.knowledge_items:
                user_knowledge_items = state.knowledge_items
                for item in user_knowledge_items.root:
                    if item.action == "update" and item.trait_id:
                        self.logger.info(f"Updating existing memory item with trait_id {item.trait_id} for user knowledge base: {item}")
                        db_obj = get_one(
                            session=session,
                            model=UserKnowledgeBase,
                            trait_id=item.trait_id
                        )
                        if db_obj:
                            update_one(
                                session=session,
                                db_obj=db_obj,
                                obj_in={
                                    "strictness": item.strictness,
                                    "content": item.content,
                                    "embedding": self.embd_model.generate_embeddings(item.content)
                                },
                                commit=True
                            )
                        else:
                            self.logger.warning(f"No existing memory item found with trait_id {item.trait_id} for update. Skipping update for this item.")
                    elif item.action == "add":
                        create_one(
                            session=session,
                            obj_in=UserKnowledgeBase(
                                user_id=state.user_id,
                                strictness=item.strictness,
                                content=item.content,
                                is_active=True,
                                embedding=self.embd_model.generate_embeddings(item.content)
                            ),
                            commit=True
                        )
                    else:
                        self.logger.warning(f"Invalid action '{item.action}' for knowledge item. Skipping this item.")
                self.logger.info(f"Persisting User Knowledge Base to DB: {state.knowledge_items}")
            if state.stm_start_update_timestamp:
                self.logger.info(f"Updating messages as summarized for session_id: {state.session_id}, user_id: {state.user_id} from {state.stm_start_update_timestamp} to {state.stm_end_update_timestamp}")
                with Session(self.engine) as session:
                    stmt = (
                        select(Message)
                        .where(
                            Message.user_id == state.user_id,
                            Message.session_id == state.session_id,
                            Message.is_summarized == False,
                            Message.created_at >= state.stm_start_update_timestamp,
                            Message.created_at < state.stm_end_update_timestamp if state.stm_end_update_timestamp else True
                        )
                    )
                    messages_to_update = session.exec(stmt).all()
                    for msg in messages_to_update:
                        update_one(
                            session=session,
                            db_obj=msg,
                            obj_in={"is_summarized": True},
                            commit=False,
                            refresh=False,
                        )
                    session.commit()
                    
    def persist_ai_response(
        self,
        state: MemoryState
    ):
        """
        Save the AI response to the database. \n
        """
        if not state.ai_response:
            self.logger.info("No AI response found in the memory state. Skipping saving AI response.")
            return
        
        final_response_text = self._extract_final_response_text(state.ai_response)
        self.logger.info(f"Saving AI response to DB: {final_response_text}")
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

            recent_messages = self._get_recent_conversation_stm(
                session=session,
                user_id=user_id,
                session_id=session_id,
            )
            
        if recent_messages:
            recent_conversation = "\nRecent Conversation:\n" + recent_messages
        else:
            recent_conversation = ""

        has_recent_context = bool(recent_conversation.strip())
        if res or has_recent_context:
            state.short_term_memory = UserSTM(
                stm_summary=res.stm_summary if res and res.stm_summary else "",
                session_preferences=res.session_preferences if res else None,
                recent_conversation=recent_conversation if has_recent_context else None,
            )
        else:
            state.short_term_memory = None
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
        relevant_keywords_embedding = []
        if state.orchestration_state and state.orchestration_state.user_knowledge_retrieval_keywords:
            for keywords in state.orchestration_state.user_knowledge_retrieval_keywords:
                relevant_keywords_embedding.append(self.embd_model.generate_embeddings(keywords))
        
        knowledge_base = []
        if relevant_keywords_embedding:
            for rke in relevant_keywords_embedding:            
                with Session(self.engine) as session:
                    res = get_similar(
                        session=session,
                        model=UserKnowledgeBase,
                        query_embedding=rke,
                        top_k=3,
                        user_id=user_id,
                    )
                knowledge_base.extend(res)
        else:
            with Session(self.engine) as session:
                res = get_similar(
                    session=session,
                    model=UserKnowledgeBase,
                    query_embedding=query_embedding,
                    top_k=5,
                    user_id=user_id,
                )
            knowledge_base.extend(res)

        deduped_knowledge: dict[str, tuple[UserKnowledgeBase, float]] = {}
        for item, similarity in knowledge_base:
            trait_key = str(item.trait_id)
            existing = deduped_knowledge.get(trait_key)
            if existing is None or similarity > existing[1]:
                deduped_knowledge[trait_key] = (item, similarity)
        
        ACCEPTABLE_SIMILARITY_THRESHOLD = state.orchestration_state.user_knowledge_acceptance_threshold if state.orchestration_state else 0.5
        self.logger.info(f"Deduped knowledge items count before applying similarity threshold: {len(deduped_knowledge)}")
        deduped_knowledge = {
            trait_id: (item, sim) for trait_id, (item, sim) in deduped_knowledge.items() if sim >= ACCEPTABLE_SIMILARITY_THRESHOLD
        }                
        
        knowledge_base = sorted(
            deduped_knowledge.values(),
            key=lambda pair: pair[1],
            reverse=True,
        )
        
        knowledge_base = [
            UserKnowledge(
                trait_id=str(item.trait_id),
                strictness=item.strictness,
                content=item.content,
                score=score
            ) for item, score in knowledge_base
        ] if knowledge_base else None

        self.logger.info(f"Fetched relevant knowledge base items: {knowledge_base} with acceptance threshold: {ACCEPTABLE_SIMILARITY_THRESHOLD}")
        
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
            keywords = state.orchestration_state.referred_message_keywords
        else:
            keywords = ""

        if not keywords or keywords.strip() == "":
            return {
                "message_history": None,
            }

        task_id = state.task_id
        user_message_created_at = None
        if task_id:
            with Session(self.engine) as session:
                user_message_created_at = session.exec(
                    select(Message.created_at)
                    .join(Task, Task.message_id == Message.message_id)
                    .where(Task.task_id == task_id)
                    .where(Message.user_id == user_id)
                    .where(Message.session_id == session_id)
                ).first()

        keyword_embedding = self.embd_model.generate_embeddings(keywords)
        messages = []
        with Session(self.engine) as session:
            similarity_expr = (1.0 - Message.embedding.cosine_distance(keyword_embedding)).label("similarity")

            stmt = (
                select(Message, similarity_expr)
                .where(
                    Message.user_id == user_id,
                    Message.session_id == session_id,
                    (
                        (Message.role == RoleType.USER)
                        | (
                            (Message.role == RoleType.AI)
                            & (
                                Message.ai_client.is_(None)
                                | (Message.ai_client != AIClientType.VOICE_CLIENT)
                            )
                        )
                    ),
                    Message.embedding.is_not(None),
                    func.vector_dims(Message.embedding) == len(keyword_embedding),
                    similarity_expr >= MESSAGES_REJECTION_THRESHOLD,
                )
            )

            if user_message_created_at:
                stmt = stmt.where(Message.created_at < user_message_created_at)

            stmt = stmt.order_by(similarity_expr.desc()).limit(MESSAGES_MAX_LIMIT)

            res = session.exec(stmt).all()
            messages.extend(res)

        message_states = [
            MessageState(
                message_id=str(item.message_id),
                session_id=str(item.session_id),
                user_id=str(item.user_id),
                content=item.content,
                role=item.role,
                ai_client=item.ai_client,
                is_summarized=item.is_summarized,
            )
            for item, _score in messages
        ] if messages else None

        message_history = MessageStateList(root=message_states) if message_states else None

        self.logger.info(f"Fetched relevant message history: {message_history} for keywords: '{keywords}' with rejection threshold: {MESSAGES_REJECTION_THRESHOLD}")
        return {
            "message_history": message_history,
        }
    
__all__ = [
    "MemoryClient"
]