from cortex_core.main.models.evaluator import CortexEvaluatorModel
from cortex_core.graph.state import (
    ConversationState,
    PlanEvaluationState,
)
from cortex_cm.utility.logger import get_logger

from cortex_core.main.models.evaluator import CortexEvaluatorModel
from cortex_core.graph.state import (
    ConversationState,
    PlanEvaluationState,
)
from cortex_cm.utility.logger import get_logger
from cortex_cm.utility.models import get_heavy_planner_model

class EvaluationOrchestrator:
    def __init__(self):
        self.logger = get_logger("CORTEX_MAIN")
        
    @property
    def evaluation_model(self):
        return CortexEvaluatorModel()

    def evaluate_tools_plan(self, state: ConversationState):
        """
        Evaluate the orchestration plan based on the feedback from the Evaluator. \n
        **Input**: \n
        - `state`: The current conversation state containing the orchestration state and feedback from the Evaluator. \n
        **Returns**: \n
        - Updated conversation state with any necessary modifications to the orchestration plan based on the feedback.
        """
        if (
            state.plan_feedback
            and (state.plan_feedback.iteration_count or 0) > 0
            and not state.plan_feedback.is_tool_selection_feedback_required
        ):
            self.logger.info("Skipping tools plan evaluation for this iteration.")
            return {}

        res = self.evaluation_model.evaluate_orchestration_tools_plan(state)
        self.logger.info("Tools Plan evaluation result: %s", res)
        return {
            "plan_feedback": PlanEvaluationState(
                is_tool_selection_feedback_required=res.is_feedback_required,
                tool_selection_feedback=res.tool_selection_feedback,
            ),
        }

    def evaluate_messages_plan(self, state: ConversationState):
        """
        Evaluate the orchestration plan based on the feedback from the Evaluator. \n
        **Input**: \n
        - `state`: The current conversation state containing the orchestration state and feedback from the Evaluator. \n
        **Returns**: \n
        - Updated conversation state with any necessary modifications to the orchestration plan based on the feedback.
        """
        if (
            state.plan_feedback
            and (state.plan_feedback.iteration_count or 0) > 0
            and not state.plan_feedback.is_message_feedback_required
        ):
            self.logger.info("Skipping messages plan evaluation for this iteration.")
            return {}

        res = self.evaluation_model.evaluate_orchestration_messages_plan(state)
        self.logger.info("Messages Plan evaluation result: %s", res)
        return {
            "plan_feedback": PlanEvaluationState(
                is_message_feedback_required=res.is_feedback_required,
                message_retrieval_feedback=res.message_retrieval_feedback,
            ),
        }
    
    def evaluate_knowledge_plan(self, state: ConversationState):
        """
        Evaluate the orchestration plan based on the feedback from the Evaluator. \n
        **Input**: \n
        - `state`: The current conversation state containing the orchestration state and feedback from the Evaluator. \n
        **Returns**: \n
        - Updated conversation state with any necessary modifications to the orchestration plan based on the feedback.
        """
        if (
            state.plan_feedback
            and (state.plan_feedback.iteration_count or 0) > 0
            and not state.plan_feedback.is_knowledge_feedback_required
        ):
            self.logger.info("Skipping knowledge plan evaluation for this iteration.")
            return {}

        res = self.evaluation_model.evaluate_orchestration_knowledge_plan(state)
        self.logger.info("Knowledge Plan evaluation result: %s", res)
        return {
            "plan_feedback": PlanEvaluationState(
                is_knowledge_feedback_required=res.is_feedback_required,
                user_knowledge_retrieval_feedback=res.user_knowledge_retrieval_feedback,
            ),
        }
 
    def evaluation_aggregator(self, state: ConversationState):
        previous_iteration = state.plan_feedback.iteration_count if state.plan_feedback else 0
        current_feedback = state.plan_feedback or PlanEvaluationState()

        return {
            "plan_feedback": current_feedback.model_copy(update={
                "iteration_count": previous_iteration + 1,
            }),
        }

__all__ = [
    "EvaluationOrchestrator"
]