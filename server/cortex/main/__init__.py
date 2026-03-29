import asyncio
from sensory.STT import STTClient
from sensory.TTS import TTSClient
from cortex.main.model import CortexMainModel
from utility.main import iterate_tokens_async
from nltk.tokenize import sent_tokenize
from typing import AsyncGenerator
from cortex.main.task import MainTaskQueue, TaskStatus, TaskItem
from logger import logger
# keep listening and processing until the program is terminated

class MainClient:
    """
        ### Cortex Main Client \n
        The Prinicipal Orchestrator for handling and controling all AI Workflow Pipelines \n
        
        **Key Features:** \n
        - Will be coming soon
    """
    
    def __init__(self):
        self.model = CortexMainModel()
        
    async def listen_task_queue(self):
        """
        ## Task Queue Listener \n
        Listens for incoming tasks from the TaskQueue and process them accordingly. \n
        This function will continuously run in the background on main thread, awaiting new tasks and dispatching them to the appropriate handlers based on their type or content. \n
        
        **Initialize it using asyncio.create_task()** in the respective entry point
        """
        
        while True:        
            logger.info("Waiting for tasks in the MainTaskQueue...")
            task = await MainTaskQueue.pick_task()
            logger.info("Received task: %s with id: %s", task.task_name, task.task_id)
            updated_task = await self._handle_task_queue(task)
            
            if updated_task.status not in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                logger.warning("Task %s is still in progress. Current status: %s", task.task_id, updated_task.status)
                continue  # Skip updating the task status until it's completed or failed
                
            await MainTaskQueue.submit_task(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED if updated_task.result else TaskStatus.FAILED,
                status_message=updated_task.result
            )
            logger.info("Completed Task with id: %s and name: %s", task.task_id, task.task_name)
                
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
            logger.info("Processing task with query: %s", query)
            
            generator = self.model.stream_text_tokens(query)
            print(type(generator))
            taskItem.result = {
                "response_type": "text_stream",
                "response": generator
            }
            taskItem.status = TaskStatus.COMPLETED
            return taskItem
        except Exception as e:
            logger.exception("Error processing task: %s", e)
            taskItem.status = TaskStatus.FAILED
            taskItem.result = str(e)
            return taskItem
   