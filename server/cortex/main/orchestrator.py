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

        previous_feedback = state.plan_feedback
        previous_iteration = previous_feedback.iteration_count if previous_feedback else 0

        merged_user_knowledge_feedback = []
        if previous_feedback and previous_feedback.user_knowledge_retrieval_feedback:
            merged_user_knowledge_feedback.extend(previous_feedback.user_knowledge_retrieval_feedback)
        if res.user_knowledge_retrieval_feedback:
            merged_user_knowledge_feedback.extend(res.user_knowledge_retrieval_feedback)

        merged_message_feedback = []
        if previous_feedback and previous_feedback.message_retrieval_feedback:
            merged_message_feedback.extend(previous_feedback.message_retrieval_feedback)
        if res.message_retrieval_feedback:
            merged_message_feedback.extend(res.message_retrieval_feedback)

        state.plan_feedback = res.model_copy(update={
            "user_knowledge_retrieval_feedback": merged_user_knowledge_feedback or None,
            "message_retrieval_feedback": merged_message_feedback or None,
            "iteration_count": previous_iteration + 1,
        })

        return {
            "plan_feedback": state.plan_feedback,
        }
    
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
        feedback = state.plan_feedback
        if not state.orchestration_state or not feedback:
            self.logger.info("No orchestration state or plan feedback found. Routing to default response generation.")
            return "build_memory_workflow"

        if feedback.iteration_count >= 3:
            self.logger.info("Maximum iteration count reached for plan evaluation. Routing to default response generation.")
            return "build_memory_workflow"
        
        if feedback.is_feedback_required:
            self.logger.info("Feedback is required for the current plan. Routing to plan modification.")
            return "plan_main_orchestration"
        else:
            self.logger.info("No feedback required for the current plan. Routing to response generation.")
            return "build_memory_workflow"
        
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