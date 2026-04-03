from langchain_huggingface import HuggingFaceEndpointEmbeddings, ChatHuggingFace, HuggingFaceEndpoint
from typing import Any
from utility.huggingface.config import models
from utility.config import env

class EmbeddingModel:
    def __init__(self):
        self.embd_model = HuggingFaceEndpointEmbeddings(
            model="sentence-transformers/all-MiniLM-L6-v2",
            task="feature-extraction",
            huggingfacehub_api_token=env.HF_TOKEN
        )
        
    def generate_embeddings(self, text: str) -> list[float]:
        """
        Generate embeddings for the given text using the model. \n
        """
        return self.embd_model.embed_query(text)
