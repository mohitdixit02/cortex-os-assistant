"""
Configuration for sensory utilities, such as speech-to-text (STT) settings or text-to-speech (TTS) settings. 
This module defines constants and parameters that are used across the sensory components of the application.
"""

STT_CONFIG = {
    "sample_rate": 16000,
    "seconds": 5,
    "channels": 1,
    "chunk_size_s": 10.0,
    "overlap_s": 1.0,
    "chunk_seconds_max_limit": 10.0,
    "end_speech_silence_threshold": 0.2,
    "chunk_batch_size": 1,
    "model_np_dtype": "float32"
}

TTS_CONFIG = {
    "voice": "af_heart",
    "sample_rate": 24000,
    "channels": 1,
    "format": "f32le",
}