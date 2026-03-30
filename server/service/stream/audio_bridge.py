import io
import wave
import asyncio
from utility.sensory.config import STT_CONFIG, TTS_CONFIG
from service.stream.event import StreamEvent
from fastapi import WebSocket
from typing import AsyncGenerator
from logger import logger

class AudioStreamBridge:
    """
    ### Audio Stream Bridge \n
    This class serves as a bridge for streaming audio data between the Websocket endpoint and the application.
    
    **`__init__()`** requires:
    - The current `Websocket object` on which AudioStreamBridge will send responses back to the client.
    - The corresponding `StreamEvent object` for handling streaming events.
    """
    
    def __init__(self, websocket: WebSocket, streamEvent: StreamEvent):
        self.websocket = websocket
        self.streamEvent = streamEvent
        self._stream_lock = asyncio.Lock()
    
    async def send_json(self, payload: dict):
        """Helper function to send JSON responses through the WebSocket connection in a thread-safe manner."""
        async with self.streamEvent.getLock():
            # logger.info("[JSON RES TEST] Sending JSON response through WebSocket: %s", payload)
            await self.websocket.send_json(payload)
            
    async def send_bytes(self, payload: bytes):
        """Helper function to send binary audio data over the websocket with proper locking."""
        async with self.streamEvent.getLock():
            await self.websocket.send_bytes(payload)
    
    def pcm16le_to_wav_bytes(self, pcm_bytes: bytes) -> bytes:
        """
        **Convert raw `PCM 16-bit Audio bytes` to `WAV format bytes` in-memory.** \n
        This is necessary because STT model expects WAV format for transcription, but the audio data is collected in raw PCM format for streaming efficiency.
        """
        
        channels = STT_CONFIG["channels"]
        sample_rate = STT_CONFIG["sample_rate"]
        
        with io.BytesIO() as wav_buffer:
            with wave.open(wav_buffer, "wb") as wav_file:
                wav_file.setnchannels(channels)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(pcm_bytes)
            return wav_buffer.getvalue()
        
    async def stream_audio_websocket(
        self, 
        audio_chunk_generator: AsyncGenerator[bytes, None],
        *args, **kwargs
    ):
        """
        ### Stream Audio to Client through WebSocket \n
        This function sends the audio data in chunks to the client and automatically handles sending metadata about the audio stream (like sample rate and format) before sending the actual audio bytes.
        """
        logger.info("[Audio Bridge] Starting audio streaming to client through WebSocket...")
        logger.info("[Audio Bridge] Audio chunk generator provided: %s", audio_chunk_generator)
        logger.info("[Audio Bridge] StreamEvent response cancel event status: %s", self.streamEvent.response_cancel_event.is_set() if self.streamEvent.response_cancel_event else "No cancel event")
        logger.info("[Audio Bridge] StreamEvent lock status: %s", "Locked" if self.streamEvent.send_lock.locked() else "Unlocked")
        logger.info("[Audio Bridge] StreamEvent isCancelEventSet: %s", self.streamEvent.isCancelEventSet())
        logger.info("[Audio Bridge] Audio Bridge Stream Lock Status: %s", "Locked" if self._stream_lock.locked() else "Unlocked")

        async with self._stream_lock:
            try:
                await self.send_json(
                    {
                        "type": "audio_meta",
                        "sampleRate": TTS_CONFIG["sample_rate"],
                        "channels": TTS_CONFIG["channels"],
                        "format": TTS_CONFIG["format"],
                    }
                )

                async for audio_chunk in audio_chunk_generator(*args, **kwargs):
                    if self.streamEvent.isCancelEventSet():
                        print("Response streaming stopped by cancel event")
                        return

                    if isinstance(audio_chunk, (bytes, bytearray, memoryview)):
                        payload = bytes(audio_chunk)
                    elif hasattr(audio_chunk, "tobytes"):
                        payload = audio_chunk.tobytes()
                    else:
                        raise TypeError(f"Unsupported audio chunk type: {type(audio_chunk)!r}")

                    await self.send_bytes(payload)
                    # await self.send_json({
                    #     "source": audio_chunk_generator.__name__,
                    #     "info": audio_chunk_generator.__doc__[0:10],
                    #     "type": "audio_chunk",
                    #     "size": len(payload)
                    # })

                logger.info("[Audio Bridge] Audio streaming completed successfully: %s", audio_chunk_generator.__name__)
                if not self.streamEvent.isCancelEventSet():
                    await self.send_json({"type": "done"})
                else:
                    print("Audio streaming completed but cancel event was set, not sending done signal")
            except asyncio.CancelledError:
                print("Response task cancelled")
                raise
            except Exception as e:
                print("Response streaming error:", e)
                await self.send_json({"type": "error", "message": str(e)})
                return {"status": "error", "message": str(e)}

            return {"status": "completed", "message": "Audio streaming completed successfully."}
