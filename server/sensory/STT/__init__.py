import io
import sounddevice as sd
import soundfile as sf
from utility.huggingface.request import HuggingFaceRequest
from utility.sensory.config import STT_CONFIG
from logger import logger

class STTClient:
    def __init__(self):
        logger.info("Initializing STTClient with config: %s", STT_CONFIG)
        self.sample_rate = STT_CONFIG["sample_rate"]
        self.seconds = STT_CONFIG["seconds"]
        self.channels = STT_CONFIG["channels"]
        
    def listen(self) -> str:
        """Record audio from the microphone and return the transcribed text using LLM"""
        
        logger.info("Starting audio recording: %d seconds at %d Hz", self.seconds, self.sample_rate)
        audio = sd.rec(
            int(self.seconds * self.sample_rate),
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
        )
        sd.wait()
        logger.info("Audio recording complete, processing...")

        wav_buffer = io.BytesIO()
        sf.write(wav_buffer, audio.flatten(), self.sample_rate, format='WAV')

        wav_buffer.seek(0) # Reset buffer position
        audio_bytes = wav_buffer.getvalue()
        transcription = self.transcribe(audio_bytes)
        return transcription
        
    def transcribe(self, audio_bytes: bytes) -> str:
        """Send the recorded audio bytes to the Hugging Face model for transcription and return the text."""
        
        logger.info("Transcribing audio data of size: %d bytes", len(audio_bytes))
        result = HuggingFaceRequest(
            feature="stt", 
            data=audio_bytes
        )
        logger.info("Transcription result: %s", result)
        return result.text
