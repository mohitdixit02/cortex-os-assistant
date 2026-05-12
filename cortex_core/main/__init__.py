from cortex_cm.pg.enums import TaskOwner
from cortex_core.graph.state import (
    ConversationState,
    EventToolState, 
    MemoryState, 
    MemoryEmotionalProfile, 
    EmotionalProfile, 
    FinalResponseGenerationState, 
    OrchestrationState, 
    CortexToolList, 
    CortexTool,
)
from cortex_cm.utility.main import iterate_tokens_async
from nltk.tokenize import sent_tokenize
from typing import AsyncGenerator
from cortex_core.graph.workflow import (
    main_workflow, 
    # test_workflow,
    # test_workflow_2
)
from cortex_core.graph.memory import build_memory_workflow
from cortex_core.graph.event import event_tool_workflow
from cortex_queue.dto import TaskStatus, TaskItem
from cortex_cm.utility.logger import get_logger
from cortex_cm.pg import TimeOfDay
import asyncio

class MainClient:
    """
        ### Cortex Main Client \n
        The Prinicipal Orchestrator for handling and controling all AI Workflow Pipelines \n
        
        **Key Features:** \n
        - Will be coming soon
    """
    
    def __init__(self):
        self.logger = get_logger("CORTEX_MAIN")

    def _extract_final_response_text(self, final_response) -> str:
        """Normalize final response state/model/string into plain text."""
        if final_response is None:
            return ""
        if isinstance(final_response, dict):
            response_text = final_response.get("response")
            if isinstance(response_text, str):
                return response_text
        response_text = getattr(final_response, "response", None)
        if isinstance(response_text, str):
            return response_text
        if isinstance(final_response, str):
            return final_response
        return str(final_response)
        
    def initialize_conversation_state(
        self,
        taskItem: TaskItem
    ) -> ConversationState:
        """
        Initialize the conversation state for a new conversation session. \n
        **Input**: \n
        - `taskItem`: The task item containing the initial query and metadata for the conversation. \n
        **Returns**: \n
        - `ConversationState`: The initialized conversation state object with default or extracted values from the task item.
        """
        self.logger.info("***** Task Item >> %s", taskItem)
        self.logger.info("***** Task Metadata >> %s", taskItem.metadata)
        user_id = taskItem.metadata.get("user_id")
        session_id = taskItem.metadata.get("session_id")
        task_id = taskItem.task_id
        voice_client_response = taskItem.metadata.get("voice_client_response")
        
        if not user_id or not session_id:
            self.logger.error("Missing user_id or session_id in task metadata. Cannot initialize conversation state.")
            raise ValueError("Missing user_id or session_id in task metadata.")
        
        query = taskItem.payload.get("query")
        
        if not query:
            self.logger.error("Missing query in task payload. Cannot initialize conversation state.")
            raise ValueError("Missing query in task payload.")
        
        emotion = taskItem.payload.get("emotion", "neutral")
        self.logger.info("Initializing conversation state for user_id: %s, session_id: %s, query: %s, emotion: %s", user_id, session_id, query, emotion)
        
        state = ConversationState(
            user_id=str(user_id),
            session_id=str(session_id),
            task_id=str(task_id),
            query=query,
            query_emotion=emotion,
            voice_client_response=voice_client_response
        )
        return state
    
    def initialize_memory_state(self, convState: ConversationState) -> MemoryState:
        """
        Initialize the memory state for a new conversation session. \n
        **Input**: \n
        - `convState`: The conversation state object containing the initial query and metadata for the conversation. \n
        **Returns**: \n
        - `MemoryState`: The initialized memory state object with default or extracted values from the conversation state.
        """
        if isinstance(convState, dict):
            convState = ConversationState.model_validate(convState)
        
        self.logger.info("enter initialize_memory_state with conversation state: %s", convState)
        if convState is None:
            self.logger.error("Conversation state is None. Cannot initialize memory state.")
            raise ValueError("Conversation state is None. Cannot initialize memory state.")
        
        if convState.final_response is None:
            self.logger.error("Final response in conversation state is None. Can't initialize memory state without AI response.")
            raise ValueError("Final response in conversation state is None. Can't initialize memory state without AI response.")
        
        ai_response = self._extract_final_response_text(convState.final_response)
        
        emotional_profile = MemoryEmotionalProfile(
            emotional_level=convState.emotional_profile.emotional_level,
            logical_level=convState.emotional_profile.logical_level,
            social_level=convState.emotional_profile.social_level,
            context_summary=convState.emotional_profile.context_summary
        ) if convState.emotional_profile else None
        
        memory_state = MemoryState(
            user_id=convState.user_id,
            session_id=convState.session_id,
            query=convState.query,
            ai_response=ai_response,
            query_emotion=convState.query_emotion,
            query_time=convState.query_time,
            short_term_memory=convState.short_term_memory,
            emotional_profile=emotional_profile,
            older_knowledge_base=convState.knowledge_base
        )
        
        self.logger.info("Initialized memory state: %s", memory_state)
        return memory_state
    
    def initialize_event_tool_state(self, taskItem: TaskItem) -> EventToolState:
        message_id = taskItem.metadata.get("message_id")
        if not message_id:
            self.logger.error("Missing message_id in task metadata. Cannot initialize event tool state.")
            raise ValueError("Missing message_id in task metadata.")
        
        event_name = taskItem.payload.get("name")
        event_description = taskItem.payload.get("event_description")
        trigger_time = taskItem.payload.get("trigger_time")
        
        if not event_description or not trigger_time:
            self.logger.error("Missing event_description or trigger_time in task metadata. Cannot initialize event tool state.")
            raise ValueError("Missing event_description or trigger_time in task metadata.")
        
        event_state = EventToolState(
            message_id=message_id,
            event_name=event_name,
            event_description=event_description,
            trigger_time=trigger_time
        )
        self.logger.info("Initialized event tool state: %s", event_state)
        return event_state

    async def _build_memory_workflow(self, state: ConversationState):
        """
        ## Memory Workflow Builder \n
        This function takes the current conversation state and builds the memory workflow for the conversation. \n
        """
        memory_state = self.initialize_memory_state(state)
        try:
            await build_memory_workflow.ainvoke(memory_state)
        except Exception as memory_exc:
            self.logger.exception("Memory workflow failed after response generation: %s", memory_exc)
            
    async def _handle_voice_client_task(self, taskItem: TaskItem) -> TaskItem:
        """
        ### Voice Client Task Handler \n
        **Handles tasks specific to voice client interactions.**
        It processes the task item received from the Task Queue that are related to voice client interactions and generates appropriate responses or actions based on the payload and metadata of the task item. \n
        **Input**: \n
        - `TaskItem`: The task item to be processed (received from the Task Queue) \n
        
        **Returns**: \n
        - `TaskItem`: The updated task item object after processing.
        """
        try:
            payload = taskItem.payload
            query = payload.get("query", "")
            self.logger.info("Processing task with query: %s", query)
            
            # Orchestrator code
            state = self.initialize_conversation_state(taskItem)
            
            # state.final_response = FinalResponseGenerationState(
            #     response="Yes, I know that you like tea and are in a good mood."
            # )
            # state.emotional_profile = EmotionalProfile(
            #     time_behavior=TimeOfDay.AFTERNOON,
            #     mood_type=state.query_emotion,
            #     emotional_level=5,
            #     logical_level=7,
            #     social_level=6,
            #     context_summary="User seems to be in a good mood and is talking about tea."
            # )
            # test workflow for memory building
            
            # selected_tools=CortexToolList(root=[CortexTool(tool_id='web_search_01', instructions="Search for popular pizza types, toppings, and recipes. Consider Mohit's neutral mood and casual tone preference.", tool_result=None, tool_exec_status='failed')])
            
            # web_tool = CortexTool(
            #     tool_id="web_search_01",
            #     instructions=""
            # )
            
            # state.orchestration_state = OrchestrationState(
            #     user_knowledge_retrieval_keywords=['drinking preference', 'favorite beverages', 'likes and dislikes'],
            #     is_message_referred=True,
            #     referred_message_keywords="drinking preference, favorite beverages, likes and dislikes",
            #     is_tool_required=False,
            #     # selected_tools=CortexToolList(root=[web_tool]),
            #     user_knowledge_acceptance_threshold=0.6
            # )
            
            # state1 = test_workflow.invoke(state)
            # memory_state = self.initialize_memory_state(state1)
            # res = test_workflow_2.invoke(memory_state)
            # res = test_workflow.invoke(state)
            # self.logger.info("Test workflow result: %s", res)
            
            # final_response_text = "Dummy response for query: " + query
            
            # ************** original flow *****************
            res = main_workflow.invoke(state)

            workflow_final_response = res.get("final_response") if isinstance(res, dict) else getattr(res, "final_response", None)
            final_response_text = self._extract_final_response_text(workflow_final_response)

            self.logger.info("Final response generated: %s", res)
            self.logger.info("Response from main workflow >> %s", final_response_text if final_response_text else "No final response generated")
            if final_response_text:
                self.logger.info("Generated response: %s", final_response_text)
                
                # Build memory
                asyncio.create_task(self._build_memory_workflow(res))
                
                taskItem.result = {
                    "response_type": "text_stream",
                    "response": final_response_text,
                }
                taskItem.status = TaskStatus.COMPLETED
                return taskItem
            else:
                self.logger.error("Failed to generate response for query: %s", query)
                taskItem.status = TaskStatus.FAILED
                taskItem.error = "Failed to generate response."
                return taskItem
        except Exception as e:
            self.logger.exception("Error processing task: %s", e)
            taskItem.status = TaskStatus.FAILED
            taskItem.error = str(e)
            return taskItem
    
    async def _handle_event_tool_task(self, taskItem: TaskItem) -> TaskItem:
        event_state = self.initialize_event_tool_state(taskItem)
        try:
            res = event_tool_workflow.invoke(event_state)
            final_response = res.get("final_reminder") if isinstance(res, dict) else getattr(res, "final_reminder", None)
            self.logger.info("Event tool workflow result: %s", res)
            taskItem.result = {
                "response_type": "text_stream",
                "response": final_response
            }
            taskItem.status = TaskStatus.COMPLETED
            return taskItem
        except Exception as e:
            self.logger.exception("Error processing event tool task: %s", e)
            taskItem.status = TaskStatus.FAILED
            taskItem.error = str(e)

    async def _handle_task_queue(self, taskItem: TaskItem) -> TaskItem:
        """
        ### Task Handler \n
        **Handles tasks retrieved from the `TaskQueue`.**
        It processes the task item received from the Task Queue based on the paramaters (like paylaod or taskname) and responsds with the updated task item object. \n
        **Input**: \n
        - `TaskItem`: The task item to be processed (received from the Task Queue) \n
        
        **Returns**: \n
        - `TaskItem`: The updated task item object after processing.
        """
        try:
            metadata = taskItem.metadata or {}
            task_owner = metadata.get("task_owner")
            self.logger.info("Handling task with owner: %s", task_owner)
            if task_owner == TaskOwner.VOICE_CLIENT.value:
                return await self._handle_voice_client_task(taskItem)
            elif task_owner == TaskOwner.EVENT_TOOL.value:
                return await self._handle_event_tool_task(taskItem)
            else:
                self.logger.warning("No handler implemented for task owner: %s. Marking task as failed.", task_owner)
                taskItem.status = TaskStatus.FAILED
                taskItem.error = f"No handler implemented for task owner: {task_owner}"
                return taskItem
        except Exception as e:
            self.logger.exception("Error handling task: %s", e)
            taskItem.status = TaskStatus.FAILED
            taskItem.error = str(e)
            return taskItem
