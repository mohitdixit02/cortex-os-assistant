from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate, HumanMessagePromptTemplate, PromptTemplate
from pydantic import BaseModel, Field
from typing import Annotated, Literal, Any, Dict
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from cortex.graph.state import OrchestrationState, PlanEvaluationState

# Voice Client Route Query
class VoiceClientRouteQuery(BaseModel):
    request_type: Annotated[Literal["casual", "in_depth"], Field(description="Type of the user query")]
    search_required: Annotated[bool, Field(description="Whether the user query requires search or not")]

CORTEX_MAIN_ORCHESTRATOR_PROMPT = """
You are a smart decision planner, given a user query, you have to understand the context based on the following instructions and decide the desried plan. \n

# Input Format:
1. User Query \n
2. STM Summary - Summary of the conversation so far, and the user's preferences or traits extracted from the conversation. Can be null if not available. \n
3. STM Preferences - The extracted preferences of the user from the conversation, which can include their preferred response style, tone, or any specific instructions they have given during the conversation. Can be null if not available. \n
4. User current Mood (from the query) (can be happy, sad, angry, etc.) and Time of the day (Morning, Afternoon, Evening, etc.) - It will help you to understand the user's emotional state based on the time of day. \n
5. User's previous emotional profile (if any else null) - For the above combination of mood and time of the day, it will give you an idea about:
    a. Emotional Level (1-10) - Give you an idea about the intensity of their emotions at that point in time. \n
    b. Logical Level (1-10) - Give you an idea about how logically the user is thinking and how much they are influenced by their emotions. \n
    c. Social Level (1-10) - Give you an idea about how socially active the user is and how much they are influenced by their social interactions. \n
    d. Context Summary - The respective pattern, preferences and behavior summary of the user for that particular combination of mood and time of the day. \n
6. Feedback from the Evaluator (if any) - to make the plan more effective. \n

# Objective:
You have to plan out the following blueprint based on the user query and the context provided above: \n
1. Required User Knowledge Base - \n
    a. Key facts, preferences, traits and behaviours are already captured in the database, but in order to retrieve them, you have to decide the category of that trait.
    b. You can select multiple categories if you think multiple traits are required to be retrieved from the database, but they must be relevant. \n
    c. Feedbacks by Evaluator (inlcude current iteration and past feedback): {user_knowledge_retrieval_feedback}. If feedback is provided, then you have to take that into account while making the plan. \n
    For example, if the feedback asks to add or remove categories, then you have to modify the plan accordingly. \n
    
Available Categories: \n
LIKE - Things that user likes or prefers \n
DISLIKE - Things that user dislikes or does not prefer \n
HABIT - Things that user does regularly or has a habit of doing \n
FACT - Factual information about the user that can be useful for response generation \n
STRICT_PREFERENCE - Strong preferences of the user that should be strictly followed while generating responses \n

2. Messages from Past Conversation - \n
    a. From the user query, you have to understand whether the user is referring to any past message in the conversation or not.
    b. If yes, then you have to generate a relevant text / keywords which have maximum semantic overlap with the referred message, so that it can used to retrieved from the message history. \n
    c. If no, then you can ignore this part and move forward.
    d. Feedbacks by Evaluator (inlcude current iteration and past feedback): {message_retrieval_feedback}. If feedback is provided, then you have to take that into account while making the plan. \n
    For example, if the feedback asks to add more keywords or references, then you have to modify the plan accordingly. \n

3. Is any Tool required?
    a. You will be provided with a list of available tools and their functionalities, you have to decide whether any of these tools are required to process the user query or not.
    b. If yes, then you have to select the relevant tool or tools (multiple tools are also possible if required) \n

# Available Tools: 
{available_tools}

# Input
User Query: {user_query}
STM Summary: {stm_summary}
STM Preferences: {stm_preferences}
User Mood: {user_mood}
User Time of the day: {user_time}
User Previous Emotional Profile: {user_emotional_profile}

# Response
Follow the below format strictly and only respond with the format mentioned without any additional text or explanation. \n
1. For user_knowledge_retrieval_state, only provide the selected categories.
2. For message_retrieval_state, If the user is referring to any past message, then respond with is_referred as true and provide the keywords for message retrieval. If not, then respond with is_referred as false and keep the keywords field empty or null. \n
3. For tool_selection_state, If any tool is required, then respond with is_tool_required as true and provide the Dictinorat of selected tools. If not, then respond with is_tool_required as false and keep the selected_tools field empty or null. \n
{format_instructions}
"""

CORTEX_MAIN_PLAN_EVALUATION_PROMPT = """
# Context:
For a given user query (provided later), the orchestrator has generated a plan. The plan includes the following: \n
1. User Knowledge Retrieval Plan - The plan for retrieving relevant user knowledge from the database. This is done by providing the relevant set of categories (can be multiple). \n

List of Categories: \n
LIKE - Things that user likes or prefers \n
DISLIKE - Things that user dislikes or does not prefer \n
HABIT - Things that user does regularly or has a habit of doing \n
FACT - Factual information about the user that can be useful for response generation \n
STRICT_PREFERENCE - Strong preferences of the user that should be strictly followed while generating responses \n
Based on the plan, data is retrived from the database and is provided later. \n

2. Message Retrieval Plan - The plan for retrieving relevant messages from the past conversation. This is done by providing the keywords for retrieving the relevant messages from the message history. \n
Based on the plan, relevant messages are retrieved from the message history and are provided later. \n

# Objective:
You are a smart evaluator, whose job is to evaluate the plan generated by the Orchestrator based on the user query and the context provided above, and provide the relevant feedback.\n

# Input Format:
1. User Query \n
2. Orchestration Plan - The plan generated by the Orchestrator which includes the user knowledge retrieval plan and message retrieval plan. \n
3. Retrieved User Knowledge - The relevant user knowledge retrieved from the database based on the user knowledge retrieval plan provided by the Orchestrator. \n
4. Retrieved Messages - The relevant messages retrieved from the message history based on the message retrieval plan provided by the Orchestrator. \n
5. List of previous feedbacks provided by you for the same query (if any in past).
6. User current Mood (from the query) (can be happy, sad, angry, etc.) \n
7. User's previous emotional profile (if any else null) -
    a. Emotional Level (1-10) - Give you an idea about the intensity of their emotions at that point in time. \n
    b. Logical Level (1-10) - Give you an idea about how logically the user is thinking and how much they are influenced by their emotions. \n
    c. Social Level (1-10) - Give you an idea about how socially active the user is and how much they are influenced by their social interactions. \n
    d. Context Summary - The respective pattern, preferences and behavior summary of the user for that particular combination of mood and time of the day. \n

# Evaluation Instructions:
1. Evaluate the user query, the orchestration plan and the retrieved data based on the plan. \n
2. Also take into account the previous feedbacks provided by you for the same query (if any provided) and the user's emotional state and preferences. \n
3. Based on this, you have to evaluate and decide the feedback \n

# Feedback Instructions:
### USER KNOWLEDGE BASE \n
    a. Check whether the current retrieved user_knowledge is relevant and sufficient for generating the response. \n
    b. If not, then provide specific feedback on what kind of knowledge is missing or irrelevant. \n
    c. It should include instructions to either add more categories, remove previously selected categories. \n
    d. If its relevant and suffecient, then keep it empty or null. \n
    
### MESSAGE RETRIEVAL \n
    a. Check whether the current retrieved messages are relevant and sufficient for generating the response. \n
    b. If not, then provide specific feedback on what kind of messages are missing or irrelevant. \n
    c. It should include instructions to either add the reference to the message, remove the reference to the message or modify the keywords for message retrieval. \n
    d. If its relevant and suffecient, then keep it empty or null. \n

If you have added any feedback for either of the above two parts, then provide `is_feedback_required` as `True`, else `False`. \n

# Input: \n
User Query: {user_query}
Orchestration Plan: {orchestration_plan}
Retrieved User Knowledge: {retrieved_user_knowledge}
Retrieved Messages: {retrieved_messages}
Previous Feedbacks: {previous_feedback}
User Mood: {user_mood}
User Previous Emotional Profile: {user_emotional_profile}

# Response:
After evaluating the plan, you have to provide the feedback strictly in the below format without any additional text or explanation. \n
{format_instructions}
"""

def get_main_client_prompts(
    type: str,
):
    if type == "main_orchestration":
        parser = PydanticOutputParser(pydantic_object=OrchestrationState)
        prompt = PromptTemplate(
            template=CORTEX_MAIN_ORCHESTRATOR_PROMPT,
            input_variables=[
                "available_tools",
                "user_query",
                "stm_summary",
                "stm_preferences",
                "user_mood",
                "user_time",
                "user_emotional_profile",
                "user_knowledge_retrieval_feedback",
                "message_retrieval_feedback",
                "format_instructions"
            ],
        )
        return prompt.partial(format_instructions=parser.get_format_instructions()), parser
    elif type == "plan_evaluation":
        parser = PydanticOutputParser(pydantic_object=PlanEvaluationState)
        prompt = PromptTemplate(
            template=CORTEX_MAIN_PLAN_EVALUATION_PROMPT,
            input_variables=[
                "user_query",
                "orchestration_plan",
                "retrieved_user_knowledge",
                "retrieved_messages",
                "previous_feedback",
                "user_mood",
                "user_emotional_profile",
                "format_instructions"
            ],
        )
        return prompt.partial(format_instructions=parser.get_format_instructions()), parser
