from cortex_core.graph.state import ConversationState, OrchestrationState
from cortex_cm.utility.logger import get_logger
from cortex_core.manager.tools import AVAILABLE_TOOLS
from cortex_cm.utility.models import get_heavy_planner_model
from cortex_core.main.prompts import get_main_orchestrator_evaluate_prompt
from cortex_core.main.prompts.main_evaluator import (
    InternalFeedbackKnowledge,
    InternalFeedbackMessages,
    InternalFeedbackTools,
)

class CortexEvaluatorModel:
    def __init__(self):
        self.logger = get_logger("CORTEX_MAIN")
        self.heavy_plan_model = get_heavy_planner_model()
    
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
                retrieved_messages += f"{msg.role.value}: {msg.content}\n"
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
                retrieved_messages += f"{msg.role.value}: {msg.content}\n"
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
