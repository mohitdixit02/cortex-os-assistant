import asyncio
from sensory.STT import STTClient
from sensory.TTS import TTSClient
from cortex.voice.model import VoiceMainModel
from utility.main import iterate_tokens_async
from nltk.tokenize import sent_tokenize
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
    
    def _get_stream_ready_text(self, buffer: str) -> tuple[str, str]:
        """
        Determines when the accumulated text buffer has reached a point where it can be sent for TTS generation, based on sentence boundaries. \n
        It uses `NLTK's sentence tokenizer` to identify complete sentences in the buffer. \n
        **Input**: \n
        - `buffer`: The current accumulated text buffer from the token stream. \n
        **Returns**: \n
        - A tuple of <ready_text, remaining_buffer> where:
            - `ready_text`: portion of the buffer that is ready to be sent for TTS
            - `remaining_buffer`: part that should be kept for further accumulation.
        """
        
        if not buffer:
            return "", ""
        stripped = buffer.strip()
        if not stripped:
            return "", ""
        if stripped.endswith((".", "!", "?")):
            return stripped, ""
        sentences = sent_tokenize(stripped)
        if len(sentences) <= 1:
            return "", buffer
        return " ".join(sentences[:-1]), sentences[-1]
    
    async def _stream_tts(self, text: str, cancel_event: asyncio.Event | None = None):
        async for audio_chunk in self.tts_client.get_audio_stream(text):
            if cancel_event and cancel_event.is_set():
                logger.info("Cancelling TTS stream due to interruption")
                return
            yield audio_chunk

    async def listen_and_respond(self, audio_bytes: bytes, cancel_event: asyncio.Event | None = None):
        logger.info("Starting Cortex Main Server...")
            
        text = await self.stt_client.transcribe(audio_bytes)
        if not text:
            return

        print("Transcribed Text:", text)
        pending_text = ""

        # Tokens stream from Voice Main Model
        async for token in iterate_tokens_async(
            generator_callback=self.model.stream_text_tokens,
            cancel_event=cancel_event,
            query=text
        ):
            if cancel_event and cancel_event.is_set():
                logger.info("Cancelling token stream due to interruption")
                return

            pending_text += token
            segment, pending_text = self._get_stream_ready_text(pending_text)

            if segment:
                async for audio_chunk in self._stream_tts(segment, cancel_event):
                    yield audio_chunk

        remaining = pending_text.strip()
        if remaining and not (cancel_event and cancel_event.is_set()):
            async for audio_chunk in self._stream_tts(remaining, cancel_event):
                yield audio_chunk
         