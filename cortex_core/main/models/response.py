from cortex_core.graph.state import ConversationState
from cortex_cm.utility.logger import get_logger
import json
from cortex_cm.utility.models import get_heavy_response_model
from cortex_core.main.prompts import get_main_orchestrator_res_prompt
from .utility import serialize_tool_results

class CortexResponseModel:
    def __init__(self):
        self.logger = get_logger("CORTEX_MAIN")
        self.heavy_response_model = get_heavy_response_model()
    
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
                retrieved_messages += f"{msg.role.value}: {msg.content}\n"
        else:
            retrieved_messages = None
            
        feedback = state.final_response_feedback
        if feedback:
            feedback_by_evaluator = feedback.model_dump()
        else:
            feedback_by_evaluator = None
            
        tool_result_payload = serialize_tool_results(state)
        
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
                retrieved_messages += f"{msg.role.value}: {msg.content}\n"
        else:
            retrieved_messages = None
            
        feedback = state.final_response_feedback
        if feedback:
            feedback_by_evaluator = feedback.model_dump()
        else:
            feedback_by_evaluator = None
        
        tool_result_payload = serialize_tool_results(state)
        
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
