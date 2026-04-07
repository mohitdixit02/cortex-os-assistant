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
from utility.huggingface.request import HuggingFaceRequest
from cortex.voice.prompts import VoiceClientRouteQuery, get_voice_client_prompts

# class QueryTypeStructModel(BaseModel):
#     type: Annotated[Literal["casual", "query"], Field(description="Type of the user query")]

# class CasualResponseStructModel(BaseModel):
#     response: Annotated[str, Field(description="Response to the casual user query")]
    
# class QueryResponseStructModel(BaseModel):
#     answer: Annotated[Dict[str, Any],  Field(description="Answer to the user query based on the provided context in form of key-value pairs")]
    
# class WikiKeywordResponseModel(BaseModel):
#     keywords: Annotated[list, Field(description="List of relevant keywords extracted from the user query")]

text = """
    Hi, It is Voice Model. I can speak in many langugages, in different tones and styles. I can also express emotions through my voice.
"""

def demo_response(chunk_size: int = 24):
    """Yield small text chunks to simulate token streaming in tests."""
    cleaned = " ".join(text.split())
    for i in range(0, len(cleaned), chunk_size):
        yield cleaned[i:i + chunk_size]
    
class VoiceMainModel:
    def __init__(self):
        self.logger = get_logger("CORTEX_VOICE")
        self.logger.info("Initializing generation model...")
        model_config = models.get("main", {})
        self.model = ChatHuggingFace(llm=HuggingFaceEndpoint(
            repo_id=model_config.get("name"),
            task=model_config.get("task", "conversational"),
            max_new_tokens=model_config.get("max_new_tokens", 200),
            temperature=model_config.get("temperature", 0.2)
        ))
        planner_model_config = models.get("planner", {})
        self.plan_model = ChatHuggingFace(llm=HuggingFaceEndpoint(
            repo_id=planner_model_config.get("name"),
            task=planner_model_config.get("task", "conversational"),
            max_new_tokens=planner_model_config.get("max_new_tokens", 200),
            temperature=planner_model_config.get("temperature", 0.2)
        ))
        
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
    
    def get_response_route(self, query: str) -> VoiceClientRouteQuery:
        """Voice Model"""
        self.logger.info("Streaming response tokens for query: %s", query)
        formatted_prompt, parser = get_voice_client_prompts(
            type="route_query",
            query=query
        )
        chain = formatted_prompt | self.plan_model | parser
        res = chain.invoke({"user_query": query})
        return res

    def stream_text_tokens(self, query: str):
        """Streaming Tokens for Casual Response from Voice Model"""
        formatted_prompt = get_voice_client_prompts(
            type="casual_response",
            query=query
        )
        chain = self.model | StrOutputParser()
        res = chain.invoke(formatted_prompt)
        return res
    
    def stream_fallback_response(self, query: str):
        """Streaming Tokens for Fallback Response from Voice Model"""
        formatted_prompt = get_voice_client_prompts(
            type="fallback_response",
            query=query
        )
        chain = self.model | StrOutputParser()
        res = chain.invoke(formatted_prompt)
        return res


class EmotionDetectionModel:
    """
    ## Emotion Detection Model
    Model for detecting emotion from input text using LLM
    
    **Functions**:
    - `get_emotion(text: str) -> Dict[str, Any]` : Detects emotion from the input text.
    """
    def __init__(self):
        self.logger = get_logger("CORTEX_VOICE")
        self.logger.info("Initializing generation model...")
        self.model_config = models.get("voice_emotion", {})
        
    def get_model(self):
        return self.model
    
    def get_emotion(self, text: str) -> Dict[str, Any]:
        """
        Detects Emotion from the input text using LLM \n
        **Input**: \n
        - `text`: The input text for which to detect emotion. \n
        **Returns**: \n
        - A dictionary containing the detected emotion label and its corresponding confidence score. \n
         For example: `{"label": "joy", "score": 0.95}`
        """
        self.logger.info("Detecting emotion for text: %s", text)
        res = HuggingFaceRequest(
            feature="voice_emotion",
            data=text
        )
        self.logger.info("Emotion detection result: %s", res)
        output = sorted(res, key=lambda x: x["score"], reverse=True)
        if output:
            top_emotion = output[0]
            top_emotion_score = top_emotion["score"]
            self.logger.info("Top detected emotion: %s with score %.4f", top_emotion["label"], top_emotion["score"])
            return {
                "label": top_emotion["label"],
                "score": top_emotion_score
            }
        else:
            self.logger.warning("No emotions detected, returning 'neutral'")
            return {
                "label": "neutral",
                "score": 1.0
            }