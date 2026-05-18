import asyncio
import io
import wave
import threading

from fastapi import WebSocket
from cortex.voice import VoiceClient
from cortex_cm.utility.sensory.config import STT_CONFIG, TTS_CONFIG
from service.stream.event import StreamEvent, ResponseKey, StreamEventResponse
from service.stream.audio_bridge import AudioStreamBridge
from cortex_server.service.config_service import config_service
from uuid import UUID

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
        self.audioBridge = AudioStreamBridge(stream_client=self)
        self.voiceClient = VoiceClient(stream_client=self)

    def get_audio_bridge(self) -> AudioStreamBridge:
        return self.audioBridge

    def get_stream_event(self) -> StreamEvent:
        return self.streamEvent

    def get_websocket(self) -> WebSocket:
        return self.websocket

    def get_user_id(self) -> str | None:
        return self.user_id

    async def stream_response(self, audio_bytes: bytes):
        """
        **Process audio buffer with conversation gap handling.**
        Transcribes audio, evaluates if the thought is complete, and either waits for more audio or responds.
        """
        try:
            wav_bytes = self.audioBridge.pcm16le_to_wav_bytes(audio_bytes)
            
            # Transcribe the current segment
            transcription_task = asyncio.create_task(self.voiceClient.stt_client.transcribe(wav_bytes))
            try:
                query_segment = await asyncio.shield(transcription_task)
            except asyncio.CancelledError:
                # If cancelled during transcription, wait for it to finish and append to buffer
                print("Transcription interrupted, waiting to preserve result...")
                query_segment = await transcription_task
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
                # Get user config for timeout
                timeout = 3.0 # Default fallback
                if self.user_id:
                    try:
                        # need to change to redis after setup
                        config = config_service.get_user_config(UUID(self.user_id))
                        timeout = config.voice_client_timeout
                    except Exception as e:
                        print(f"Error fetching user config, using default timeout: {e}")

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
            
            final_query = query_completion_res.refined_query
            self.streamEvent.resetTranscribedBuffer()
            
            await self.audioBridge.stream_audio_websocket(
                audio_chunk_generator=self.voiceClient.respond_to_text,
                query=final_query,
                user_id=self.streamEvent.user_id,
                session_id=self.streamEvent.session_id
            )

        except asyncio.CancelledError:
            # Buffer is preserved in streamEvent, so no need to clear it here
            raise
        except Exception as e:
            print("Response streaming error:", e)
            await self.audioBridge.send_json({"type": "error", "message": str(e)})

    async def shutdown(self) -> None:
        """Per-connection cleanup hook."""
        pass
            
    # Dummy Flow Test
    async def read_flow(self, query: str):
        async for token in self.voiceClient.read_and_respond(query):
            yield token