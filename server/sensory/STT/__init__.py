from sensory.STT.model import STTModel
from utility.sensory.config import STT_CONFIG
from logger import logger
import asyncio

class STTClient:
    def __init__(self):
        logger.info("Initializing STTClient with config: %s", STT_CONFIG)
        self.sample_rate = int(STT_CONFIG["sample_rate"])
        self.chunk_size_s = float(STT_CONFIG["chunk_size_s"])
        self.overlap_s = float(STT_CONFIG["overlap_s"])
        self.chunk_seconds_max_limit = float(STT_CONFIG["chunk_seconds_max_limit"])
        self.end_speech_silence_threshold = float(STT_CONFIG["end_speech_silence_threshold"])
        self.chunk_batch_size = int(STT_CONFIG.get("chunk_batch_size", 1))
        self.model = STTModel()
        logger.info("STT model loaded locally...")

    # Sync function as involves Audio decoding and model inference, which are both CPU/GPU bound and not natively async-friendly.
    def _transcribe_sync(self, audio_bytes: bytes) -> str:
        """
            Transcribe audio bytes synchronously.
                1. Decode incoming PCM audio bytes to numpy array.
                2. If audio is short (<=30s), transcribe in one pass.
                3. If audio is long (>30s), perform manual chunking with overlap and transcribe each chunk sequentially.
        """
        audio = self.model.decode_wav_bytes(audio_bytes)
        total_seconds = len(audio) / float(self.sample_rate)
        logger.info("Transcribing local audio, duration: %.2fs", total_seconds)

        # Single pass if shorter audio
        if total_seconds <= self.chunk_seconds_max_limit:
            print("Audio duration within single pass limit, transcribing in one go...")
            return self.model.transcribe_chunk(audio)

        # Fallback for longer audio: manual chunking (no pipeline chunk_length_s warning path)
        chunk_s = self.chunk_size_s
        overlap_s = self.overlap_s
        chunk_n = int(chunk_s * self.sample_rate)
        overlap_n = int(overlap_s * self.sample_rate)
        step_n = max(1, chunk_n - overlap_n)

        parts = []
        chunks = []
        for start in range(0, len(audio), step_n):
            end = min(start + chunk_n, len(audio))
            chunk = audio[start:end]
            if len(chunk) < int(self.end_speech_silence_threshold * self.sample_rate):
                break # Too short to transcribe reliably, likely end of speech
            chunks.append(chunk)
            if end >= len(audio):
                break

        if not chunks:
            return ""

        if self.chunk_batch_size > 1:
            texts = self.model.transcribe_chunks_batched(chunks, batch_size=self.chunk_batch_size)
            parts.extend([t for t in texts if t])
        else:
            for chunk in chunks:
                txt = self.model.transcribe_chunk(chunk)
                if txt:
                    print("Transcribed chunk text if higher Length:", txt)
                    parts.append(txt)

        return " ".join(parts).strip()
    
    async def transcribe(self, audio_bytes: bytes) -> str:
        """
            ***Transcribe Audio Bytes to Text Asynchronously*** \n
            Offloads the CPU/GPU-bound transcription work to a separate thread \n
            **Input**: Raw audio bytes - PCM (16-bit) \n
            **Output**: Transcribed text - String
        """
        logger.info("Transcribing audio bytes size: %d", len(audio_bytes))
        return await asyncio.to_thread(self._transcribe_sync, audio_bytes)