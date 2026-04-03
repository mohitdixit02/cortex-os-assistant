from langchain_huggingface import HuggingFacePipeline, HuggingFaceEmbeddings, HuggingFaceEndpoint, ChatHuggingFace, HuggingFaceEndpointEmbeddings
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from pydantic import BaseModel, Field
from typing import TypedDict, Annotated, Literal, Optional, Dict, Any
import numpy as np
from numpy import dot
from numpy.linalg import norm
from utility.logger import get_logger
from utility.huggingface.config import models
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate, HumanMessagePromptTemplate

text = """
    Hi, It is Cortex Main Model. I am main Orchestrator for handling user queries and generating responses. I can understand and respond to a wide range of queries, providing concise and accurate answers.
"""

def demo_response(chunk_size: int = 24):
    """Yield small text chunks to simulate token streaming in tests."""
    cleaned = " ".join(text.split())
    for i in range(0, len(cleaned), chunk_size):
        yield cleaned[i:i + chunk_size]

class CortexMainModel:
    def __init__(self):
        self.logger = get_logger("CORTEX_MAIN")
        self.logger.info("Initializing generation model...")
        model_config = models.get("main", {})
        self.model = ChatHuggingFace(llm=HuggingFaceEndpoint(
            repo_id=model_config.get("name"),
            task=model_config.get("task", "conversational"),
            max_new_tokens=model_config.get("max_new_tokens", 200),
            temperature=model_config.get("temperature", 0.2)
        ))
        # self.template_provider = TemplateProvider()
        # self.str_parser = StrOutputParser()
        
    def get_model(self):
        return self.model
    
    def _chunk_to_text(self, chunk: Any) -> str:
        if chunk is None:
            return ""
        if isinstance(chunk, str):
            return chunk
        content = getattr(chunk, "content", "")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str):
                        parts.append(text)
            return "".join(parts)
        return str(content) if content else ""

    def stream_text_tokens(self, query: str):
        """Cortex Model"""
        self.logger.info("Streaming response tokens for query: %s", query)
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template("You are a helpful friend wit cool vibe that provides answers to user queries. Don't reply in more than 100 words."),
            HumanMessagePromptTemplate.from_template("{query}")
        ])
        formatted_prompt = prompt.format_messages(query=query)
        # for chunk in self.model.stream(formatted_prompt):
        for chunk in demo_response():
            token = self._chunk_to_text(chunk)
            if token:
                yield token
        
       