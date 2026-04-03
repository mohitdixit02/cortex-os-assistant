from cortex.main.model import CortexMainModel
from cortex.graph.state import ConversationState
from utility.logger import get_logger

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