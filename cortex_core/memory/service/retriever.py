from cortex_core.graph.state import (
    ConversationState,
    EmotionalProfile,
    UserKnowledge,
    UserSTM,
    MessageState,
    MessageStateList,
    MemoryState
)
from cortex_core.memory.model import MemoryModel
from cortex_core.memory.embedding import EmbeddingModel
from sqlalchemy import func
from sqlalchemy.engine import Engine
from sqlmodel import Session, select
from cortex_cm.utility.logger import get_logger
from cortex_cm.pg.req import (
    get_one,
    get_similar,
)
from cortex_cm.pg import (
    UserShortTermMemory,
    UserEmotionalProfile,
    UserKnowledgeBase,
    Message,
    RoleType,
    AIClientType,
    Task,
)
from cortex_cm.utility.time_utils import UTC_NOW

# Self reference: value 'x' means 'x' complete conversations (user query + ai response) in the message history
MINIMUM_CONVERSATION_HISTORY_COUNT = 2 # Must be less than what is going to summarize
CONVERSATION_HISTORY_SUMMARIZATION_THRESHOLD = 5 # Can't be zero as summarization is must (>= 1)

MESSAGES_REJECTION_THRESHOLD = 0.1 # Messages only similar more than 10% will be kept.
MESSAGES_MAX_LIMIT = 15 # Max messages to send to Cortex

class MemoryRetriever:
    def __init__(
        self, 
        engine: Engine, 
        model: MemoryModel,
        embd_model: EmbeddingModel,
    ):
        self.engine = engine
        self.model = model
        self.embd_model = embd_model
        self.logger = get_logger("CORTEX_MEMORY")

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
        time_behavior = state.query_time
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
    "MemoryRetriever"
]
