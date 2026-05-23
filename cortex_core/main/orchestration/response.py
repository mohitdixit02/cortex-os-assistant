from cortex_core.main.models.response import CortexResponseModel
from cortex_core.graph.state import ConversationState
from cortex_cm.utility.logger import get_logger

from cortex_core.main.models.response import CortexResponseModel
from cortex_core.graph.state import ConversationState
from cortex_cm.utility.logger import get_logger
from cortex_cm.utility.models import get_heavy_response_model

class ResponseOrchestrator:
    def __init__(self):
        self.logger = get_logger("CORTEX_MAIN")

    @property
    def response_model(self):
        return CortexResponseModel()

    def generate_final_response(self, state: ConversationState):
        """
        Generate the final response for the user query based on the current conversation state and orchestration plan. \n
        **Input**: \n
        - `state`: The current conversation state containing all relevant information and the orchestration plan. \n
        **Returns**: \n
        - The final response generated for the user query that will be sent back to the user.
        """
        res = self.response_model.generate_final_response(state)
        self.logger.info("Final response generated: %s", res)
        state.final_response = res
        return {
            "final_response": state.final_response,
        }
        
    def align_final_response(self, state: ConversationState):
        """
        Align the final response with the user's emotional profile and preferences. \n
        **Input**: \n
        - `state`: The current conversation state containing the generated final response and the user's emotional profile and preferences. \n
        **Returns**: \n
        - The aligned final response that takes into account the user's emotional state and preferences for a more personalized response.
        """
        res = self.response_model.evaluate_final_response(state)
        self.logger.info("Final response aligned: %s", res)
        
        previous_feedback = state.final_response_feedback
        previous_iteration = previous_feedback.iteration_count if previous_feedback else 0

        merged_final_response_feedback = []
        if previous_feedback and previous_feedback.feedback:
            merged_final_response_feedback.extend(previous_feedback.feedback)
        if res.feedback:
            merged_final_response_feedback.extend(res.feedback)
            
        state.final_response_feedback = res.model_copy(update={
            "feedback": merged_final_response_feedback or None, 
            "iteration_count": previous_iteration + 1,
        })
        
        return {
            "final_response_feedback": state.final_response_feedback,
        }

__all__ = [
    "ResponseOrchestrator"
]