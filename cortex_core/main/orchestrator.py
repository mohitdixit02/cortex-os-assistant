from cortex_core.main.model import CortexMainModel
from cortex_core.graph.state import (
    ConversationState, 
    MemoryState, 
    MemoryEmotionalProfile, 
    EmotionalProfile, 
    FinalResponseGenerationState,
    OrchestrationState, 
    PlanEvaluationState,
    CortexToolList, 
    CortexTool,
    ToolManagerState,
    WebSearchToolState, 
    TaskRetrieverToolState
)
from cortex_core.manager.tools import AvailableToolsType, WebSearchTool, WebSearchInput
from cortex_core.graph.manager import tool_manager_workflow
from cortex_cm.utility.logger import get_logger
from typing import Literal

MAX_ITERATIONS_LIMIT = 3

class Orchestrator:
    def __init__(self):
        self.model = CortexMainModel()
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
        
        revised_plan = self.model.build_main_orchestration_plan(state)
        self.logger.info("Revised orchestration plan generated: %s", revised_plan)
        revised_plan_feedback = state.plan_feedback.model_copy(update={
            "is_knowledge_feedback_required": revised_plan.is_knowledge_plan_refinement_required,
            "is_message_feedback_required": revised_plan.is_message_plan_refinement_required,
            "is_tool_selection_feedback_required": revised_plan.is_tool_selection_plan_refinement_required,
        }) if state.plan_feedback else None
        
        return {
            "plan_feedback": revised_plan_feedback
        }

    # def route_main_orchestration(
    #     self,
    #     state: ConversationState,
    # ) -> Literal["build_knowledge_plan", "build_messages_plan", "build_tools_plan", "route_execute_tools"] | list[str]:
    #     feedback = state.plan_feedback
    #     if not feedback:
    #         self.logger.info("No prior feedback found. Routing all planning branches.")
    #         return ["build_knowledge_plan", "build_messages_plan", "build_tools_plan"]

    #     # routes = []
    #     # if feedback.is_knowledge_feedback_required:
    #     #     routes.append("build_knowledge_plan")
    #     # if feedback.is_message_feedback_required:
    #     #     routes.append("build_messages_plan")
    #     # if feedback.is_tool_selection_feedback_required:
    #     #     routes.append("build_tools_plan")
        
    #     if (bool(feedback.is_knowledge_feedback_required) or 
    #     bool(feedback.is_message_feedback_required) or 
    #     bool(feedback.is_tool_selection_feedback_required)):
    #         self.logger.info("Feedback requested for branches %s; routing all planning branches for stable join semantics.")
    #         return ["build_knowledge_plan", "build_messages_plan", "build_tools_plan"]
            
    #     # if routes:

    #     self.logger.info("No plan branch requires rebuild. Routing to final response generation.")
    #     return "route_execute_tools"

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

        res = self.model.build_main_orchestration_knowledge_plan(state)
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

        res = self.model.build_main_orchestration_messages_plan(state)
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

        res = self.model.build_main_orchestration_tools_plan(state)
        self.logger.info("Tools orchestration plan generated: %s", res)
        return {
            "orchestration_state": OrchestrationState(
                is_tool_required=res.is_tool_required,
                selected_tools=res.selected_tools,
            ),
        }
        
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

        res = self.model.evaluate_orchestration_tools_plan(state)
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

        res = self.model.evaluate_orchestration_messages_plan(state)
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

        res = self.model.evaluate_orchestration_knowledge_plan(state)
        self.logger.info("Knowledge Plan evaluation result: %s", res)
        return {
            "plan_feedback": PlanEvaluationState(
                is_knowledge_feedback_required=res.is_feedback_required,
                user_knowledge_retrieval_feedback=res.user_knowledge_retrieval_feedback,
            ),
        }

    def route_condition_fetch_knowledge(
        self,
        state: ConversationState,
    ) -> Literal["fetch_user_knowledge_base", "skip_knowledge_retrieval"]:
        """Skip knowledge retrieval fetch when this branch is not requested in current feedback cycle."""
        if state.plan_feedback and not state.plan_feedback.is_knowledge_feedback_required:
            self.logger.info("Knowledge retrieval is not required this iteration. Skipping fetch_user_knowledge_base.")
            return "skip_knowledge_retrieval"
        return "fetch_user_knowledge_base"
        
    def evaluation_aggregator(self, state: ConversationState):
        previous_iteration = state.plan_feedback.iteration_count if state.plan_feedback else 0
        current_feedback = state.plan_feedback or PlanEvaluationState()

        return {
            "plan_feedback": current_feedback.model_copy(update={
                "iteration_count": previous_iteration + 1,
            }),
        }
    
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

        if feedback.iteration_count > MAX_ITERATIONS_LIMIT:
            self.logger.info("Maximum iteration count reached for final response evaluation. Routing to workflow termination.")
            return "terminate"
        
        if feedback and feedback.is_feedback_required:
            self.logger.info("Response re-building is required. Routing to final_response_generation.")
            return "final_response_generation"
        else:
            self.logger.info("Final response evaluation is not required. Routing to workflow termination.")
            return "terminate"

    def execute_tools(
        self,
        state: ConversationState,
    ):
        orchestration_state = state.orchestration_state
        
        if orchestration_state is None:
            self.logger.warning("No orchestration state found in the conversation state. Skipping tool execution.")
            return {}
    
        if orchestration_state.is_tool_required is False:
            self.logger.info("No tool is required for the current query as per the orchestration state. Skipping tool execution.")
            return {}
        
        selected_tools = orchestration_state.selected_tools
        selected_tools_list = selected_tools.root if hasattr(selected_tools, "root") else selected_tools
        
        tool_manager_state = ToolManagerState(
            user_id=state.user_id,
            session_id=state.session_id,
            task_id=state.task_id,
            query=state.query,
        )
        
        for tool in selected_tools_list:
            if isinstance(tool, CortexTool):
                if tool.tool_id == AvailableToolsType.WEB_SEARCH_TOOL.value:
                    tool_manager_state.web_search_tool = WebSearchToolState(
                        instructions=tool.instructions,
                    )
                if tool.tool_id == AvailableToolsType.TASK_RETRIEVER_TOOL.value:
                    tool_manager_state.task_retriever_tool = TaskRetrieverToolState(
                        instructions=tool.instructions,
                    )
            else:
                self.logger.warning(f"Invalid tool format: {tool}. Skipping this tool.")
        
        #  manager execute tools workflow
        res = tool_manager_workflow.invoke(tool_manager_state)
        res = ToolManagerState.model_validate(res)
        self.logger.info("[ORCHESTRATOR] Tools execution completed with results: %s", res)
        tools_result = []
        if res.web_search_tool:
            tools_result.append(CortexTool(
                tool_id=AvailableToolsType.WEB_SEARCH_TOOL.value,
                instructions=res.web_search_tool.instructions,
                tool_result=res.web_search_tool.tool_result,
                tool_exec_status=res.web_search_tool.tool_exec_status
            ))
        if res.task_retriever_tool:
            tools_result.append(CortexTool(
                tool_id=AvailableToolsType.TASK_RETRIEVER_TOOL.value,
                instructions=res.task_retriever_tool.instructions,
                tool_result=res.task_retriever_tool.tool_result,
                tool_exec_status=res.task_retriever_tool.tool_exec_status
            ))
            
        orchestration_state.selected_tools = CortexToolList(root=tools_result)
        return {
            "orchestration_state": orchestration_state,
        }
