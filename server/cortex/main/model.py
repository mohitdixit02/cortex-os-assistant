from langchain_huggingface import HuggingFacePipeline, HuggingFaceEmbeddings, HuggingFaceEndpoint, ChatHuggingFace, HuggingFaceEndpointEmbeddings
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from pydantic import BaseModel, Field
from cortex.graph.state import ConversationState, OrchestrationState
from cortex.main.prompts import get_main_client_prompts
from typing import TypedDict, Annotated, Literal, Optional, Dict, Any
import numpy as np
from numpy import dot
from numpy.linalg import norm
from utility.logger import get_logger
from utility.huggingface.config import models
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from cortex.manager.tools import AVAILABLE_TOOLS
import json
from utility.models import MAIN_MODEL, PLANNER_MODEL

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
        self.model = MAIN_MODEL
        self.plan_model = PLANNER_MODEL
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

    def _serialize_tool_results(self, state: ConversationState) -> Optional[str]:
        """Serialize tool results into JSON payload for prompts."""
        orchestration_plan = state.orchestration_state
        if not orchestration_plan or not orchestration_plan.selected_tools:
            return None

        tools_result_list = (
            orchestration_plan.selected_tools.root
            if hasattr(orchestration_plan.selected_tools, "root")
            else orchestration_plan.selected_tools
        )
        if not tools_result_list:
            return None

        serializable_tools = [
            tool.model_dump() if hasattr(tool, "model_dump") else tool
            for tool in tools_result_list
        ]
        return json.dumps(serializable_tools)

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
                
    def build_main_orchestration_plan(self, state: ConversationState):
        formatted_prompt, parser = get_main_client_prompts(
            type="main_orchestration",
        )
        chain = formatted_prompt | self.plan_model | parser
        available_tools = "\n".join([f"{tool.get('tool_name')}: {tool.get('tool_description')} - {tool.get('tool_id')}" for tool in AVAILABLE_TOOLS])
        
        feedback = state.plan_feedback
        if feedback and feedback.user_knowledge_retrieval_feedback:
            user_knowledge_retrieval_feedback = feedback.user_knowledge_retrieval_feedback
        else:
            user_knowledge_retrieval_feedback = ""
            
        if feedback and feedback.message_retrieval_feedback:
            message_retrieval_feedback = feedback.message_retrieval_feedback
        else:
            message_retrieval_feedback = ""

        res = chain.invoke({
            "available_tools": available_tools,
            "user_query": state.query,
            "stm_summary": state.short_term_memory.stm_summary if state.short_term_memory else "",
            "stm_preferences": state.short_term_memory.session_preferences if state.short_term_memory else {},
            "user_mood": state.query_emotion,
            "user_time": state.query_time,
            "user_emotional_profile": state.emotional_profile.model_dump_json() if state.emotional_profile else None,
            "user_knowledge_retrieval_feedback": user_knowledge_retrieval_feedback,
            "message_retrieval_feedback": message_retrieval_feedback,
        })
        return res
    
    def evaluate_orchestration_plan(self, state: ConversationState):
        formatted_prompt, parser = get_main_client_prompts(
            type="plan_evaluation",
        )
        chain = formatted_prompt | self.model | parser
        if state.knowledge_base:
            retrieved_user_knowledge = [item.model_dump() for item in state.knowledge_base]
        else:
            retrieved_user_knowledge = None
        
        if state.message_history and state.message_history.root:
            retrieved_messages = [msg.model_dump() for msg in state.message_history.root]
        else:
            retrieved_messages = None
        
        feedback = state.plan_feedback
        if feedback:
            feedback_by_evaluator = feedback.model_dump()
        else:
            feedback_by_evaluator = None

        res = chain.invoke({
            "user_query": state.query,
            "orchestration_plan": state.orchestration_state.model_dump_json() if state.orchestration_state else None,
            "retrieved_user_knowledge": json.dumps(retrieved_user_knowledge) if retrieved_user_knowledge else None,
            "retrieved_messages": json.dumps(retrieved_messages) if retrieved_messages else None,
            "previous_feedback": json.dumps(feedback_by_evaluator) if feedback_by_evaluator else None,
            "user_mood": state.query_emotion,
            "user_emotional_profile": state.emotional_profile.model_dump_json() if state.emotional_profile else None,
        })
        return res
    
    def generate_final_response(self, state: ConversationState):
        formatted_prompt, parser = get_main_client_prompts(
            type="final_response_generation",
        )
        if state.knowledge_base:
            retrieved_user_knowledge = [item.model_dump() for item in state.knowledge_base]
        else:
            retrieved_user_knowledge = None
        
        if state.message_history and state.message_history.root:
            retrieved_messages = [msg.model_dump() for msg in state.message_history.root]
        else:
            retrieved_messages = None
            
        feedback = state.final_response_feedback
        if feedback:
            feedback_by_evaluator = feedback.model_dump()
        else:
            feedback_by_evaluator = None
            
        tool_result_payload = self._serialize_tool_results(state)
        
        chain = formatted_prompt | self.model | parser
        res = chain.invoke({
            "user_query": state.query,
            "stm_summary": state.short_term_memory.stm_summary if state.short_term_memory else "",
            "stm_preferences": state.short_term_memory.session_preferences if state.short_term_memory else {},
            "user_mood": state.query_emotion,
            "user_time": state.query_time,
            "user_emotional_profile": state.emotional_profile.model_dump_json() if state.emotional_profile else None,
            "retrieved_user_knowledge": json.dumps(retrieved_user_knowledge) if retrieved_user_knowledge else None,
            "retrieved_messages": json.dumps(retrieved_messages) if retrieved_messages else None,
            "previous_feedback": json.dumps(feedback_by_evaluator) if feedback_by_evaluator else None,
            "tool_result": tool_result_payload,
            "fallback_response": state.voice_client_response if state.voice_client_response else "",
        })
        return res
    
    def evaluate_final_response(self, state: ConversationState):
        formatted_prompt, parser = get_main_client_prompts(
            type="final_response_evaluation",
        )
        chain = formatted_prompt | self.plan_model | parser
        
        if state.knowledge_base:
            retrieved_user_knowledge = [item.model_dump() for item in state.knowledge_base]
        else:
            retrieved_user_knowledge = None
        
        if state.message_history and state.message_history.root:
            retrieved_messages = [msg.model_dump() for msg in state.message_history.root]
        else:
            retrieved_messages = None
            
        feedback = state.final_response_feedback
        if feedback:
            feedback_by_evaluator = feedback.model_dump()
        else:
            feedback_by_evaluator = None
        
        tool_result_payload = self._serialize_tool_results(state)
        
        res = chain.invoke({
            "user_query": state.query,
            "final_response": state.final_response.response if state.final_response else None,
            "stm_summary": state.short_term_memory.stm_summary if state.short_term_memory else "",
            "stm_preferences": state.short_term_memory.session_preferences if state.short_term_memory else {},
            "user_mood": state.query_emotion,
            "user_time": state.query_time,
            "user_emotional_profile": state.emotional_profile.model_dump_json() if state.emotional_profile else None,
            "retrieved_user_knowledge": json.dumps(retrieved_user_knowledge) if retrieved_user_knowledge else None,
            "retrieved_messages": json.dumps(retrieved_messages) if retrieved_messages else None,
            "previous_feedback": json.dumps(feedback_by_evaluator) if feedback_by_evaluator else None,
            "tool_result": tool_result_payload,
            "fallback_response": state.voice_client_response if state.voice_client_response else "",
        })
        return res
