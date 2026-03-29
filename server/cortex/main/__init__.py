import asyncio
from sensory.STT import STTClient
from sensory.TTS import TTSClient
from cortex.voice.model import VoiceMainModel
from utility.main import iterate_tokens_async
from nltk.tokenize import sent_tokenize
from typing import AsyncGenerator
from cortex.main.task import MainTaskQueue, TaskStatus
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
        # self.stt_client = STTClient()
        # self.tts_client = TTSClient()
        self.model = VoiceMainModel()
        
    async def listen_task_queue(self):
        """
        Main loop to listen for incoming tasks from the TaskQueue and process them accordingly. \n
        This function will continuously run in the background, awaiting new tasks and dispatching them to the appropriate handlers based on their type or content. \n
        **Key Features:** \n 
        - Continuously listens for new tasks without blocking the main thread, allowing for responsive handling of incoming requests. \n
        """
        
        while True:        
            logger.info("Waiting for tasks in the MainTaskQueue...")
            task = await MainTaskQueue.pick_task()
            logger.info("Received task: %s with payload: %s", task.task_name, task.payload)
            if task.task_name == "TextResponseTask":
                logger.info("Processing TextResponseTask with query: %s", task.payload.get("query"))
                query = task.payload["query"]
                response_ans = ""
                async for response in self.handle_text_response(query):
                    response_ans += response
                
                task.result = response_ans
                
                await MainTaskQueue.submit_task(
                    task_id=task.task_id,
                    status=TaskStatus.COMPLETED,
                    status_message=response_ans
                )
                logger.info("Completed TextResponseTask with response: %s", response_ans)
                
    async def handle_text_response(self, query: str) -> AsyncGenerator[str, None]:
        """
        Handles a text response task by processing the input query through the Cortex model and yielding the generated response tokens. \n
        **Input**: \n
        - `query`: The input text query that needs to be processed and responded to. \n
        
        **Yields**: \n
        - Generated response tokens as they are produced by the model, allowing for streaming responses back to the client.
        """

        dummy_response = "Hello bro, I am also fine, how can I help you today?"
        yield dummy_response    
    # async def listen_and_respond(self, audio_bytes: bytes, cancel_event: asyncio.Event | None = None):
    #     return ""    
            
            
         