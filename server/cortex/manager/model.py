from langchain_huggingface import HuggingFacePipeline, HuggingFaceEmbeddings, HuggingFaceEndpoint, ChatHuggingFace, HuggingFaceEndpointEmbeddings
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from pydantic import BaseModel, Field
from cortex.graph.state import ConversationState, CortexTool, OrchestrationState
from cortex.manager.prompts import get_manager_client_prompts
from typing import TypedDict, Annotated, Literal, Optional, Dict, Any
import numpy as np
from numpy import dot
from numpy.linalg import norm
from utility.logger import get_logger
from utility.huggingface.config import models
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from cortex.manager.tools import AVAILABLE_TOOLS, WebSearchInput
import json

class ManagerModel:
    def __init__(self):
        self.logger = get_logger("CORTEX_MANAGER")
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
                
    def build_web_search_plan(
        self,
        query: str,
        tool: CortexTool,
    ) -> WebSearchInput:
        """
        Build the input for web search tool based on the user query and orchestrator instructions using the generation model. \n
        - query: user query for which the web search input is to be generated
        - tool: CortexTool object which may contain instructions from the orchestrator for web search query planning
        
        Returns: WebSearchInput object containing the generated keywords for web search
        """
        formatted_prompt, parser = get_manager_client_prompts(
            type="web_query_planning",
        )
        chain = formatted_prompt | self.model | parser
        
        instructions = tool.instructions if tool.instructions else ""

        res = chain.invoke({
            "user_query": query,
            "orchestrator_instructions": instructions
        })
        web_input = WebSearchInput(
            query=res.query
        )
        return web_input

    def summarize_tool_result(
        self,
        tool_result: str,
        query: str,
        tool_type: str,
    ) -> str:
        """
        Summarize the tool result based on the user query and tool type using the generation model. \n
        - tool_result: The raw result obtained from executing the tool which may contain a large amount of information
        - query: user query for which the tool was executed, to be used as context for summarization
        - tool_type: type of the tool which may be used to condition the summarization (e.g. web search result may be summarized differently than a calculator result)
        
        Returns: A summarized version of the tool result which is concise and relevant to the user query
        """
        formatted_prompt, parser = get_manager_client_prompts(
            type="tool_result_summarization",
            tool_type=tool_type,
        )
        chain = formatted_prompt | self.model | parser
        
        res = chain.invoke({
            "tool_result": tool_result,
            "user_query": query,
            "tool_type": tool_type,
        })
        summary = self._chunk_to_text(res)
        return summary
