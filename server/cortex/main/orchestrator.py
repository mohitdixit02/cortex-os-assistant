from cortex.main.model import CortexMainModel
from cortex.graph.state import ConversationState
from utility.logger import get_logger
from langgraph.graph import END
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
        self.model.build_main_orchestration_plan(state)
        return state
    
    def evaluate_plan(self, state: ConversationState):
        """
        Evaluate the orchestration plan based on the feedback from the Evaluator. \n
        **Input**: \n
        - `state`: The current conversation state containing the orchestration state and feedback from the Evaluator. \n
        **Returns**: \n
        - Updated conversation state with any necessary modifications to the orchestration plan based on the feedback.
        """
        self.model.evaluate_orchestration_plan(state)
        return state
    
    def route_condition_orchestration_evaluation(
        self, 
        state: ConversationState
        ) -> Literal["plan_main_orchestration", "build_memory_workflow"]:
        """
        Route the orchestration flow based on the conditions defined in the orchestration state. \n
        **Input**: \n
        - `state`: The current conversation state containing the orchestration state with routing conditions. \n
        **Returns**: \n
        - The next node or step in the workflow to route to based on the conditions evaluated from the orchestration state.
        """
        orchestration_state = state.orchestration_state
        if not orchestration_state or not orchestration_state.feedback_by_evaluator:
            # /pending/ Why this case is printing
            self.logger.info("No orchestration state or feedback by evaluator found. Routing to default response generation.")
            return "build_memory_workflow"
        
        feedback = orchestration_state.feedback_by_evaluator
        if feedback.iteration_count >= 3:
            self.logger.info("Maximum iteration count reached for plan evaluation. Routing to default response generation.")
            return "build_memory_workflow"
        
        if feedback.is_feedback_required:
            self.logger.info("Feedback is required for the current plan. Routing to plan modification.")
            return "plan_main_orchestration"
        else:
            self.logger.info("No feedback required for the current plan. Routing to response generation.")
            return "build_memory_workflow"