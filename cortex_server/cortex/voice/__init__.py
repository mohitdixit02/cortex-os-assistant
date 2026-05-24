import asyncio
from cortex_server.cortex.sensory.STT import STTClient
from cortex_server.cortex.sensory.TTS import TTSClient
from cortex_server.cortex.voice.model import VoiceMainModel, EmotionDetectionModel
from cortex_cm.utility.main import iterate_tokens_async
from typing import AsyncGenerator, Optional, Any
from cortex_cm.utility.logger import get_logger
from .req import add_voice_task, save_casual_response
from .utility import generate_audio_stream
from cortex_cm.pg import TaskOwner
from fastapi import WebSocket
from service.stream.event import StreamEvent
from cortex_cm.utility.sensory.config import STT_CONFIG, TTS_CONFIG
import re
from contextlib import nullcontext
from langsmith.run_helpers import tracing_context

from cortex_server.service.stream.state_manager import voice_state_manager

class VoiceClient:
    """
        ### Cortex Voice Client \n
        Main interface for handling the voice processing pipeline, including STT transcription, interaction with the Cortex Models, and TTS generation. \n
        
        **`__init__()`** requires:
        - The current `StreamEvent object` for handling streaming events.
        - The `user_id` for state management.
        
        **Key Features:** \n
        - Manages the end-to-end flow of audio input to audio response using `STT Client` and `TTS Client`.
        - Interacts with the `VoiceMainModel` and `CortexMainModel` to generate context-aware responses.
    """
    
    def __init__(
        self, 
        streamEvent: StreamEvent,
        user_id: str | None = None
    ):
        self.streamEvent = streamEvent
        self.user_id = user_id
        self.stt_client = STTClient()
        self.tts_client = TTSClient()
        self.model = VoiceMainModel()
        self.emotion_model = EmotionDetectionModel()
        self.logger = get_logger("CORTEX_VOICE")

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
    
    async def transcribe_audio(self, audio_bytes: bytes) -> tuple[str, str]:
        """Transcribes audio bytes using the internal STT client."""
        return await self.stt_client.transcribe(audio_bytes)

    async def get_tts_stream(self, text: str) -> AsyncGenerator[bytes, None]:
        """Gets TTS audio stream using the internal TTS client."""
        async for chunk in self.tts_client.get_audio_stream(text):
            yield chunk

    async def stream_audio(
        self,
        input_data: str | Any,
        cancel_event: asyncio.Event | None = None
    ) -> AsyncGenerator[bytes, None]:
        """
        Unified utility function to stream audio chunks.
        Accepts either a plain string or a tokens_callback for streaming.
        """
        async for chunk in generate_audio_stream(
            input_data=input_data,
            tts_client=self.tts_client,
            stream_event=self.streamEvent,
            logger=self.logger,
            cancel_event=cancel_event
        ):
            yield chunk
            
    async def _submit_voice_task(
        self,
        query: str,
        emotion: str,
        task_name: str,
        task_description: str,
        user_id: str | None = None,
        session_id: str | None = None,
        voice_client_response: str = "",
        original_query: str | None = None,
        is_refined_query: bool = False,
        run_in_background: bool = True
    ):
        """Common helper to submit a task to the queue, optionally in the background."""
        
        async def _submission_task():
            try:
                return await add_voice_task(
                    query=query,
                    emotion=emotion,
                    task_name=task_name,
                    task_description=task_description,
                    user_id=user_id,
                    session_id=session_id,
                    voice_client_response=voice_client_response,
                    original_query=original_query,
                    is_refined_query=is_refined_query
                )
            except Exception as task_exc:
                self.logger.exception("Failed to submit background voice task: %s", task_exc)

        if run_in_background:
            asyncio.create_task(_submission_task())
        else:
            return await _submission_task()

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
            
            response_text = ""
            if route_res.request_type == "casual":
                self.streamEvent.is_depth = False
                # immediate casual response
                response_text = self.model.stream_text_tokens(query)
                print("Is search query:", route_res.search_required)
                print("Casual response:", response_text)

                # Save casual conversation to DB
                asyncio.create_task(save_casual_response(
                    query=query,
                    user_id=user_id,
                    session_id=session_id,
                    voice_client_response=response_text,
                    original_query=original_query,
                    is_refined_query=is_refined_query
                ))
            else:
                self.streamEvent.is_depth = True
                emotion = self.emotion_model.get_emotion(query)
                response_text = self.model.stream_fallback_response(query)
                
                if submit_task:
                    await self._submit_voice_task(
                        query=query,
                        emotion=emotion.get("label", "neutral"),
                        task_name=route_res.task_name,
                        task_description=route_res.task_description,
                        user_id=user_id,
                        session_id=session_id,
                        voice_client_response=response_text,
                        original_query=original_query,
                        is_refined_query=is_refined_query,
                        run_in_background=True
                    )

                print("Fallback response:", response_text)

            async for audio_chunk in self.stream_audio(
                input_data=response_text,
                cancel_event=cancel_event,
            ):
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
            query, detected_lang = await self.transcribe_audio(audio_bytes)
            self.logger.info("Detected Language: %s", detected_lang)
            if not query:
                return

            if detected_lang and detected_lang != "en":
                self.logger.info("Non-English language detected (%s), sending fallback response.", detected_lang)
                async for chunk in self.get_tts_stream("Sorry! I can't understand what you said"):
                    yield chunk
                return

            async for chunk in self.respond_to_text(
                query=query,
                submit_task=submit_task,
                user_id=user_id,
                session_id=session_id
            ):
                yield chunk

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
        
        await self._submit_voice_task(
            query=query,
            emotion=emotion.get("label", "neutral"),
            task_name=route_res.task_name,
            task_description=route_res.task_description,
            user_id=self.user_id,
            session_id=self.streamEvent.session_id if self.streamEvent else None,
            voice_client_response=casual_response,
            run_in_background=False
        )
        
        tokens = re.split(r'(\s+)', casual_response)
        for token in tokens:
            yield token
