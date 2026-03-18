"""
This module contains the configuration for Hugging Face models used in the application. 
Dictionary that maps model types (e.g., "stt", "tts", "main") to their corresponding Hugging Face model names. 
"""

models = {
    "stt": {
        "name": "openai/whisper-large-v3-turbo"
    },
    "tts":{
        "name":"hexgrad/Kokoro-82M"
    },
    "main":{
        "name":"meta-llama/Llama-3.1-8B-Instruct",
        "task":"conversational",
        "max_new_tokens":500,
        "temperature":0.2,
    }
}