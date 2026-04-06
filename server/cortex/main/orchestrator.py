from cortex.main.model import CortexMainModel
from cortex.graph.state import ConversationState
from utility.logger import get_logger
from typing import Literal

class Orchestrator:
    def __init__(self):
        self.model = CortexMainModel()
        self.logger = get_logger("CORTEX_MAIN")

    def build_main_orchestration_plan(self, state: ConversationState):
        """
        Build the orchestration plan for the main workflow based on the current conversation state. \n
        **Input**: \n
        - `state`: The current conversation state containing all relevant information about the user query, emotional profile, short term memory, etc. \n
        **Returns**: \n
        - The orchestration plan or prompt that will guide the main workflow in processing the query and generating a response.
        """
        res = self.model.build_main_orchestration_plan(state)
        self.logger.info("Orchestration plan generated: %s", res)
        state.orchestration_state = res
        return {
            "orchestration_state": state.orchestration_state,
        }
    
    def evaluate_plan(self, state: ConversationState):
        """
        Evaluate the orchestration plan based on the feedback from the Evaluator. \n
        **Input**: \n
        - `state`: The current conversation state containing the orchestration state and feedback from the Evaluator. \n
        **Returns**: \n
        - Updated conversation state with any necessary modifications to the orchestration plan based on the feedback.
        """
        res = self.model.evaluate_orchestration_plan(state)
        self.logger.info("Plan evaluation result: %s", res)

        # Iteration count update
        previous_feedback = state.plan_feedback
        previous_iteration = previous_feedback.iteration_count if previous_feedback else 0

        state.plan_feedback = res.model_copy(update={
            "iteration_count": previous_iteration + 1,
        })

        return {
            "plan_feedback": state.plan_feedback,
        }
    
    def route_condition_orchestration_evaluation(
        self, 
        state: ConversationState
        ) -> Literal["plan_main_orchestration", "final_response_generation"]:
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
            return "final_response_generation"

        if feedback.iteration_count >= 3:
            self.logger.info("Maximum iteration count reached for plan evaluation. Routing to default response generation.")
            return "final_response_generation"
        
        if feedback.is_feedback_required:
            self.logger.info("Feedback is required for the current plan. Routing to plan modification.")
            return "plan_main_orchestration"
        else:
            self.logger.info("No feedback required for the current plan. Routing to response generation.")
            return "final_response_generation"
        
    def route_condition_fetch_messages(
        self,
        state: ConversationState
    ) -> Literal["fetch_message_history", "plan_evaluation"]:
        """
        Route the workflow based on whether message retrieval is required or not. \n
        **Input**: \n
        - `state`: The current conversation state containing the orchestration state with message retrieval condition. \n
        **Returns**: \n
        - The next node or step in the workflow to route to based on whether message retrieval is required or not.
        """
        if state.orchestration_state and state.orchestration_state.is_message_referred:
            self.logger.info("Message retrieval is required for the current query. Routing to fetch_message_history.")
            return "fetch_message_history"
        else:
            self.logger.info("Message retrieval is not required for the current query. Routing to plan evaluation.")
            return "plan_evaluation"
        
    def generate_final_response(self, state: ConversationState):
        """
        Generate the final response for the user query based on the current conversation state and orchestration plan. \n
        **Input**: \n
        - `state`: The current conversation state containing all relevant information and the orchestration plan. \n
        **Returns**: \n
        - The final response generated for the user query that will be sent back to the user.
        """
        res = self.model.generate_final_response(state)
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
        res = self.model.evaluate_final_response(state)
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

        if feedback.iteration_count >= 3:
            self.logger.info("Maximum iteration count reached for final response evaluation. Routing to workflow termination.")
            return "terminate"
        
        if feedback and feedback.is_feedback_required:
            self.logger.info("Response re-building is required. Routing to final_response_generation.")
            return "final_response_generation"
        else:
            self.logger.info("Final response evaluation is not required. Routing to workflow termination.")
            return "terminate"
