import asyncio
import threading
import numpy as np
import sounddevice as sd
from kokoro import KPipeline
from logger import logger
from utility.sensory.config import TTS_CONFIG

_pipeline = KPipeline(lang_code="a")
_state_lock = asyncio.Lock()
_stream_lock = threading.Lock()
_current_task = None
_current_stop_flag = None
_current_stream = None

class TTSClient:
    def __init__(self):
        logger.info("Initializing TTSClient...")
        self.voice = TTS_CONFIG.get("voice", "af_heart")
        self.sample_rate = TTS_CONFIG.get("sample_rate", 24000)
        self.channels = TTS_CONFIG.get("channels", 1)
        
    def play_blocking(self, text: str, voice: str, stop_flag: threading.Event) -> None:
        """Blocking playback path executed in a worker thread."""
        global _current_stream
        stream = sd.OutputStream(samplerate=self.sample_rate, channels=1, dtype="float32")

        with _stream_lock:
            _current_stream = stream

        stream.start()
        try:
            for _, _, audio in _pipeline(text, voice=voice):
                if stop_flag.is_set():
                    break

                chunk = audio.detach().cpu().numpy().astype(np.float32)
                if chunk.ndim == 1:
                    chunk = chunk.reshape(-1, 1)

                stream.write(chunk)
        finally:
            with _stream_lock:
                if _current_stream is stream:
                    _current_stream = None

            stream.stop()
            stream.close()


    async def stop_speaking(self) -> None:
        """Stop current playback task and audio stream (barge-in)."""
        global _current_task, _current_stop_flag

        async with _state_lock:
            task = _current_task
            stop_flag = _current_stop_flag
            _current_task = None
            _current_stop_flag = None

        if stop_flag is not None:
            stop_flag.set()

        with _stream_lock:
            if _current_stream is not None:
                _current_stream.abort()

        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


    async def play(self, text: str) -> None:
        """Interrupt current speech (if any) and speak new text."""
        global _current_task, _current_stop_flag

        await self.stop_speaking()
        stop_flag = threading.Event()
        task = asyncio.create_task(asyncio.to_thread(_play_blocking, text, voice, stop_flag))

        async with _state_lock:
            _current_task = task
            _current_stop_flag = stop_flag

        try:
            await task
        except asyncio.CancelledError:
            pass
        finally:
            async with _state_lock:
                if _current_task is task:
                    _current_task = None
                    _current_stop_flag = None


    # async def demo_interrupt(interrupt_after: float | None = None) -> None:
    #     """Example: start speaking, then interrupt after 1.5 seconds."""
    #     long_text = (
    #         "Hello, this is a long response to demonstrate interruption. "
    #         "If you call interrupt while this is playing, speech should stop immediately."
    #     )
    #     speaking_task = asyncio.create_task(speak_interruptible(long_text, VOICE))
    #     if interrupt_after is not None:
    #         await asyncio.sleep(interrupt_after)
    #         await stop_speaking()

    #     await speaking_task


# if __name__ == "__main__":  
#     # asyncio.run(play_text("Hello, Kokoro speech is now playing through your system speaker."))
#     asyncio.run(demo_interrupt(interrupt_after=1.5))


