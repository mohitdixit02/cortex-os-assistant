import numpy as np
from kokoro import KPipeline
from utility.logger import get_logger
from utility.sensory.config import TTS_CONFIG
from utility.main import iterate_tokens_async
from utility.models import TTS_PIPELINE

class TTSClient:
    """
        ### TTS Client
        Main interface for handling Text-to-Speech generation\n
        
        `get_audio_stream(text: str)` - Asynchronously generates audio chunks for a given input text \n
        
        **Notes**: \n
        - PCM chunks are generated in a streaming fashing based on the frame_samples configuration to have better control over latency and smooth interruption.     
    """
    def __init__(self):
        self.logger = get_logger("SENSORY")
        self.logger.info("Initializing TTSClient...")
        self.voice = TTS_CONFIG.get("voice", "af_heart")
        self.sample_rate = TTS_CONFIG.get("sample_rate", 24000)
        self.channels = TTS_CONFIG.get("channels", 1)
        self.frame_samples = TTS_CONFIG.get("frame_samples")
        self._pipeline = TTS_PIPELINE
    
    # chunk duration (seconds) = frame_samples / sample_rate
    def _get_audio_stream_sync(self, text: str):
        """
        Generates audio chunks for a given input text \n
        Returns generator yielding PCM audio chunks as numpy arrays of shape (frame_samples,) and dtype float32.
        """
        self.logger.info("Generating audio chunks for text: %s", text)
        for _, _, audio in self._pipeline(text, voice=self.voice):
            pcm = audio.detach().cpu().numpy().astype(np.float32).reshape(-1)
            for i in range(0, len(pcm), self.frame_samples):
                yield pcm[i:i + self.frame_samples]
        
    async def get_audio_stream(self, text: str):
        """
        Asynchronously generates audio chunks for a given input text \n
        **Input**: \n
        - `text`: The input text to be converted to speech. \n
        
        **Yields**: \n
        - PCM audio chunks as numpy arrays of shape (frame_samples,) and dtype float32.
        """
        async for chunk in iterate_tokens_async(generator_callback=self._get_audio_stream_sync, text=text):
            yield chunk

