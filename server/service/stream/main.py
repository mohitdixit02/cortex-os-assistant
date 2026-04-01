import asyncio
import io
import wave

from fastapi import WebSocket
from cortex.voice import VoiceClient
from cortex.main import MainClient
from utility.sensory.config import STT_CONFIG, TTS_CONFIG
from service.stream.event import StreamEvent
from service.stream.audio_bridge import AudioStreamBridge
    
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
    
    _main_listener_task: asyncio.Task | None = None

    def __init__(self, websocket: WebSocket, streamEvent: StreamEvent):
        self.streamEvent = streamEvent
        self.audioBridge = AudioStreamBridge(websocket=websocket, streamEvent=streamEvent)
        self.voiceClient = VoiceClient(audioBridge=self.audioBridge, streamEvent=streamEvent)
        self._auto_stream_task = asyncio.create_task(self.voiceClient.run_auto_task_stream())

        # Global producer worker should run only once for the process.
        if StreamClient._main_listener_task is None or StreamClient._main_listener_task.done():
            self._main_client = MainClient()
            StreamClient._main_listener_task = asyncio.create_task(self._main_client.listen_task_queue())
        
    async def stream_response(self, audio_bytes: bytes):
        """
        **Process the complete audio buffer through the Cortex model and stream back TTS audio chunks in real-time.** \n
        """
        try:
            wav_bytes = self.audioBridge.pcm16le_to_wav_bytes(audio_bytes)
            # await self.voiceClient.listen_and_respond(audio_bytes=wav_bytes)
            await self.audioBridge.stream_audio_websocket(
                audio_chunk_generator=self.voiceClient.listen_and_respond,
                audio_bytes=wav_bytes
            )
        except asyncio.CancelledError:
            print("Response task cancelled")
            raise
        except Exception as e:
            print("Response streaming error:", e)
            await self.audioBridge.send_json({"type": "error", "message": str(e)})

    async def shutdown(self) -> None:
        """Per-connection cleanup hook."""
        if self._auto_stream_task and not self._auto_stream_task.done():
            self._auto_stream_task.cancel()
            try:
                await self._auto_stream_task
            except asyncio.CancelledError:
                pass
            
    # Dummy Flow Test
    async def read_flow(self, query: str):
        async for token in self.voiceClient.read_and_respond(query):
            yield token