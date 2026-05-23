from cortex_core.main.models.planner import CortexPlannerModel
from cortex_core.graph.state import (
    ConversationState,
    OrchestrationState
)
from cortex_cm.utility.logger import get_logger

class PlanOrchestrator:
    def __init__(self):
        self.planner_model = CortexPlannerModel()
        self.logger = get_logger("CORTEX_MAIN")
        
    def main_orchestration(self, state: ConversationState):
        """Graph node placeholder for the orchestration stage.

        Routing is handled by `route_main_orchestration` via conditional edges.
        """
        self.logger.info("Entering main orchestration node.")
        
        iteration = state.plan_feedback.iteration_count if state.plan_feedback else 0
        self.logger.info(f"Current iteration count for orchestration: {iteration}")
        
        if iteration == 0:
            self.logger.info("Initial iteration of orchestration. Routing to build all plans.")
            return {}
        
        revised_plan = self.planner_model.build_main_orchestration_plan(state)
        self.logger.info("Revised orchestration plan generated: %s", revised_plan)
        revised_plan_feedback = state.plan_feedback.model_copy(update={
            "is_knowledge_feedback_required": revised_plan.is_knowledge_plan_refinement_required,
            "is_message_feedback_required": revised_plan.is_message_plan_refinement_required,
            "is_tool_selection_feedback_required": revised_plan.is_tool_selection_plan_refinement_required,
        }) if state.plan_feedback else None
        
        return {
            "plan_feedback": revised_plan_feedback
        }

    def build_knowledge_plan(self, state: ConversationState):
        """
        Build the orchestration plan for the main workflow based on the current conversation state. \n
        **Input**: \n
        - `state`: The current conversation state containing all relevant information about the user query, emotional profile, short term memory, etc. \n
        **Returns**: \n
        - The orchestration plan or prompt that will guide the main workflow in processing the query and generating a response.
        """
        if state.plan_feedback and not state.plan_feedback.is_knowledge_feedback_required:
            self.logger.info("Skipping knowledge plan rebuild for this iteration.")
            return {}

        res = self.planner_model.build_main_orchestration_knowledge_plan(state)
        self.logger.info("Knowledge Orchestration plan generated: %s", res)
        return {
            "orchestration_state": OrchestrationState(
                user_knowledge_retrieval_keywords=res.user_knowledge_retrieval_keywords,
                user_knowledge_acceptance_threshold=res.user_knowledge_acceptance_threshold,
            ),
        }
        
    def build_messages_plan(self, state: ConversationState):
        """
        Build the orchestration plan for the main workflow based on the current conversation state. \n
        **Input**: \n
        - `state`: The current conversation state containing all relevant information about the user query, emotional profile, short term memory, etc. \n
        **Returns**: \n
        - The orchestration plan or prompt that will guide the main workflow in processing the query and generating a response.
        """
        if state.plan_feedback and not state.plan_feedback.is_message_feedback_required:
            self.logger.info("Skipping messages plan rebuild for this iteration.")
            return {}

        res = self.planner_model.build_main_orchestration_messages_plan(state)
        self.logger.info("Messages Orchestration plan generated: %s", res)
        return {
            "orchestration_state": OrchestrationState(
                is_message_referred=res.is_message_referred,
                referred_message_keywords=res.referred_message_keywords,
            ),
        }
        
    def build_tools_plan(self, state: ConversationState):
        """
        Build the orchestration plan specifically for tool selection and execution based on the current conversation state. \n
        **Input**: \n
        - `state`: The current conversation state containing all relevant information about the user query, emotional profile, short term memory, orchestration state, etc. \n
        **Returns**: \n
        - The orchestration plan or prompt that will guide the tool selection and execution workflow in processing the query and generating a response.
        """
        if state.plan_feedback and not state.plan_feedback.is_tool_selection_feedback_required:
            self.logger.info("Skipping tools plan rebuild for this iteration.")
            return {}

        res = self.planner_model.build_main_orchestration_tools_plan(state)
        self.logger.info("Tools orchestration plan generated: %s", res)
        return {
            "orchestration_state": OrchestrationState(
                is_tool_required=res.is_tool_required,
                selected_tools=res.selected_tools,
            ),
        }

__all__ = [
    "PlanOrchestrator"
]
