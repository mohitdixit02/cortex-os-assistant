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

class CortexMainModel:
    def __init__(self):
        logger.info("Initializing generation model...")
        model_config = models.get("main", {})
        self.model = ChatHuggingFace(llm=HuggingFaceEndpoint(
            repo_id=model_config.get("name"),
            task=model_config.get("task", "conversational"),
            max_new_tokens=model_config.get("max_new_tokens", 500),
            temperature=model_config.get("temperature", 0.2)
        ))
        # self.template_provider = TemplateProvider()
        # self.str_parser = StrOutputParser()
        
    def get_model(self):
        return self.model
        
    def generate(
        self,
        query: str,
    ):
        logger.info("Generating response...")
        prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template("You are a helpful assistant that provides concise and accurate answers to user queries."),
            HumanMessagePromptTemplate.from_template("{query}")
        ])
        formatted_prompt = prompt.format_messages(query=query)
        print(formatted_prompt)
        logger.info("Generating response for query: %s", query)
        response = self.model.invoke(formatted_prompt)
        return response.content
        
       