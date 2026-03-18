import os
import requests
from dotenv import load_dotenv
from typing import Literal
from utility.huggingface.config import models
from huggingface_hub import InferenceClient
load_dotenv()

HUGGINGFACE_API_KEY = os.environ["HF_TOKEN"]
HUGGINGFACE_MODEL_API_URL = "https://api-inference.huggingface.co/models/"

def HuggingFaceRequest(
    feature: Literal["tts", "stt", "embedding"], # Literal needs to update later
    data: dict,  
) -> dict:
    """
        Sends request to the HuggingFace API for the specified feature and data.
        Args:
            feature (str): The feature to use ("tts", "stt", or "embedding"). Helps in setting custom headers
            data (dict): The data to send in the request.
    """
    
    model_name = models[feature].get("name") if feature in models else None
    if not model_name:
        raise ValueError(f"No model configured for feature '{feature}'")
        
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
    }
    
    if feature == "stt":
        headers["Content-Type"] = "audio/wav"
        client = InferenceClient(
            model=model_name,
            token=HUGGINGFACE_API_KEY,
            headers=headers
        )
        res = client.automatic_speech_recognition(
            audio=data
        )
        return res
    else:
        headers["Content-Type"] = "application/json"
        
    
    