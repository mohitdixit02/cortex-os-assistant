from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from cortex_core.graph.state import OrchestrationState, PlanEvaluationState, FinalResponseFeedbackState, FinalResponseGenerationState
from cortex_core.main.prompts.main_evaluator import (
    CORTEX_MAIN_KNOWLEDGE_EVALUATION_PROMPT,
    CORTEX_MAIN_MESSAGE_EVALUATION_PROMPT,
    CORTEX_MAIN_TOOL_EVALUATION_PROMPT,
    InternalFeedbackKnowledge,
    InternalFeedbackMessages,
    InternalFeedbackTools,
)
from cortex_core.main.prompts.main_planner import (
    CORTEX_MAIN_ORCHESTRATOR_KNOWLEDGE_PROMPT,
    CORTEX_MAIN_ORCHESTRATOR_MESSAGES_PROMPT,
    CORTEX_MAIN_ORCHESTRATOR_TOOLS_PROMPT,
    InternalPlanKnowledge,
    InternalPlanMessages,
    InternalPlanTools,
)

from cortex_core.main.prompts.response import (
    CORTEX_MAIN_FINAL_RESPONSE_PROMPT,
    CORTEX_MAIN_FINAL_RESPONSE_EVALUATION_PROMPT,
)

from cortex_core.main.prompts.orchestrator import (
    CORTEX_MAIN_ORCHESTRATION_PROMPT,
    MainOrchestrationDecision,
)

def get_main_orchestrator_plan_prompt(
    type: str,
):
    if type == "main_orchestration":
        parser = PydanticOutputParser(pydantic_object=MainOrchestrationDecision)
        prompt = PromptTemplate(
            template=CORTEX_MAIN_ORCHESTRATION_PROMPT,
            input_variables=[
                "knowledge_plan_builder_output",
                "conversation_history_plan_builder_output",
                "tool_selection_plan_builder_output",
                "retrieved_user_knowledge",
                "retrieved_messages",
                "knowledge_plan_builder_feedback",
                "conversation_history_plan_builder_feedback",
                "tool_selection_feedback",
                "user_query",
                "stm_summary",
                "stm_preferences",
                "available_tools",
                "iteration_count",
                "format_instructions"
            ],
        )
        return prompt.partial(format_instructions=parser.get_format_instructions()), parser
    elif type == "main_orchestration_knowledge":
        parser = PydanticOutputParser(pydantic_object=InternalPlanKnowledge)
        prompt = PromptTemplate(
            template=CORTEX_MAIN_ORCHESTRATOR_KNOWLEDGE_PROMPT,
            input_variables=[
                "user_query",
                "stm_summary",
                "stm_preferences",
                "user_mood",
                "user_time",
                "user_emotional_profile",
                "user_knowledge_retrieval_feedback",
                "format_instructions"
            ],
        )
        return prompt.partial(format_instructions=parser.get_format_instructions()), parser
    elif type == "main_orchestration_messages":
        parser = PydanticOutputParser(pydantic_object=InternalPlanMessages)
        prompt = PromptTemplate(
            template=CORTEX_MAIN_ORCHESTRATOR_MESSAGES_PROMPT,
            input_variables=[
                "user_query",
                "stm_summary",
                "stm_preferences",
                "user_mood",
                "user_time",
                "retrieved_user_knowledge",
                "message_retrieval_feedback",
                "format_instructions"
            ],
        )
        return prompt.partial(format_instructions=parser.get_format_instructions()), parser
    elif type == "main_orchestration_tools":
        parser = PydanticOutputParser(pydantic_object=InternalPlanTools)
        prompt = PromptTemplate(
            template=CORTEX_MAIN_ORCHESTRATOR_TOOLS_PROMPT,
            input_variables=[
                "available_tools",
                "user_query",
                "stm_summary",
                "stm_preferences",
                "user_mood",
                "user_time",
                "user_emotional_profile",
                "retrieved_user_knowledge",
                "retrieved_messages",
                "tool_selection_feedback",
                "format_instructions",
                "iteration_count"
                "timestamp"
            ],
        )
        return prompt.partial(format_instructions=parser.get_format_instructions()), parser
    
def get_main_orchestrator_evaluate_prompt(
    type: str,
):
    if type == "plan_evaluation_knowledge":
        parser = PydanticOutputParser(pydantic_object=InternalFeedbackKnowledge)
        prompt = PromptTemplate(
            template=CORTEX_MAIN_KNOWLEDGE_EVALUATION_PROMPT,
            input_variables=[
                "user_query",
                "orchestration_plan",
                "retrieved_user_knowledge",
                "previous_feedback",
                "user_mood",
                "user_emotional_profile",
                "format_instructions"
            ],
        )
        return prompt.partial(format_instructions=parser.get_format_instructions()), parser
    elif type == "plan_evaluation_messages":
        parser = PydanticOutputParser(pydantic_object=InternalFeedbackMessages)
        prompt = PromptTemplate(
            template=CORTEX_MAIN_MESSAGE_EVALUATION_PROMPT,
            input_variables=[
                "user_query",
                "orchestration_plan",
                "retrieved_messages",
                "previous_feedback",
                "user_mood",
                "retrieved_user_knowledge",
                "format_instructions"
            ],
        )
        return prompt.partial(format_instructions=parser.get_format_instructions()), parser
    elif type == "plan_evaluation_tools":
        parser = PydanticOutputParser(pydantic_object=InternalFeedbackTools)
        prompt = PromptTemplate(
            template=CORTEX_MAIN_TOOL_EVALUATION_PROMPT,
            input_variables=[
                "user_query",
                "orchestration_plan",
                "previous_feedback",
                "user_mood",
                "user_emotional_profile",
                "available_tools",
                "retrieved_user_knowledge",
                "retrieved_messages",
                "format_instructions"
            ],
        )
        return prompt.partial(format_instructions=parser.get_format_instructions()), parser
    
def get_main_orchestrator_res_prompt(
    type: str,
):
    if type == "final_response_generation":
        parser = PydanticOutputParser(pydantic_object=FinalResponseGenerationState)
        prompt = PromptTemplate(
            template=CORTEX_MAIN_FINAL_RESPONSE_PROMPT,
            input_variables=[
                "user_query",
                "stm_summary",
                "stm_preferences",
                "user_mood",
                "user_time",
                "user_emotional_profile",
                "retrieved_user_knowledge",
                "retrieved_messages",
                "previous_feedback",
                "tool_result",
                "fallback_response",
                "format_instructions"
            ],
        )
        return prompt.partial(format_instructions=parser.get_format_instructions()), parser
    elif type == "final_response_evaluation":
        parser = PydanticOutputParser(pydantic_object=FinalResponseFeedbackState)
        prompt = PromptTemplate(
            template=CORTEX_MAIN_FINAL_RESPONSE_EVALUATION_PROMPT,
            input_variables=[
                "user_query",
                "final_response",
                "stm_summary",
                "stm_preferences",
                "user_mood",
                "user_time",
                "user_emotional_profile",
                "retrieved_user_knowledge",
                "retrieved_messages",
                "previous_feedback",
                "tool_result",
                "fallback_response",
                "iteration_count", 
                "format_instructions"
            ],
        )
        return prompt.partial(format_instructions=parser.get_format_instructions()), parser
    
