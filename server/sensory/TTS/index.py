import os
from dotenv import load_dotenv

load_dotenv()
cache_dir = os.getenv("HF_CACHE_DIR", "./hf_cache")
os.environ['HF_HOME'] = cache_dir
os.environ['TRANSFORMERS_CACHE'] = cache_dir
os.environ['HF_DATASETS_CACHE'] = cache_dir
os.environ["SENTENCE_TRANSFORMERS_HOME"] = cache_dir
os.makedirs(cache_dir, exist_ok=True)

import asyncio
import threading

import numpy as np
import sounddevice as sd

from kokoro import KPipeline

VOICE = "af_heart"
SAMPLE_RATE = 24000

_pipeline = KPipeline(lang_code="a")
_state_lock = asyncio.Lock()
_stream_lock = threading.Lock()
_current_task = None
_current_stop_flag = None
_current_stream = None


def _play_blocking(text: str, voice: str, stop_flag: threading.Event) -> None:
    """Blocking playback path executed in a worker thread."""
    global _current_stream
    stream = sd.OutputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32")

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


async def stop_speaking() -> None:
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


async def speak_interruptible(text: str, voice: str = VOICE) -> None:
    """Interrupt current speech (if any) and speak new text."""
    global _current_task, _current_stop_flag

    await stop_speaking()
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


async def play_text(text: str, voice: str = VOICE) -> None:
    """Simple one-shot playback."""
    await speak_interruptible(text, voice=voice)


async def demo_interrupt(interrupt_after: float | None = None) -> None:
    """Example: start speaking, then interrupt after 1.5 seconds."""
    long_text = (
        "Hello, this is a long response to demonstrate interruption. "
        "If you call interrupt while this is playing, speech should stop immediately."
    )
    speaking_task = asyncio.create_task(speak_interruptible(long_text, VOICE))
    if interrupt_after is not None:
        await asyncio.sleep(interrupt_after)
        await stop_speaking()

    await speaking_task


if __name__ == "__main__":
    # asyncio.run(play_text("Hello, Kokoro speech is now playing through your system speaker."))
    asyncio.run(demo_interrupt(interrupt_after=1.5))


