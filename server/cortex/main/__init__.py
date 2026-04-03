from cortex.graph.state import ConversationState
from utility.main import iterate_tokens_async
from nltk.tokenize import sent_tokenize
from typing import AsyncGenerator
from cortex.graph.workflow import build_memory_workflow, main_workflow
from cortex.task import MainTaskQueue, TaskStatus, TaskItem
from utility.logger import get_logger
from pprint import pprint
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
            query_emotion=emotion
        )
        return state
        
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
            res = main_workflow.invoke(state)
            print("\n\n***** Orchestration Workflow Result *****\n\n")
            pprint("Workflow Result: %s", res)
            print("\n\n\n\n")
            
            taskItem.result = {
                "response_type": "text_stream",
                "response": "This is a dummy response for the query: {}".format(query)
            }
            taskItem.status = TaskStatus.COMPLETED
            return taskItem
        except Exception as e:
            self.logger.exception("Error processing task: %s", e)
            taskItem.status = TaskStatus.FAILED
            taskItem.error = str(e)
            return taskItem
   