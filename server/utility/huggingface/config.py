"""
This module contains the configuration for Hugging Face models used in the application. 
Dictionary that maps model types (e.g., "stt", "tts", "main") to their corresponding Hugging Face model names. 
"""

import torch

models = {
    "stt": {
        # "name": "openai/whisper-large-v3-turbo",
        "name": "openai/whisper-small",
        "dtype": torch.float16 if torch.cuda.is_available() else torch.float32,
        "device": "cuda:0" if torch.cuda.is_available() else "cpu",
        "model_np_dtype": "float32",
        "low_cpu_mem_usage": True,
        "use_safetensors": True,
        "processor_return_tensors": "pt",
        "task": "transcribe",
        "return_timestamps": False,
        "skip_special_tokens": True,
        "max_source_positions": 3000
    },
    "tts":{
        "name":"hexgrad/Kokoro-82M"
    },
    "main":{
        "name":"meta-llama/Llama-3.1-8B-Instruct",
        "task":"conversational",
        "max_new_tokens":500,
        "temperature":0.2,
    },
    "voice_emotion":{
        "name":"boltuix/bert-emotion",
        "task":"text-classification",
        "max_new_tokens":50,
        "temperature":0.2,
    }
}