from typing import Literal
from cortex_core.graph.state import ConversationState

from cortex_core.main.orchestration.evaluator import EvaluationOrchestrator
from cortex_core.main.orchestration.planner import PlanOrchestrator
from cortex_core.main.orchestration.response import ResponseOrchestrator
from cortex_core.main.orchestration.routes import OrchestrationRoutes
from cortex_core.main.orchestration.tools import ToolsOrchestrator

class Orchestrator:
    def __init__(self):
        self.evaluator = EvaluationOrchestrator()
        self.planner = PlanOrchestrator()
        self.response = ResponseOrchestrator()
        self.routes = OrchestrationRoutes()
        self.tools = ToolsOrchestrator()
        
    def main_orchestration(self, state: ConversationState):
        return self.planner.main_orchestration(state)

    def build_knowledge_plan(self, state: ConversationState):
        return self.planner.build_knowledge_plan(state)
        
    def build_messages_plan(self, state: ConversationState):
        return self.planner.build_messages_plan(state)
        
    def build_tools_plan(self, state: ConversationState):
        return self.planner.build_tools_plan(state)
        
    def evaluate_tools_plan(self, state: ConversationState):
        return self.evaluator.evaluate_tools_plan(state)

    def evaluate_messages_plan(self, state: ConversationState):
        return self.evaluator.evaluate_messages_plan(state)
    
    def evaluate_knowledge_plan(self, state: ConversationState):
        return self.evaluator.evaluate_knowledge_plan(state)

    def route_condition_fetch_knowledge(
        self,
        state: ConversationState,
    ) -> Literal["fetch_user_knowledge_base", "skip_knowledge_retrieval"]:
        return self.routes.route_condition_fetch_knowledge(state)
        
    def evaluation_aggregator(self, state: ConversationState):
        return self.evaluator.evaluation_aggregator(state)
    
    def route_condition_orchestration_evaluation(
        self, 
        state: ConversationState
        ) -> Literal["plan_main_orchestration", "route_execute_tools"]:
        return self.routes.route_condition_orchestration_evaluation(state)
        
    def route_condition_fetch_messages(
        self,
        state: ConversationState
    ) -> Literal["fetch_message_history", "skip_message_retrieval"]:
        return self.routes.route_condition_fetch_messages(state)

    def generate_final_response(self, state: ConversationState):
        return self.response.generate_final_response(state)
        
    def align_final_response(self, state: ConversationState):
        return self.response.align_final_response(state)
    
    def route_condition_final_response_evaluation(
        self,
        state: ConversationState
    ) -> Literal["final_response_generation", "terminate"]:
        return self.routes.route_condition_final_response_evaluation(state)

    def execute_tools(
        self,
        state: ConversationState,
    ):
        return self.tools.execute_tools(state)
