from cortex_core.graph.state import ConversationState
from cortex_cm.utility.logger import get_logger
from typing import Literal

MAX_ITERATIONS_LIMIT = 3

class OrchestrationRoutes:
    def __init__(self):
        self.logger = get_logger("CORTEX_MAIN")
        
    def route_condition_fetch_knowledge(
        self,
        state: ConversationState,
    ) -> Literal["fetch_user_knowledge_base", "skip_knowledge_retrieval"]:
        """Skip knowledge retrieval fetch when this branch is not requested in current feedback cycle."""
        if state.plan_feedback and not state.plan_feedback.is_knowledge_feedback_required:
            self.logger.info("Knowledge retrieval is not required this iteration. Skipping fetch_user_knowledge_base.")
            return "skip_knowledge_retrieval"
        return "fetch_user_knowledge_base"
    
    def route_condition_orchestration_evaluation(
        self, 
        state: ConversationState
        ) -> Literal["plan_main_orchestration", "route_execute_tools"]:
        """
        Route the orchestration flow based on the conditions defined in the orchestration state. \n
        **Input**: \n
        - `state`: The current conversation state containing the orchestration state with routing conditions. \n
        **Returns**: \n
        - The next node or step in the workflow to route to based on the conditions evaluated from the orchestration state.
        """
        feedback = state.plan_feedback
        if not state.orchestration_state or not feedback:
            self.logger.info("No orchestration state or plan feedback found. Routing to default response generation.")
            return "route_execute_tools"

        if feedback.iteration_count > MAX_ITERATIONS_LIMIT:
            self.logger.info("Maximum iteration count reached for plan evaluation. Routing to default response generation.")
            return "route_execute_tools"

        requires_feedback = (
            bool(feedback.is_knowledge_feedback_required)
            or bool(feedback.is_message_feedback_required)
            or bool(feedback.is_tool_selection_feedback_required)
        )

        if (requires_feedback):
            self.logger.info("Feedback is required for the current plan. Routing to plan modification.")
            return "plan_main_orchestration"
        else:
            self.logger.info("No feedback required for the current plan. Routing to response generation.")
            return "route_execute_tools"
        
    def route_condition_fetch_messages(
        self,
        state: ConversationState
    ) -> Literal["fetch_message_history", "skip_message_retrieval"]:
        """
        Route the workflow based on whether message retrieval is required or not. \n
        **Input**: \n
        - `state`: The current conversation state containing the orchestration state with message retrieval condition. \n
        **Returns**: \n
        - The next node or step in the workflow to route to based on whether message retrieval is required or not.
        """
        if state.plan_feedback and not state.plan_feedback.is_message_feedback_required:
            self.logger.info("Message retrieval is not required this iteration. Routing to skip_message_retrieval.")
            return "skip_message_retrieval"

        if state.orchestration_state and state.orchestration_state.is_message_referred:
            self.logger.info("Message retrieval is required for the current query. Routing to fetch_message_history.")
            return "fetch_message_history"
        else:
            self.logger.info("Message retrieval is not required for the current query. Routing to skip message retrieval.")
            return "skip_message_retrieval"
    
    def route_condition_final_response_evaluation(
        self,
        state: ConversationState
    ) -> Literal["final_response_generation", "terminate"]:
        """
        Route the workflow based on whether final response evaluation is required or not. \n
        **Input**: \n
        - `state`: The current conversation state containing the final response feedback with evaluation condition. \n
        **Returns**: \n
        - The next node or step in the workflow to route to based on whether final response evaluation is required or not.
        """
        feedback = state.final_response_feedback
        if not feedback:
            self.logger.info("No final response feedback found. Routing to workflow termination.")
            return "terminate"

        if feedback.iteration_count > MAX_ITERATIONS_LIMIT:
            self.logger.info("Maximum iteration count reached for final response evaluation. Routing to workflow termination.")
            return "terminate"
        
        if feedback and feedback.is_feedback_required:
            self.logger.info("Response re-building is required. Routing to final_response_generation.")
            return "final_response_generation"
        else:
            self.logger.info("Final response evaluation is not required. Routing to workflow termination.")
            return "terminate"

__all__ = [
    "OrchestrationRoutes"
]