import asyncio
import io
import wave

from fastapi import WebSocket
from cortex.voice import listen_and_respond
from utility.sensory.config import TTS_CONFIG
from service.stream.event import StreamEvent, send_json

async def send_bytes(payload: bytes, websocket: WebSocket, streamEvent: StreamEvent):
    """Helper function to send binary audio data over the websocket with proper locking."""
    async with streamEvent.getLock():
        await websocket.send_bytes(payload)
        
def pcm16le_to_wav_bytes(pcm_bytes: bytes) -> bytes:
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

async def stream_response(streamEvent: StreamEvent, websocket: WebSocket):
    """
    **Process the complete audio buffer through the Cortex model and stream back TTS audio chunks in real-time.** \n
    """
    try:
        wav_bytes = pcm16le_to_wav_bytes(streamEvent.getAudioBufferBytes())
        await send_json(
            {
                "type": "audio_meta",
                "sampleRate": TTS_CONFIG["sample_rate"],
                "channels": TTS_CONFIG["channels"],
                "format": TTS_CONFIG["format"],
            },
            websocket=websocket,
            streamEvent=streamEvent
        )
        
        async for audio_chunk in listen_and_respond(wav_bytes, cancel_event=streamEvent.response_cancel_event):
            if streamEvent.isCancelEventSet():
                print("Response streaming stopped by cancel event")
                return
            await send_bytes(audio_chunk.tobytes(), websocket, streamEvent)

        if not streamEvent.isCancelEventSet():
            await send_json({"type": "done"}, websocket=websocket, streamEvent=streamEvent)
    except asyncio.CancelledError:
        print("Response task cancelled")
        raise
    except Exception as e:
        print("Response streaming error:", e)
        await send_json({"type": "error", "message": str(e)}, websocket=websocket, streamEvent=streamEvent)
