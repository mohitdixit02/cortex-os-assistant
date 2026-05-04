from langchain_huggingface import HuggingFaceEmbeddings, HuggingFaceEndpointEmbeddings, ChatHuggingFace, HuggingFaceEndpoint
from typing import Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from cortex_cm.utility.huggingface.config import models
from cortex_cm.utility.config import env
import numpy as np
from numpy import dot
from numpy.linalg import norm
from cortex_cm.utility.models import get_embedding_model

class EmbeddingModel:
    def __init__(self):
        # self.embd_model = HuggingFaceEndpointEmbeddings(
        #     model="sentence-transformers/all-MiniLM-L6-v2",
        #     task="feature-extraction",
        #     huggingfacehub_api_token=env.HF_TOKEN
        # )
        self.embd_model = get_embedding_model()
        
    def generate_embeddings(self, text: str) -> list[float]:
        """
        Generate embeddings for the given text using the model. \n
        """
        return self.embd_model.embed_query(text)

    def _embed_batch(self, batch_items: list[str]) -> list[list[float]]:
        return self.embd_model.embed_documents(batch_items)
    
    def generate_embeddings_batch(
        self,
        texts: list[str],
        batch_size: int = 32,
        max_workers: int = 4,
    ) -> list[list[float]]:
        """Generate embeddings for multiple texts using batched requests with bounded parallelism."""
        if not texts:
            return []

        normalized_texts = [text if isinstance(text, str) else str(text) for text in texts]
        indexed_batches: list[tuple[int, list[str]]] = []
        for i in range(0, len(normalized_texts), batch_size):
            indexed_batches.append((i, normalized_texts[i:i + batch_size]))

        results: list[list[float] | None] = [None] * len(normalized_texts)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_offset = {
                executor.submit(self._embed_batch, batch_items): offset
                for offset, batch_items in indexed_batches
            }
            for future in as_completed(future_to_offset):
                offset = future_to_offset[future]
                batch_embeddings = future.result()
                for idx, emb in enumerate(batch_embeddings):
                    results[offset + idx] = emb

        # Fallback - In case any worker failed to fill any position.
        for i, emb in enumerate(results):
            if emb is None:
                results[i] = self.generate_embeddings(normalized_texts[i])

        return [emb for emb in results if emb is not None]
    
    def get_cosine_similarity(self, query_embedding: list[float], doc_embedding: list[float]) -> float:
        cosine_sim = dot(np.array(query_embedding), np.array(doc_embedding)) / (norm(np.array(query_embedding)) * norm(np.array(doc_embedding)))
        return cosine_sim
