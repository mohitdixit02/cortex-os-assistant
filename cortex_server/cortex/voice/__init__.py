import asyncio
from cortex_server.cortex.sensory.STT import STTClient
from cortex_server.cortex.sensory.TTS import TTSClient
from cortex_server.cortex.voice.model import VoiceMainModel, EmotionDetectionModel
from cortex_server.service.stream.audio_bridge import AudioStreamBridge
from cortex_cm.utility.main import iterate_tokens_async
from nltk.tokenize import sent_tokenize
from typing import AsyncGenerator, Optional
from cortex_cm.utility.logger import get_logger
from cortex_queue.dto import TaskStatus, TaskItem
from .req import add_task as add_task_remote, get_task_result as get_task_result_remote
from cortex_cm.pg import TaskOwner
from fastapi import WebSocket
from service.stream.event import StreamEvent
from cortex_cm.utility.sensory.config import STT_CONFIG, TTS_CONFIG
import re
from contextlib import nullcontext
from langsmith.run_helpers import tracing_context

class MainTaskQueue:
    @staticmethod
    async def add_task(
        payload: any,
        task_name: str,
        task_description: str = "",
        user_id: str | None = None,
        session_id: str | None = None,
        voice_client_response: str = ""
    ):
        resp = await add_task_remote(
            payload=payload,
            task_name=task_name,
            task_description=task_description,
            metadata={
                "user_id": user_id,
                "session_id": session_id,
                "voice_client_response": voice_client_response,
                "task_owner": TaskOwner.VOICE_CLIENT.value
            }
        )
        class TaskWrapper:
            def __init__(self, data):
                self.task_id = str(data.get("task_id"))
                self.status = data.get("status")
        return TaskWrapper(resp)

    @staticmethod
    async def get_task_snapshot(task_id: str):
        data = await get_task_result_remote(task_id)
        if data:
            class TaskSnapshot:
                def __init__(self, d):
                    self.task_id = d.get("task_id")
                    self.status = TaskStatus(d.get("status"))
                    self.result = d.get("result")
                    self.error = d.get("error")
            return TaskSnapshot(data)
        return None

from cortex_server.service.stream.state_manager import voice_state_manager

class VoiceClient:
    """
        ### Cortex Voice Client \n
        Main interface for handling the voice processing pipeline, including STT transcription, interaction with the Cortex Models, and TTS generation. \n
        
        **`__init__()`** requires:
        - The current `AudioStreamBridge object` which VoiceClient will use to send the audio responses back to the client.
        - The corresponding `StreamEvent object` for handling streaming events.
        
        **Key Features:** \n
        - Manages the end-to-end flow of audio input to audio response using `STT Client` and `TTS Client`.
        - Interacts with the `VoiceMainModel` and `CortexMainModel` to generate context-aware responses.
    """
    
    def __init__(
        self, 
        stream_client: any = None
    ):
        self.stream_client = stream_client
        self.stt_client = STTClient()
        self.tts_client = TTSClient()
        self.model = VoiceMainModel()
        self.emotion_model = EmotionDetectionModel()
        self.logger = get_logger("CORTEX_VOICE")

    @property
    def user_id(self):
        return self.stream_client.get_user_id() if self.stream_client else None

    @property
    def audioBridge(self):
        return self.stream_client.get_audio_bridge() if self.stream_client else None

    @property
    def streamEvent(self):
        return self.stream_client.get_stream_event() if self.stream_client else None

    @property
    def user_state(self):
        if not self.user_id:
            return None
        return voice_state_manager.get_state(self.user_id)

    def _no_trace_context(self):
        """Disable LangSmith tracing for this request path."""
        if tracing_context is None:
            return nullcontext()
        return tracing_context(enabled=False)
    
    def _get_stream_ready_text(self, buffer: str) -> tuple[str, str]:
        """
        Determines when the accumulated text buffer has reached a point where it can be sent for TTS generation, based on sentence boundaries. \n
        It uses `NLTK's sentence tokenizer` to identify complete sentences in the buffer. \n
        **Input**: \n
        - `buffer`: The current accumulated text buffer from the token stream. \n
        **Returns**: \n
        - A tuple of <ready_text, remaining_buffer> where:
            - `ready_text`: portion of the buffer that is ready to be sent for TTS
            - `remaining_buffer`: part that should be kept for further accumulation.
        """
        
        if not buffer:
            return "", ""
        stripped = buffer.strip()
        if not stripped:
            return "", ""
        if stripped.endswith((".", "!", "?")):
            return stripped, ""
        sentences = sent_tokenize(stripped)
        if len(sentences) <= 1:
            return "", buffer
        return " ".join(sentences[:-1]), sentences[-1]
    
    async def _stream_tts(self, text: str, cancel_event: asyncio.Event | None = None):
        """
        Helper function to stream TTS audio chunks for a given text segment, with support for cancellation. \n
        """
        if cancel_event is None and self.streamEvent:
            cancel_event = self.streamEvent.response_cancel_event
        async for audio_chunk in self.tts_client.get_audio_stream(text):
            if self.streamEvent and self.streamEvent.isUserSpeaking():
                self.logger.info("Stopping TTS stream because user started speaking")
                return
            if cancel_event and cancel_event.is_set():
                self.logger.info("Cancelling TTS stream due to interruption")
                return
            yield audio_chunk
            
    async def evaluate_query_completion(self, text: str):
        """Evaluates if the current text represents a complete thought and handles query refinement."""
        return self.model.get_conversation_end_confidence(text)

    async def respond_to_text(
        self,
        query: str,
        submit_task: bool = True,
        user_id: str | None = None,
        session_id: str | None = None,
        original_query: str | None = None,
        is_refined_query: bool = False
    ) -> AsyncGenerator[bytes, None]:
        """
        ### Process Transcribed Query and Reply with Audio Stream
        Generates a response for the provided text query and streams back TTS audio chunks.
        """
        with self._no_trace_context():
            self.logger.info("Processing text query for response...")
            cancel_event = self.streamEvent.response_cancel_event if self.streamEvent else None
            
            if not query:
                return

            print("Query to process:", query)
            route_res = self.model.get_response_route(query)
            self.logger.info("Determined route type: %s", route_res.request_type)
            if route_res.request_type == "casual":
                # immediate casual response is not saved in db yet - /pending/
                casual_response = self.model.stream_text_tokens(query)
                print("Is search query:", route_res.search_required)
                print("Casual response:", casual_response)
                tokens = re.split(r'(\s+)', casual_response)
            else:
                emotion = self.emotion_model.get_emotion(query)
                fallback_response = self.model.stream_fallback_response(query)
                task_name = route_res.task_name
                task_description = route_res.task_description
    
                async def _submit_main_task() -> None:
                    try:
                        await MainTaskQueue.add_task(
                            payload={
                                "query": query,
                                "original_query": original_query,
                                "is_refined_query": is_refined_query,
                                "emotion": emotion.get("label", "neutral"),
                            },
                            task_name=task_name,
                            task_description=task_description,
                            user_id=user_id,
                            session_id=session_id,
                            voice_client_response=fallback_response,
                        )
                    except Exception as task_exc:
                        self.logger.exception("Failed to submit background main task: %s", task_exc)

                if submit_task:
                    asyncio.create_task(_submit_main_task())

                print("Fallback response:", fallback_response)
                tokens = re.split(r'(\s+)', fallback_response)

            pending_text = ""
            # Tokens stream from Voice Main Model
            async for token in iterate_tokens_async(
                generator_callback=lambda: tokens,
                cancel_event=cancel_event,
            ):
                if cancel_event and cancel_event.is_set():
                    self.logger.info("Cancelling token stream due to interruption")
                    return
                
                pending_text += token
                segment, pending_text = self._get_stream_ready_text(pending_text)
                
                if segment:
                    async for audio_chunk in self._stream_tts(segment):
                        yield audio_chunk
            
            remaining = pending_text.strip()
            if remaining and not (cancel_event and cancel_event.is_set()):
                async for audio_chunk in self._stream_tts(remaining):
                    yield audio_chunk

    async def listen_and_respond(
        self, 
        audio_bytes: bytes,
        submit_task: bool = True,
        user_id: str | None = None,
        session_id: str | None = None
        ) -> AsyncGenerator[bytes, None]:
        """
        ### Listen and Reply with Audio Stream
        Processes the incoming audio bytes, transcribes them, and generates a immediate fallback response through the model, streaming back TTS audio chunks. \n
        
        **Input**: \n
        - `audio_bytes`: Raw audio bytes (PCM 16-bit) received from the client.
        - `submit_task`: Whether to submit the transcribed query as a task to the TaskQueue for further processing. Default is True. \n
        
        **Yields**: \n
        - PCM audio chunks as numpy arrays of shape (frame_samples,) and dtype float32
        
        **Note**: \n
        If `submit_task` is False, reply will be generated by `VoiceMainModel`. However, if it is True, task submission is not gurranted and this behaviour will be decided based on the user query.
        """
        with self._no_trace_context():
            self.logger.info("Starting Cortex Main Server...")
            query = await self.stt_client.transcribe(audio_bytes)
            if not query:
                return

            async for chunk in self.respond_to_text(
                query=query,
                submit_task=submit_task,
                user_id=user_id,
                session_id=session_id
            ):
                yield chunk
    
    async def _stream_audio_queue_response(self, taskItem: TaskItem) -> None:
        """
        ### Streams Audio Response for a Completed Task \n
        This function takes the text response from a completed task item in the `TaskQueue` and uses `AudioBridge` to send audio stream directly to the client websocket. \n
        
        **Input**: \n
        - `taskItem`: The completed TaskItem from the TaskQueue \n
        """
        if taskItem.result["response_type"] != "text_stream":
            self.logger.warning("Unsupported response type in task result: %s", taskItem.result["response_type"])
            return

        if self.audioBridge is None:
            self.logger.warning("Audio bridge is missing; cannot stream queue response")
            return

        # Queue playback must not depend on response_task cancel event lifecycle.
        queue_cancel_event = asyncio.Event()
        response_text = taskItem.result.get("response", "")
        if not isinstance(response_text, str):
            response_text = getattr(response_text, "response", str(response_text))
        response_tokens = re.split(r'(\s+)', response_text)

        async def _generator():
            pending_text = ""
            async for token in iterate_tokens_async(
                generator_callback=lambda: response_tokens,
                cancel_event=queue_cancel_event,
            ):
                if self.streamEvent and self.streamEvent.isUserSpeaking():
                    self.logger.info("Stopping queue token stream because user started speaking")
                    return
                if queue_cancel_event.is_set():
                    self.logger.info("Cancelling token stream due to interruption")
                    return

                pending_text += token
                segment, pending_text = self._get_stream_ready_text(pending_text)

                if segment:
                    self.logger.info("Streaming audio for segment: %s", segment)
                    async for audio_chunk in self._stream_tts(segment, cancel_event=queue_cancel_event):
                        yield audio_chunk

            remaining = pending_text.strip()
            if remaining and not queue_cancel_event.is_set():
                async for audio_chunk in self._stream_tts(remaining, cancel_event=queue_cancel_event):
                    yield audio_chunk

        await self.audioBridge.stream_audio_websocket(audio_chunk_generator=_generator)

    # Will be used later for text based queries from UI
    async def read_and_respond(self, query: str) -> AsyncGenerator[str, None]:
        """
        ### Takes Text as Input and yields Text \n
        Main function to handle the flow of processing an input text query, generating a response through the model, and yielding the response text tokens as they are generated. \n
                
        **Input**: \n
        - `query`: The input text query for which to generate a response. \n
        
        **Yields**: \n
        - The final response text generated by the model after processing the transcribed input.
        """
        self.logger.info("Starting Cortex Main Server for text response...")
        
        # emotion =self.emotion_model.get_emotion(query)
        emotion = {"label": "neutral", "confidence": 0.99}
        
        route_res = self.model.get_response_route(query)
        
        casual_response = "Ok sure, I will look into that for you."
        task_name = route_res.task_name
        task_description = route_res.task_description
        task_item = await MainTaskQueue.add_task(
            payload={
                "query": query,
                "emotion": emotion.get("label", "neutral")
            },
            task_name=task_name,
            task_description=task_description,
            user_id=self.user_id,
            session_id=self.streamEvent.session_id if self.streamEvent else None,
            voice_client_response=casual_response
        )
        tokens = re.split(r'(\s+)', casual_response)
        for token in tokens:
            yield token

    async def _handle_task_queue(self, taskItem: TaskItem, cancel_event: asyncio.Event | None = None) -> None:
        """**Handles tasks retrieved from the `TaskQueue`.**\n
        It processes the task item received from the Task Queue based on the paramaters (like paylaod or taskname)\n
        """
        self.logger.info("task name: %s", taskItem.task_name)
        self.logger.info("task status: %s", taskItem.status)
        self.logger.info("task payload: %s", taskItem.result)
        try:
            if taskItem.status is TaskStatus.FAILED:
                self.logger.error("Task %s failed with error: %s", taskItem.task_id, taskItem.error)
                return
            if taskItem.status is TaskStatus.COMPLETED:
                self.logger.info("Task %s completed with result: %s", taskItem.task_id, taskItem.result)
                await self._stream_audio_queue_response(taskItem)
                return
                # if taskItem.result and taskItem.result.get("response_type") == "text_stream":
                #     await self._stream_audio_queue_response(taskItem)
                #     return
                # else:
                #     self.logger.warning("Task %s has unsupported or missing response type in result: %s", taskItem.task_id, taskItem.result)
                #     return
            self.logger.warning("Task %s is in unexpected status: %s", taskItem.task_id, taskItem.status)
        except Exception as e:
            self.logger.exception("Error handling task %s: %s", taskItem.task_id, e)
