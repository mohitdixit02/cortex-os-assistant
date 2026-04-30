from langchain_huggingface import HuggingFacePipeline, HuggingFaceEmbeddings, HuggingFaceEndpoint, ChatHuggingFace, HuggingFaceEndpointEmbeddings
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from cortex.graph.state import ConversationState, OrchestrationState, CortexToolList
from typing import TypedDict, Annotated, Literal, Optional, Dict, Any
import numpy as np
from utility.logger import get_logger
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from cortex.manager.tools import AVAILABLE_TOOLS
import json
from utility.models import HEAVY_PLANNER_MODEL, HEAVY_RESPONSE_MODEL, MAIN_ORCHESTRATOR_MODEL
from cortex.main.prompts import get_main_orchestrator_evaluate_prompt, get_main_orchestrator_plan_prompt, get_main_orchestrator_res_prompt
from cortex.main.prompts.main_evaluator import (
    InternalFeedbackKnowledge,
    InternalFeedbackMessages,
    InternalFeedbackTools,
)
from cortex.main.prompts.main_planner import (
    InternalPlanKnowledge,
    InternalPlanMessages,
    InternalPlanTools,
)
from cortex.main.prompts.orchestrator import MainOrchestrationDecision

from datetime import datetime, timezone
UTC_NOW = lambda: datetime.now(timezone.utc)

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
        self.heavy_plan_model = HEAVY_PLANNER_MODEL
        self.heavy_response_model = HEAVY_RESPONSE_MODEL
        self.main_orchestrator_model = MAIN_ORCHESTRATOR_MODEL
        # self.template_provider = TemplateProvider()
        # self.str_parser = StrOutputParser()
    
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
      
    def build_main_orchestration_plan(self, state: ConversationState) -> MainOrchestrationDecision:
        formatted_prompt, parser = get_main_orchestrator_plan_prompt(
            type="main_orchestration",
        )
        chain = formatted_prompt | self.main_orchestrator_model | parser
        
        orchestration_plan = state.orchestration_state
        if orchestration_plan and orchestration_plan.user_knowledge_retrieval_keywords:
            knowledge_plan_builder_output = json.dumps(orchestration_plan.user_knowledge_retrieval_keywords)
        else:
            knowledge_plan_builder_output = "[]"
            
        if orchestration_plan and orchestration_plan.referred_message_keywords:
            conversation_history_plan_builder_output = orchestration_plan.referred_message_keywords
        else:
            conversation_history_plan_builder_output = ""
            
        if orchestration_plan and orchestration_plan.selected_tools:
            tools_payload = orchestration_plan.selected_tools.root if hasattr(orchestration_plan.selected_tools, "root") else orchestration_plan.selected_tools
            tools_payload = [tool.model_dump() if hasattr(tool, "model_dump") else tool for tool in tools_payload]
            tool_selection_plan_builder_output = json.dumps(tools_payload)
        else:
            tool_selection_plan_builder_output = "[]"
            
        retrieved_user_knowledge = ""
        if state.knowledge_base:
            for item in state.knowledge_base:
                retrieved_user_knowledge += f"- {item.strictness}: {item.content}\n"
                
        if state.message_history and state.message_history.root:
            retrieved_messages = ""
            for msg in state.message_history.root:
                retrieved_messages += f"{msg.role}: {msg.content}\n"
        else:
            retrieved_messages = ""
        
        feedback = state.plan_feedback
        
        if feedback and feedback.iteration_count:
            iteration_count = feedback.iteration_count
        else:
            iteration_count = 0
        
        if feedback and feedback.user_knowledge_retrieval_feedback:
            user_knowledge_retrieval_feedback = feedback.user_knowledge_retrieval_feedback
        else:
            user_knowledge_retrieval_feedback = ""
            
        if feedback and feedback.message_retrieval_feedback:
            message_retrieval_feedback = feedback.message_retrieval_feedback
        else:
            message_retrieval_feedback = ""
        
        if feedback and feedback.tool_selection_feedback:
            tool_selection_feedback = feedback.tool_selection_feedback
        else:
            tool_selection_feedback = ""
            
        available_tools = "\n".join([f"{tool.get('tool_name')}: {tool.get('tool_description')} - {tool.get('tool_id')}" for tool in AVAILABLE_TOOLS])

        res = chain.invoke({
            "knowledge_plan_builder_output": knowledge_plan_builder_output,
            "conversation_history_plan_builder_output": conversation_history_plan_builder_output,
            "tool_selection_plan_builder_output": tool_selection_plan_builder_output,
            "retrieved_user_knowledge": retrieved_user_knowledge,
            "retrieved_messages": retrieved_messages,
            "knowledge_plan_builder_feedback": user_knowledge_retrieval_feedback,
            "conversation_history_plan_builder_feedback": message_retrieval_feedback,
            "tool_selection_feedback": tool_selection_feedback,
            "user_query": state.query,
            "stm_summary": state.short_term_memory.stm_summary if state.short_term_memory else "",
            "stm_preferences": state.short_term_memory.session_preferences if state.short_term_memory else {},
            "available_tools": available_tools,
            "iteration_count": iteration_count,
        })
        
        return res

    def build_main_orchestration_knowledge_plan(self, state: ConversationState) -> InternalPlanKnowledge:
        formatted_prompt, parser = get_main_orchestrator_plan_prompt(
            type="main_orchestration_knowledge",
        )
        chain = formatted_prompt | self.heavy_plan_model | parser
        
        feedback = state.plan_feedback
        if feedback and feedback.user_knowledge_retrieval_feedback:
            user_knowledge_retrieval_feedback = feedback.user_knowledge_retrieval_feedback
        else:
            user_knowledge_retrieval_feedback = ""
        
        res = chain.invoke({
            "user_query": state.query,
            "stm_summary": state.short_term_memory.stm_summary if state.short_term_memory else "",
            "stm_preferences": state.short_term_memory.session_preferences if state.short_term_memory else {},
            "user_mood": state.query_emotion,
            "user_time": state.query_time,
            "user_emotional_profile": state.emotional_profile.model_dump_json() if state.emotional_profile else None,
            "user_knowledge_retrieval_feedback": user_knowledge_retrieval_feedback,
        })
        
        return res
    
    def build_main_orchestration_messages_plan(self, state: ConversationState) -> InternalPlanMessages:
        formatted_prompt, parser = get_main_orchestrator_plan_prompt(
            type="main_orchestration_messages",
        )
        chain = formatted_prompt | self.heavy_plan_model | parser
                
        feedback = state.plan_feedback
            
        if feedback and feedback.message_retrieval_feedback:
            message_retrieval_feedback = feedback.message_retrieval_feedback
        else:
            message_retrieval_feedback = ""
        
        retrieved_user_knowledge = ""
        if state.knowledge_base:
            for item in state.knowledge_base:
                retrieved_user_knowledge += f"- {item.strictness}: {item.content}\n"

        res = chain.invoke({
            "user_query": state.query,
            "stm_summary": state.short_term_memory.stm_summary if state.short_term_memory else "",
            "stm_preferences": state.short_term_memory.session_preferences if state.short_term_memory else {},
            "user_mood": state.query_emotion,
            "user_time": state.query_time,
            "message_retrieval_feedback": message_retrieval_feedback,
            "retrieved_user_knowledge": retrieved_user_knowledge,
        })
        return res
    
    def build_main_orchestration_tools_plan(self, state: ConversationState) -> InternalPlanTools:
        formatted_prompt, parser = get_main_orchestrator_plan_prompt(
            type="main_orchestration_tools",
        )
        chain = formatted_prompt | self.heavy_plan_model | parser
        available_tools = "\n".join([f"{tool.get('tool_name')}: {tool.get('tool_description')} - {tool.get('tool_id')}" for tool in AVAILABLE_TOOLS])
        
        feedback = state.plan_feedback
            
        if feedback and feedback.tool_selection_feedback:
            tool_selection_feedback = feedback.tool_selection_feedback
        else:
            tool_selection_feedback = ""
        
        retrieved_user_knowledge = ""
        if state.knowledge_base:
            for item in state.knowledge_base:
                retrieved_user_knowledge += f"- {item.strictness}: {item.content}\n"
        
        if state.message_history and state.message_history.root:
            retrieved_messages = ""
            for msg in state.message_history.root:
                retrieved_messages += f"{msg.role}: {msg.content}\n"
        else:
            retrieved_messages = None
        
        timestamp = UTC_NOW()
        if timestamp.tzinfo is not None and timestamp.tzinfo.utcoffset(timestamp) is not None:
            local_timestamp = timestamp.astimezone()
        else:
            local_timestamp = timestamp

        res = chain.invoke({
            "available_tools": available_tools,
            "user_query": state.query,
            "stm_summary": state.short_term_memory.stm_summary if state.short_term_memory else "",
            "stm_preferences": state.short_term_memory.session_preferences if state.short_term_memory else {},
            "user_mood": state.query_emotion,
            "user_time": state.query_time,
            "user_emotional_profile": state.emotional_profile.model_dump_json() if state.emotional_profile else None,
            "tool_selection_feedback": tool_selection_feedback,
            "retrieved_user_knowledge": retrieved_user_knowledge,
            "retrieved_messages": retrieved_messages,
            "timestamp": local_timestamp,
        })
        return res
    
    def evaluate_orchestration_knowledge_plan(self, state: ConversationState) -> InternalFeedbackKnowledge:
        formatted_prompt, parser = get_main_orchestrator_evaluate_prompt(
            type="plan_evaluation_knowledge",
        )
        chain = formatted_prompt | self.heavy_plan_model | parser
        
        retrieved_user_knowledge = ""
        if state.knowledge_base:
            for item in state.knowledge_base:
                retrieved_user_knowledge += f"- {item.strictness}: {item.content}\n"
        
        feedback = state.plan_feedback
        if feedback and feedback.user_knowledge_retrieval_feedback:
            feedback_by_evaluator = feedback.user_knowledge_retrieval_feedback
        else:
            feedback_by_evaluator = ""

        specific_orchestration_plan = OrchestrationState(
            user_knowledge_retrieval_keywords=state.orchestration_state.user_knowledge_retrieval_keywords,
            user_knowledge_acceptance_threshold=state.orchestration_state.user_knowledge_acceptance_threshold,
        ) if state.orchestration_state else None
        
        res = chain.invoke({
            "user_query": state.query,
            "orchestration_plan": specific_orchestration_plan.model_dump_json() if specific_orchestration_plan else None,
            "retrieved_user_knowledge": retrieved_user_knowledge,
            "previous_feedback": feedback_by_evaluator,
            "user_mood": state.query_emotion,
            "user_emotional_profile": state.emotional_profile.model_dump_json() if state.emotional_profile else None,
        })
        return res
    
    def evaluate_orchestration_messages_plan(self, state: ConversationState) -> InternalFeedbackMessages:
        formatted_prompt, parser = get_main_orchestrator_evaluate_prompt(
            type="plan_evaluation_messages",    
        )
        chain = formatted_prompt | self.heavy_plan_model | parser
        
        if state.message_history and state.message_history.root:
            retrieved_messages = ""
            for msg in state.message_history.root:
                retrieved_messages += f"{msg.role}: {msg.content}\n"
        else:
            retrieved_messages = None
        
        retrieved_user_knowledge = ""
        if state.knowledge_base:
            for item in state.knowledge_base:
                retrieved_user_knowledge += f"- {item.strictness}: {item.content}\n"
        
        feedback = state.plan_feedback
        if feedback and state.plan_feedback.message_retrieval_feedback:
            feedback_by_evaluator = feedback.message_retrieval_feedback
        else:
            feedback_by_evaluator = ""

        specific_orchestration_plan = OrchestrationState(
            is_message_referred=state.orchestration_state.is_message_referred if state.orchestration_state else False,
            referred_message_keywords=state.orchestration_state.referred_message_keywords if state.orchestration_state else None,
        ) if state.orchestration_state else None
        
        res = chain.invoke({
            "user_query": state.query,
            "orchestration_plan": specific_orchestration_plan.model_dump_json() if specific_orchestration_plan else None,
            "retrieved_messages": retrieved_messages,
            "previous_feedback": feedback_by_evaluator,
            "user_mood": state.query_emotion,
            "retrieved_user_knowledge": retrieved_user_knowledge,
        })
        return res
    
    def evaluate_orchestration_tools_plan(self, state: ConversationState) -> InternalFeedbackTools:
        formatted_prompt, parser = get_main_orchestrator_evaluate_prompt(
            type="plan_evaluation_tools",
        )
        chain = formatted_prompt | self.heavy_plan_model | parser
        
        feedback = state.plan_feedback
        if feedback and state.plan_feedback.tool_selection_feedback:
            feedback_by_evaluator = feedback.tool_selection_feedback
        else:
            feedback_by_evaluator = ""

        available_tools = "\n".join([f"{tool.get('tool_name')}: {tool.get('tool_description')} - {tool.get('tool_id')}" for tool in AVAILABLE_TOOLS])
        
        specific_orchestration_plan = OrchestrationState(
            is_tool_required=state.orchestration_state.is_tool_required if state.orchestration_state else False,
            selected_tools=state.orchestration_state.selected_tools if state.orchestration_state else None,
        ) if state.orchestration_state else None
        
        retrieved_user_knowledge = ""
        if state.knowledge_base:
            for item in state.knowledge_base:
                retrieved_user_knowledge += f"- {item.strictness}: {item.content}\n"
        
        if state.message_history and state.message_history.root:
            retrieved_messages = ""
            for msg in state.message_history.root:
                retrieved_messages += f"{msg.role}: {msg.content}\n"
        else:
            retrieved_messages = None
                
        res = chain.invoke({
            "user_query": state.query,
            "orchestration_plan": specific_orchestration_plan.model_dump_json() if specific_orchestration_plan else None,
            "previous_feedback": feedback_by_evaluator,
            "user_mood": state.query_emotion,
            "user_emotional_profile": state.emotional_profile.model_dump_json() if state.emotional_profile else None,
            "available_tools": available_tools,
            "retrieved_user_knowledge": retrieved_user_knowledge,
            "retrieved_messages": retrieved_messages,
        })
        return res
    
    def generate_final_response(self, state: ConversationState):
        formatted_prompt, parser = get_main_orchestrator_res_prompt(
            type="final_response_generation",
        )
        retrieved_user_knowledge = ""
        if state.knowledge_base:
            for item in state.knowledge_base:
                retrieved_user_knowledge += f"- {item.strictness}: {item.content}\n"
        
        if state.message_history and state.message_history.root:
            retrieved_messages = ""
            for msg in state.message_history.root:
                retrieved_messages += f"{msg.role}: {msg.content}\n"
        else:
            retrieved_messages = None
            
        feedback = state.final_response_feedback
        if feedback:
            feedback_by_evaluator = feedback.model_dump()
        else:
            feedback_by_evaluator = None
            
        tool_result_payload = self._serialize_tool_results(state)
        
        chain = formatted_prompt | self.heavy_response_model | parser
        res = chain.invoke({
            "user_query": state.query,
            "stm_summary": state.short_term_memory.stm_summary if state.short_term_memory else "",
            "stm_preferences": state.short_term_memory.session_preferences if state.short_term_memory else {},
            "user_mood": state.query_emotion,
            "user_time": state.query_time,
            "user_emotional_profile": state.emotional_profile.model_dump_json() if state.emotional_profile else None,
            "retrieved_user_knowledge": retrieved_user_knowledge,
            "retrieved_messages": retrieved_messages,
            "previous_feedback": json.dumps(feedback_by_evaluator) if feedback_by_evaluator else None,
            "tool_result": tool_result_payload,
            "fallback_response": state.voice_client_response if state.voice_client_response else "",
        })
        return res
    
    def evaluate_final_response(self, state: ConversationState):
        formatted_prompt, parser = get_main_orchestrator_res_prompt(
            type="final_response_evaluation",
        )
        chain = formatted_prompt | self.heavy_response_model | parser
        
        if state.knowledge_base:
            retrieved_user_knowledge = ""
            for item in state.knowledge_base:
                retrieved_user_knowledge += f"- {item.strictness}: {item.content}\n"
        else:
            retrieved_user_knowledge = None
        
        if state.message_history and state.message_history.root:
            retrieved_messages = ""
            for msg in state.message_history.root:
                retrieved_messages += f"{msg.role}: {msg.content}\n"
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
            "retrieved_user_knowledge": retrieved_user_knowledge,
            "retrieved_messages": retrieved_messages,
            "previous_feedback": json.dumps(feedback_by_evaluator) if feedback_by_evaluator else None,
            "tool_result": tool_result_payload,
            "fallback_response": state.voice_client_response if state.voice_client_response else "",
            "iteration_count": feedback.iteration_count if feedback and feedback.iteration_count else 0,
        })
        return res
