import requests
from typing import Literal
from cortex_cm.utility.huggingface.config import models
from huggingface_hub import InferenceClient
from cortex_cm.utility.config import env

HUGGINGFACE_API_KEY = env.HF_TOKEN

def HuggingFaceRequest(
    feature: Literal["tts", "stt", "embedding", "voice_emotion"], # Literal needs to update later
    data: dict,  
) -> dict:
    """
        Sends request to the HuggingFace API for the specified feature and data.
        Args:
            feature (str): The feature to use ("tts", "stt", "embedding", or "voice_emotion"), helps in setting custom headers
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
    elif feature == "voice_emotion":
        headers["Content-Type"] = "application/json"
        client = InferenceClient(
            model=model_name,
            token=HUGGINGFACE_API_KEY,
            headers=headers
        )
        res = client.text_classification(
            text=data,
            model=model_name
        )
        output = []
        for item in res:
            output.append({
                "label": item.label,
                "score": item.score
            })
        return output
    else:
        headers["Content-Type"] = "application/json"
        
    