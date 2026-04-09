from cortex.manager.tools import WebSearchInput
from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field
from typing import Annotated, Literal, Any, Dict, Optional
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from cortex.graph.state import OrchestrationState, PlanEvaluationState, FinalResponseFeedbackState, FinalResponseGenerationState
from cortex.manager.tools import AvailableToolsType

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

TOOL_RESULT_SUMMARIZATION_PROMPT = """
# Input Format: \n
You will be given: \n
1. User Query: Question or information or suggestion from the user. \n
2. Tool Result: To get relevant info, a respective tool is executed and its result is given as input to you. \n
3. Tool Instructions: Additional Instructions specific to the tool. \n

# Input: \n
User Query: {user_query}
Tool Result: {tool_result}

# Tool Specific instructions: \n
{tool_instructions}

# Objective: \n
1. Based on the user query, tool result and specifictool instructions, you have to extract the core facts that answer the user's query. \n
2. Rewrite them as relevant sentences of 10-12 lines (no html tags, json, python functions, etc.). \n
2. Make sure no important information got missed from the tool result while re-organizing facts. \n
3. Your response is later used by the response generator to generate the final response for the user query, so it should be relevant and useful. \n
4. If the tool result is empty, reply with an empty string. Never create any information on your own. \n

# Response Format: \n
String of Relevant sentences, with no extra explanation, text, formatting, python function, etc. Just the concise summary string.
"""

WEB_TOOL_SPECIFIC_INSTRUCTIONS = """
The tool used is Web Search Tool. The tool result will contain concatenated content of multiple web documents. All the Web Documents are relevant. \n
# Instructions:
1. Some of the content might have repeative data, so make sure to not include repeative information. \n
2. Make sure that user query is fully addressed in the summary and no relevant information is missed. \n
"""
def get_manager_client_prompts(
    type: str,
    tool_type: Optional[str] = None,
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
    elif type == "tool_result_summarization":
        parser = StrOutputParser()
        prompt = PromptTemplate(
            template=TOOL_RESULT_SUMMARIZATION_PROMPT,
            input_variables=[
                "user_query",
                "tool_result",
                "tool_instructions"
            ],
        )
        if not tool_type:
            return prompt.partial(tool_instructions=""), parser
        
        if tool_type == AvailableToolsType.WEB_SEARCH_TOOL.value:
            return prompt.partial(tool_instructions=WEB_TOOL_SPECIFIC_INSTRUCTIONS), parser


