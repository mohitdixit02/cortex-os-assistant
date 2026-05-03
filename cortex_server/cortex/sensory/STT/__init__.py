from sensory.STT.model import STTModel
from cortex_cm.utility.sensory.config import STT_CONFIG
from cortex_cm.utility.logger import get_logger
import numpy as np
import asyncio
import time

class STTClient:
    """
    ### Speech-to-Text (STT) Client \n
    Main interface for handling Speech-to-Text transcription \n
    **Key Features:** \n
    - Transcribes raw audio bytes (PCM 16-bit) into text \n
    - Offloads the transcription work to a separate thread for performance effeciency.
    - Handles both short and long audio inputs with configurable chunking and batching strategies to optimize latency.
    """
    def __init__(self):
        self.logger = get_logger("SENSORY")
        self.logger.info("Initializing STTClient with config: %s", STT_CONFIG)
        self.sample_rate = int(STT_CONFIG["sample_rate"])
        self.chunk_size_s = float(STT_CONFIG["chunk_size_s"])
        self.chunk_seconds_max_limit = float(STT_CONFIG["chunk_seconds_max_limit"])
        self.end_speech_silence_threshold = float(STT_CONFIG["end_speech_silence_threshold"])
        self.chunk_batch_size = int(STT_CONFIG.get("chunk_batch_size", 1))
        self.model = STTModel()
        
    def _batch_chunks(self, audio: np.ndarray) -> list:
        """
        ### Batch Audio into Chunks for Transcription \n
        For smaller audio inputs, return a list of single chunk. \n
        If the total audio duration exceeds the `chunk_seconds_max_limit`, split the audio into contiguous chunks of `chunk_size_s` seconds. \n
        
        **Usage**: \n
        - If chunk_batch_size is set to >1, these chunks can be transcribed in batches for improved efficiency. \n
        - If chunk_batch_size is 1, chunks will be transcribed sequentially, but it will help preventing overflow for model window \n
        """
        total_seconds = len(audio) / float(self.sample_rate)
        if total_seconds <= self.chunk_seconds_max_limit:
            return [audio]
        
        chunk_s = self.chunk_size_s
        chunk_n = int(chunk_s * self.sample_rate)
        step_n = max(1, chunk_n)
        chunks = []
        
        for start in range(0, len(audio), step_n):
            end = min(start + chunk_n, len(audio))
            chunk = audio[start:end]
            if len(chunk) < int(self.end_speech_silence_threshold * self.sample_rate):
                break # Too short to transcribe reliably, likely end of speech
            chunks.append(chunk)
            if end >= len(audio):
                break

        return chunks

    # Sync function as involves Audio decoding and model inference, which are both CPU/GPU bound and not natively async-friendly.
    def _transcribe_sync(self, audio_bytes: bytes) -> str:
        """
            Transcribe audio bytes synchronously.
                1. Decode incoming PCM audio bytes to numpy array.
                2. Batch audio into chunks based on configuration for better handling of long audio inputs.
        """
        audio = self.model.decode_wav_bytes(audio_bytes)
        total_seconds = len(audio) / float(self.sample_rate)
        self.logger.info("Transcribing local audio, duration: %.2fs", total_seconds)
        
        start_time = time.time()
        self.logger.info("STT Transcription started at: %s", time.strftime("%H:%M:%S", time.localtime(start_time)))
        
        audio_chunks = self._batch_chunks(audio)
        output = self.model.transcribe_chunks(audio_chunks, batch_size=self.chunk_batch_size)
        final_text = " ".join(output).strip()
        self.logger.info("STT Transcription completed at: %s", time.strftime("%H:%M:%S", time.localtime(time.time())))
        self.logger.info("Total transcription time: %f", time.time() - start_time)
        self.logger.info("Combined Text: %s", final_text)
        return final_text
    
    async def transcribe(self, audio_bytes: bytes) -> str:
        """
            ### Transcribe Audio Bytes to Text Asynchronously
            **Input**: Raw audio bytes - PCM (16-bit) \n
            **Output**: Transcribed text - String \n
            **Key Features**: \n
            - Offloads the transcription work to a separate thread for performance effeciency.
            - Handles both short and long audio inputs with configurable chunking and batching strategies to optimize latency.
        """
        self.logger.info("Transcribing audio bytes size: %d", len(audio_bytes))
        return await asyncio.to_thread(self._transcribe_sync, audio_bytes)