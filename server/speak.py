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

VOICE = "en-IN-NeerjaNeural"
_current_proc = None
_speak_lock = asyncio.Lock()


async def _terminate_proc(proc: asyncio.subprocess.Process, timeout: float = 1.5) -> None:
    if proc.returncode is not None:
        return

    proc.terminate()
    try:
        await asyncio.wait_for(proc.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()


async def stop_speaking() -> None:
    global _current_proc
    async with _speak_lock:
        proc = _current_proc
        _current_proc = None

    if proc is not None:
        await _terminate_proc(proc)


async def speak_interruptible(text: str, voice: str = VOICE) -> None:
    """Interrupt current speech (if any) and speak new text."""
    global _current_proc

    await stop_speaking()

    proc = await asyncio.create_subprocess_exec(
        "edge-playback",
        "--voice", voice,
        "--text", text,
    )

    async with _speak_lock:
        _current_proc = proc

    try:
        await proc.wait()
    finally:
        async with _speak_lock:
            if _current_proc is proc:
                _current_proc = None


async def speak(text: str) -> None:
    # Backward-compatible name.
    await speak_interruptible(text)


if __name__ == "__main__":
    asyncio.run(speak("Hello, I can speak directly to your speaker without saving a file."))

# en-IN-NeerjaNeural 
# en-IN-NeerjaExpressiveNeural
# en-IN-PrabhatNeural 
# hi-IN-SwaraNeural
# hi-IN-MadhurNeural 

