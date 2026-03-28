import asyncio
import io
import wave

from fastapi import WebSocket
from cortex.voice import VoiceClient
from utility.sensory.config import TTS_CONFIG
from service.stream.event import StreamEvent
    
class StreamClient:
    """
        ### Streaming Service Client \n
        Recieves Audio Data and Control Messages from Websocket Endpoint, and streams back the processed Audio response from the AI Application into Websocket. \n
        
        **Key Features:** \n
        - Talks directly with the `Voice Client` for processing the audio data and generating responses
        - Manages the state of the conversation and streaming through the `StreamEvent` class.
    """
    
    def __init__(self, websocket: WebSocket, streamEvent: StreamEvent):
        self.websocket = websocket
        self.streamEvent = streamEvent
        self.voiceClient = VoiceClient()
        
    async def _send_json(self, payload: dict):
        """Helper function to send JSON responses through the WebSocket connection in a thread-safe manner."""
        async with self.streamEvent.getLock():
            await self.websocket.send_json(payload)
            
    async def _send_bytes(self, payload: bytes):
        """Helper function to send binary audio data over the websocket with proper locking."""
        async with self.streamEvent.getLock():
            await self.websocket.send_bytes(payload)
            
    def pcm16le_to_wav_bytes(self, pcm_bytes: bytes) -> bytes:
        """
        **Convert raw `PCM 16-bit Audio bytes` to `WAV format bytes` in-memory.** \n
        This is necessary because STT model expects WAV format for transcription, but the audio data is collected in raw PCM format for streaming efficiency.
        """
        
        channels = TTS_CONFIG["channels"]
        sample_rate = TTS_CONFIG["sample_rate"]
        
        with io.BytesIO() as wav_buffer:
            with wave.open(wav_buffer, "wb") as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(pcm_bytes)
            return wav_buffer.getvalue()

    async def stream_response(self):
        """
        **Process the complete audio buffer through the Cortex model and stream back TTS audio chunks in real-time.** \n
        """
        try:
            wav_bytes = self.pcm16le_to_wav_bytes(self.streamEvent.getAudioBufferBytes())
            await self._send_json(
                {
                    "type": "audio_meta",
                    "sampleRate": TTS_CONFIG["sample_rate"],
                    "channels": TTS_CONFIG["channels"],
                    "format": TTS_CONFIG["format"],
                }
            )
            
            async for audio_chunk in self.voiceClient.listen_and_respond(wav_bytes, cancel_event=self.streamEvent.response_cancel_event):
                if self.streamEvent.isCancelEventSet():
                    print("Response streaming stopped by cancel event")
                    return
                await self._send_bytes(audio_chunk.tobytes())

            if not self.streamEvent.isCancelEventSet():
                await self._send_json({"type": "done"})
        except asyncio.CancelledError:
            print("Response task cancelled")
            raise
        except Exception as e:
            print("Response streaming error:", e)
            await self._send_json({"type": "error", "message": str(e)})