"""
Configuration for sensory utilities, such as speech-to-text (STT) settings or text-to-speech (TTS) settings. 
This module defines constants and parameters that are used across the sensory components of the application.
"""

STT_CONFIG = {
    "sample_rate": 16000,
    "seconds": 5,
    "channels": 1
}

TTS_CONFIG = {
    "voice": "af_heart",
    "sample_rate": 24000,
    "channels": 1
}