from cortex_core.graph.state import ConversationState
from cortex_cm.utility.logger import get_logger
from cortex_core.manager.tools import AVAILABLE_TOOLS
import json
from cortex_cm.utility.cortex import (
    get_heavy_planner_model,
    get_main_orchestrator_model
)
from cortex_core.main.prompts import get_main_orchestrator_plan_prompt
from cortex_core.main.prompts.main_planner import (
    InternalPlanKnowledge,
    InternalPlanMessages,
    InternalPlanTools,
)
from cortex_core.main.prompts.orchestrator import MainOrchestrationDecision

class CortexPlannerModel:
    def __init__(self):
        self.logger = get_logger("CORTEX_MAIN")
        self.heavy_plan_model = get_heavy_planner_model()
        self.main_orchestrator_model = get_main_orchestrator_model()
      
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
                retrieved_messages += f"{msg.role.value}: {msg.content}\n"
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
                retrieved_messages += f"{msg.role.value}: {msg.content}\n"
        else:
            retrieved_messages = None
        
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
            "timestamp": state.query_timestamp,
        })
        return res
