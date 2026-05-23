from cortex_core.graph.state import MemoryState
from cortex_core.memory.model import MemoryModel
from cortex_core.memory.embedding import EmbeddingModel
from cortex_core.memory.service.saver import MemorySaver
from sqlalchemy.engine import Engine
from sqlmodel import Session, select
from cortex_cm.utility.logger import get_logger
from cortex_cm.pg.req import (
    get_one,
    create_one,
    update_one,
)
from cortex_cm.pg import (
    UserShortTermMemory,
    UserEmotionalProfile,
    UserKnowledgeBase,
    Message,
    RoleType,
    AIClientType,
)
from cortex_cm.utility.main import extract_final_response_text

class MemoryPersister:
    def __init__(
        self, 
        engine: Engine,
        model: MemoryModel, 
        embd_model: EmbeddingModel,
        memory_saver: MemorySaver
    ):
        self.engine = engine
        self.model = model
        self.embd_model = embd_model
        self.logger = get_logger("CORTEX_MEMORY")
        self.memory_saver = memory_saver

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
        
        is_tool_used = False
        joined_tool_ids = None
        executed_tools = []

        if state.orchestration_state and state.orchestration_state.selected_tools:
            tools_list = (
                state.orchestration_state.selected_tools.root
                if hasattr(state.orchestration_state.selected_tools, "root")
                else state.orchestration_state.selected_tools
            )
            executed_tools = [t for t in tools_list if t.tool_exec_status == "completed"]
            if executed_tools:
                is_tool_used = True
                joined_tool_ids = ", ".join([t.tool_id for t in executed_tools])

        final_response_text = extract_final_response_text(state.ai_response)
        self.logger.info(f"Saving AI response to DB: {final_response_text}. Tool used: {is_tool_used}, IDs: {joined_tool_ids}")
        
        self.memory_saver.save_message(
            session_id=state.session_id,
            user_id=state.user_id,
            content=final_response_text,
            role=RoleType.AI,
            ai_client=AIClientType.CORTEX_MAIN_CLIENT,
            is_tool_used=is_tool_used,
            tool_id=joined_tool_ids
        )

__all__ = [
    "MemoryPersister"
]
