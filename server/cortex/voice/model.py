from langchain_huggingface import HuggingFacePipeline, HuggingFaceEmbeddings, HuggingFaceEndpoint, ChatHuggingFace, HuggingFaceEndpointEmbeddings
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from pydantic import BaseModel, Field
from typing import TypedDict, Annotated, Literal, Optional, Dict, Any
import numpy as np
from numpy import dot
from numpy.linalg import norm
from logger import logger
from utility.huggingface.config import models
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate, HumanMessagePromptTemplate

# class QueryTypeStructModel(BaseModel):
#     type: Annotated[Literal["casual", "query"], Field(description="Type of the user query")]

# class CasualResponseStructModel(BaseModel):
#     response: Annotated[str, Field(description="Response to the casual user query")]
    
# class QueryResponseStructModel(BaseModel):
#     answer: Annotated[Dict[str, Any],  Field(description="Answer to the user query based on the provided context in form of key-value pairs")]
    
# class WikiKeywordResponseModel(BaseModel):
#     keywords: Annotated[list, Field(description="List of relevant keywords extracted from the user query")]

text = """
    This is a sample response from the CortexMainModel. The actual implementation will generate dynamic responses based on user queries and context. This model is designed to provide concise and accurate answers to user queries, leveraging the power of HuggingFace's language models. The response is streamed token by token to allow for real-time interaction with the user.
    The CortexMainModel can be extended to include more complex logic, such as handling different types of queries (e.g., casual conversation vs. specific information retrieval), integrating with external APIs for additional context, and providing structured responses based on the user's needs. The model is built with flexibility in mind, allowing for easy updates and improvements as new features are added.
    Overall, the CortexMainModel serves as the core component of the system, responsible for generating intelligent and contextually relevant responses to user queries, making it a powerful tool for a wide range of applications.    
    Mainly, it will utilize HuggingFace's language models to understand and respond to user input in a natural and engaging way, providing a seamless conversational experience.    
"""

def demo_response(chunk_size: int = 24):
    """Yield small text chunks to simulate token streaming in tests."""
    cleaned = " ".join(text.split())
    for i in range(0, len(cleaned), chunk_size):
        yield cleaned[i:i + chunk_size]
    
class VoiceMainModel:
    def __init__(self):
        logger.info("Initializing generation model...")
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
        logger.info("Streaming response tokens for query: %s", query)
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template("You are a helpful assistant that provides concise and accurate answers to user queries. Don't reply in more than 20 words."),
            HumanMessagePromptTemplate.from_template("{query}")
        ])
        formatted_prompt = prompt.format_messages(query=query)
        # for chunk in self.model.stream(formatted_prompt):
        for chunk in demo_response():
            token = self._chunk_to_text(chunk)
            if token:
                yield token
        
    async def generate(
        self,
        query: str,
    ):
        logger.info("Generating response...")
        return self.stream_text_tokens(query)
        
       