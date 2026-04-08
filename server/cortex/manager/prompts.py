from cortex.manager.tools import WebSearchInput
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from typing import Annotated, Literal, Any, Dict
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from cortex.graph.state import OrchestrationState, PlanEvaluationState, FinalResponseFeedbackState, FinalResponseGenerationState

MANAGER_WEB_QUERY_PROMPT = """
# Context: \n
You are a smart query planner for the web search tool. 

# Input Format: \n
1. User Query: Question or information or suggestion from the user that requires web search. \n
2. Instructions by Orchestrator: Additional instructions or constraints provided by the orchestrator to guide the query planning. (can be null) \n

# Task: \n
Based on the user query and the instructions by orchestrator, you have to give a list of relevant queries which can be used for web search.

# Instructions: \n
1. Each query should be relevant enough to search for.
2. Strictly follow the orchestrator instructions if provided. If no instructions are provided, generate queries based on the user query alone.
3. Similar Queries must be grouped together while each query in the list should be different from other queries to cover different aspects.
4. Give atleast one query and at max five queries in the output list.

# Input:
User Query: {user_query}
Instructions by Orchestrator: {orchestrator_instructions}

# Output Format: \n
A list of relevant queries (strings) to be used for web search. Follow the below format strictly. Never include any explanations, additional text, python functions, etc in the response. \n
{format_instructions}
"""

def get_manager_client_prompts(
    type: str,
):
    if type == "web_query_planning":
        parser = PydanticOutputParser(pydantic_object=WebSearchInput)
        prompt = PromptTemplate(
            template=MANAGER_WEB_QUERY_PROMPT,
            input_variables=[
                "user_query",
                "orchestrator_instructions",
                "format_instructions"
            ],
        )
        return prompt.partial(format_instructions=parser.get_format_instructions()), parser

