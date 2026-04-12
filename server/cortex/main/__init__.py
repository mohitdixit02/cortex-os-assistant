from cortex.graph.state import ConversationState, MemoryState, MemoryEmotionalProfile, EmotionalProfile, FinalResponseGenerationState, OrchestrationState, CortexToolList, CortexTool
from utility.main import iterate_tokens_async
from nltk.tokenize import sent_tokenize
from typing import AsyncGenerator
from cortex.graph.workflow import (
    main_workflow, 
    build_memory_workflow,
    test_workflow,
    # test_workflow_2
)
from cortex.task import MainTaskQueue, TaskStatus, TaskItem
from utility.logger import get_logger
from db import TimeOfDay
import asyncio
# keep listening and processing until the program is terminated

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
            user_id=user_id,
            session_id=session_id,
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
        
    async def listen_task_queue(self):
        """
        ## Task Queue Listener \n
        Listens for incoming tasks from the TaskQueue and process them accordingly. \n
        This function will continuously run in the background on main thread, awaiting new tasks and dispatching them to the appropriate handlers based on their type or content. \n
        
        **Initialize it using asyncio.create_task()** in the respective entry point
        """
        
        while True:        
            self.logger.info("Waiting for tasks in the MainTaskQueue...")
            task = await MainTaskQueue.pick_task()
            self.logger.info("Received task: %s with id: %s", task.task_name, task.task_id)
            updated_task = await self._handle_task_queue(task)
            
            if updated_task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                self.logger.warning("Task %s is still in progress. Current status: %s", task.task_id, updated_task.status)
                continue  # Skip updating the task status until it's completed or failed
                
            await MainTaskQueue.submit_task(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED if updated_task.result else TaskStatus.FAILED,
                status_message=updated_task.result if updated_task.result else updated_task.error
            )
            self.logger.info("Completed Task with id: %s and name: %s", task.task_id, task.task_name)
            self.logger.info("Task Status: %s", updated_task.status)
            
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
            res = test_workflow.invoke(state)
            # self.logger.info("Test workflow result: %s", res)
            
            final_response_text = "Dummy response for query: " + query
            
            # ************** original flow *****************
            # res = main_workflow.invoke(state)

            # workflow_final_response = res.get("final_response") if isinstance(res, dict) else getattr(res, "final_response", None)
            # final_response_text = self._extract_final_response_text(workflow_final_response)
            
            # # Build memory
            # asyncio.create_task(self._build_memory_workflow(res))

            self.logger.info("Final response generated: %s", res)
            self.logger.info("Response from main workflow >> %s", final_response_text if final_response_text else "No final response generated")
            if final_response_text:
                self.logger.info("Generated response: %s", final_response_text)
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
   