import asyncio
from fastapi import WebSocket
from cortex.voice import VoiceClient
from service.stream.event import StreamEvent, ResponseKey, StreamEventResponse
from service.stream.audio_bridge import AudioStreamBridge
from cortex_server.service.config_service import config_service
from uuid import UUID
from cortex_queue.dto import TaskItem, TaskStatus
from .state_manager import voice_state_manager

class StreamClient:
    """
        ## Streaming Service Client \n
        **Main Interface for Websocket Stream Endpoint** \n
        Recieves Audio Data and Control Messages from Websocket Endpoint, and streams back the processed Audio response from the AI Application into Websocket. \n
        
        **Key Features:** \n
        - Uses `Voice Client` for processing the audio data and generating responses
        - Manages the state of the conversation and streaming through the `StreamEvent` class.
        - Stream Back responses using `AudioStreamBridge`.
        
        **`__init__()`** requires:
        - The current `Websocket object` on which StreamClient will send responses back to the client.
        - The corresponding `StreamEvent object` for handling streaming events.
    """

    def __init__(self, websocket: WebSocket, streamEvent: StreamEvent, user_id: str | None = None):
        self.websocket = websocket
        self.streamEvent = streamEvent
        self.user_id = user_id
        self.audioBridge = AudioStreamBridge(websocket=websocket, streamEvent=streamEvent, user_id=user_id)
        self.voiceClient = VoiceClient(streamEvent=streamEvent, user_id=user_id)

    async def stream_response(self, audio_bytes: bytes):
        """
        **Process audio buffer with conversation gap handling.**
        Transcribes audio, evaluates if the thought is complete, and either waits for more audio or responds.
        """
        try:
            wav_bytes = self.audioBridge.pcm16le_to_wav_bytes(audio_bytes)
            
            # Transcribe the current segment
            transcription_task = asyncio.create_task(self.voiceClient.transcribe_audio(wav_bytes))
            try:
                query_segment, detected_lang = await asyncio.shield(transcription_task)
                if detected_lang:
                    self.streamEvent.detected_language = detected_lang
                print(f"Segment Detected Language: {detected_lang}")
            except asyncio.CancelledError:
                # If cancelled during transcription, wait for it to finish and append to buffer
                print("Transcription interrupted, waiting to preserve result...")
                query_segment, detected_lang = await transcription_task
                if detected_lang:
                    self.streamEvent.detected_language = detected_lang
                if query_segment:
                    self.streamEvent.appendTranscribedBuffer(query_segment)
                    print(f"Interrupted transcription preserved: {query_segment}")
                raise

            if not query_segment:
                return
            
            # Append buffer - if not interrupted
            self.streamEvent.appendTranscribedBuffer(query_segment)
            combined_text = self.streamEvent.getTranscribedText()
            print(f"Combined transcribed text: {combined_text}")
            
            # Evaluate gap confidence
            query_completion_res = await self.voiceClient.evaluate_query_completion(combined_text)
            print(f"Confidence: {query_completion_res.confidence}, is_complete: {query_completion_res.is_complete}")
            print(f"Reasoning: {query_completion_res.reasoning}")
            print(f"Refined query after gap evaluation: {query_completion_res.refined_query}")
            
            stream_event_response = StreamEventResponse(
                websocket=self.websocket,
                streamEvent=self.streamEvent
            )

            # Check if complete or if vc should wait
            if not query_completion_res.is_complete and query_completion_res.confidence < 0.8:
                # Get user config for timeout (prioritizes Redis)
                timeout = 3.0 # Default fallback
                if self.user_id:
                    try:
                        timeout = config_service.get_voice_client_timeout(UUID(self.user_id))
                    except Exception as e:
                        print(f"Error fetching voice client timeout, using default: {e}")

                print(f"Thought incomplete, waiting for {timeout}s...")
                try:
                    await asyncio.sleep(timeout)
                    print("Timeout reached, proceeding with response.")
                except asyncio.CancelledError:
                    print("Interrupted by new user speech, preserved buffer for next turn.")
                    raise

            # Either complete, or VC timed out waiting
            print("Finalizing listening and starting response...")
            await stream_event_response.send_response(ResponseKey.FINISH_LISTENING)
            
            # Fallback for non-English language
            if self.streamEvent.detected_language and self.streamEvent.detected_language != "en":
                print(f"Non-English language detected ({self.streamEvent.detected_language}), sending fallback response.")
                self.streamEvent.resetTranscribedBuffer()
                await self.audioBridge.stream_audio_websocket(
                    audio_chunk_generator=self.voiceClient.get_tts_stream,
                    text="Sorry! I can't understand what you said"
                )
                return

            final_query = query_completion_res.refined_query
            is_refined = query_completion_res.is_refined
            self.streamEvent.resetTranscribedBuffer()
            
            await self.audioBridge.stream_audio_websocket(
                audio_chunk_generator=self.voiceClient.respond_to_text,
                query=final_query,
                original_query=combined_text,
                is_refined_query=is_refined,
                user_id=self.streamEvent.user_id,
                session_id=self.streamEvent.session_id
            )

        except asyncio.CancelledError:
            raise
        except Exception as e:
            print("Response streaming error:", e)
            await self.audioBridge.send_json({"type": "error", "message": str(e)})

    async def handle_task_result(self, task_item: TaskItem):
        """
        ### Handles a completed/failed task from the Result Worker.
        Manages concurrency, session validation, and initiates audio streaming if applicable.
        """
        state = voice_state_manager.get_state(self.user_id)
        
        # Wait for Channel Clear (No one is speaking)
        while state.is_user_speaking or state.is_ai_speaking:
            await asyncio.sleep(0.2)

        async with state.stream_lock:
            if not state.audio_socket:
                print(f"Ignoring result for user {self.user_id}: Audio socket missing.")
                return

            task_session_id = task_item.metadata.get("session_id")
            
            # Verify the session ID matches the currently active session
            if task_session_id and self.streamEvent.session_id and str(self.streamEvent.session_id) != str(task_session_id):
                print(f"Ignoring task result {task_item.task_id}: Session mismatch (Task: {task_session_id}, Active: {self.streamEvent.session_id})")
                return

            print(f"Streaming result for task {task_item.task_id} to user {self.user_id}")
            state.is_ai_speaking = True
            
            event_response = StreamEventResponse(
                websocket=state.audio_socket,
                streamEvent=self.streamEvent
            )

            try:
                # Notify UI that a stream is starting
                await event_response.send_response(ResponseKey.AI_AUDIO_STREAM_START)
                
                if task_item.status is TaskStatus.FAILED:
                    print(f"Task {task_item.task_id} failed with error: {task_item.error}")
                elif task_item.status is TaskStatus.COMPLETED:
                    response_text = task_item.result.get("response", "")
                    if not isinstance(response_text, str):
                        response_text = getattr(response_text, "response", str(response_text))
                    
                    await self.audioBridge.stream_audio_websocket(
                        audio_chunk_generator=self.voiceClient.stream_audio,
                        input_data=response_text,
                        cancel_event=asyncio.Event()
                    )
                
                # Notify UI that server finished sending audio
                await event_response.send_response(ResponseKey.AI_AUDIO_STREAM_END)
                
            except Exception as e:
                print(f"Failed to stream task {task_item.task_id}: {e}")
                await self.audioBridge.send_json({"type": "error", "message": str(e)})
            finally:
                state.is_ai_speaking = False

    async def shutdown(self) -> None:
        """Per-connection cleanup hook."""
        pass
            
    # Dummy Flow Test
    async def read_flow(self, query: str):
        async for token in self.voiceClient.read_and_respond(query):
            yield token