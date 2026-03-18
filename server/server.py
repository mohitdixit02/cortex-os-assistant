from langchain_huggingface import HuggingFacePipeline, HuggingFaceEmbeddings, HuggingFaceEndpoint, ChatHuggingFace, HuggingFaceEndpointEmbeddings

import io
import os
from huggingface_hub import InferenceClient
import sounddevice as sd
import soundfile as sf
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.environ["HF_TOKEN"]
client = InferenceClient(
    provider="hf-inference",
    api_key=api_key,
)

# model = ChatHuggingFace(llm=HuggingFaceEndpoint(
#     repo_id="meta-llama/Llama-3.1-8B-Instruct",
#     task="conversational",
#     max_new_tokens=500,
#     temperature=0.2,
# ))

sample_rate = 16000
seconds = 5

print("Recording...")
audio = sd.rec(
    int(seconds * sample_rate),
    samplerate=sample_rate,
    channels=1,
    dtype="float32",
)
sd.wait()

print("Recording finished.")
wav_buffer = io.BytesIO()
sf.write(wav_buffer, audio.flatten(), sample_rate, format='WAV')

wav_buffer.seek(0) # Reset buffer position

# 4. Pass buffer to inference client
audio_bytes = wav_buffer.getvalue()
response = requests.post(
    "https://router.huggingface.co/hf-inference/models/openai/whisper-large-v3-turbo",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "audio/wav",
    },
    data=audio_bytes,
)
response.raise_for_status()
result = response.json()
print(result)
print(result["text"])
