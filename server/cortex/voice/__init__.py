import asyncio
from sensory.STT import STTClient
from sensory.TTS import TTSClient
from cortex.voice.model import VoiceMainModel
from logger import logger
# keep listening and processing until the program is terminated

class VoiceClient:
    """
        ### Cortex Voice Client \n
        Main interface for handling the voice processing pipeline, including STT transcription, interaction with the Cortex Models, and TTS generation. \n
        
        **Key Features:** \n
        - Manages the end-to-end flow of audio input to audio response using `STT Client` and `TTS Client`.
        - Interacts with the `VoiceMainModel` and `CortexMainModel` to generate context-aware responses.
    """
    
    def __init__(self):
        self.stt_client = STTClient()
        self.tts_client = TTSClient()
        self.model = VoiceMainModel()

    async def iter_model_tokens_async(self, query: str, cancel_event: asyncio.Event | None = None):
        loop = asyncio.get_running_loop()
        queue: asyncio.Queue = asyncio.Queue(maxsize=32)
        stream_done = object()

        def producer():
            try:
                for token in self.model.stream_text_tokens(query=query):
                    if cancel_event and cancel_event.is_set():
                        break
                    fut = asyncio.run_coroutine_threadsafe(queue.put(token), loop)
                    fut.result()
            except Exception as exc:
                fut = asyncio.run_coroutine_threadsafe(queue.put(exc), loop)
                fut.result()
            finally:
                fut = asyncio.run_coroutine_threadsafe(queue.put(stream_done), loop)
                fut.result()

        producer_task = asyncio.create_task(asyncio.to_thread(producer))
        try:
            while True:
                item = await queue.get()
                if item is stream_done:
                    break
                if isinstance(item, Exception):
                    raise item
                yield item
        finally:
            if cancel_event:
                cancel_event.set()
            await producer_task


    async def listen_and_respond(self, audio_bytes: bytes, cancel_event: asyncio.Event | None = None):
        logger.info("Starting Cortex Main Server...")
            
        text = await self.stt_client.transcribe(audio_bytes)
        if not text:
            return

        print("Transcribed Text:", text)
        pending_text = ""

        def should_flush(buffer: str) -> bool:
            if not buffer:
                return False
            stripped = buffer.strip()
            if not stripped:
                return False
            if stripped.endswith((".", "!", "?", "\n")):
                return True
            return len(stripped) >= 80

        async for token in self.iter_model_tokens_async(query=text, cancel_event=cancel_event):
            if cancel_event and cancel_event.is_set():
                logger.info("Cancelling token stream due to interruption")
                return

            pending_text += token

            if should_flush(pending_text):
                segment = pending_text.strip()
                pending_text = ""
                if segment:
                    async for audio_chunk in self.tts_client.get_audio_stream(segment):
                        if cancel_event and cancel_event.is_set():
                            logger.info("Cancelling audio stream due to interruption")
                            return
                        yield audio_chunk

        remaining = pending_text.strip()
        if remaining and not (cancel_event and cancel_event.is_set()):
            async for audio_chunk in self.tts_client.get_audio_stream(remaining):
                if cancel_event and cancel_event.is_set():
                    logger.info("Cancelling final audio flush due to interruption")
                    return
                yield audio_chunk

            

            