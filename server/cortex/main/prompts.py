from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate, HumanMessagePromptTemplate, PromptTemplate
from pydantic import BaseModel, Field
from typing import Annotated, Literal, Any, Dict
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from cortex.graph.state import OrchestrationState, PlanEvaluationState, FinalResponseFeedbackState, FinalResponseGenerationState

# Voice Client Route Query
class VoiceClientRouteQuery(BaseModel):
    request_type: Annotated[Literal["casual", "in_depth"], Field(description="Type of the user query")]
    search_required: Annotated[bool, Field(description="Whether the user query requires search or not")]

CORTEX_MAIN_ORCHESTRATOR_PROMPT = """
# Input Format:
1. User Query \n
2. STM Summary - Summary of the conversation so far, and the user's preferences or traits extracted from the conversation. Can be null if not available. \n
3. STM Preferences - The extracted preferences of the user from the conversation, which can include their preferred response style, tone, or any specific instructions. Can be null if not available. \n
4. User current Mood (from the query) (can be happy, sad, angry, etc.) and Time of the day (Morning, Afternoon, Evening, etc.) - Help you to understand the user's emotional state based on the time of day. \n
5. User's previous emotional profile (if any else null) - For the above combination of mood and time of the day, it will give you an idea about:
    a. Emotional Level (1-10) - Intensity of user emotions at that point of time and how much they prefer emotional responses \n
    b. Logical Level (1-10) - How logically the user thinks and prefers logical discussions. \n
    c. Social Level (1-10) - How socially active the user is and how much they are influenced by their social interactions.
    d. Context Summary - The respective pattern, preferences and behavior summary of the user for that particular combination of mood and time of the day. \n
6. Feedback from the Evaluator (if any) - to make the plan more effective. \n

# Objective:
You are a smart decision planner, given a user query, you have to understand the user query, context provided based on all the input fields and instructions, plan out the blueprint and decide below things: \n

# Blueprint:
1. user_knowledge_retrieval_keywords - \n
    a. Key facts, preferences, traits and behaviours for the user are captured in the database. \n
    b. You have to provide the relevant keywords for retrieving the corresponding user knowledge from the database. \n
    c. All Feedbacks by Evaluator: {user_knowledge_retrieval_feedback}. If feedback is provided, then you have to take that into account while making the plan. \n
    d. For example, if the feedback asks to add or remove keywords to a string or group of strings, then you have to modify the plan accordingly. \n
    
### Response: 
1. Provide a list of strings, where each string contains keywords for retrieving a specific piece of user knowledge. \n
2. The keywords should be relevant enough to fetch the useful information from the user knowledge base for generating the response. \n
3. Note that, each string of keywords will be used to retrieve a specific type of user knowledge, so keep similar keywords in one string and each string semantic meaning should be as different as possible, to cover different aspects of the user knowledge base. \n
4. For example, user_query: "Remeber our goa trip?" \n
user_knowledge_retrieval_keywords: ["travel preferences, travel history, travel companions, travel habits", "goa plan, goa memories, goa experiences"] \n

2. is_message_referred and referred_message_keywords - \n
    a. From the user query, you have to understand whether the user is referring to any past message in the conversation or not.
    b. If yes, then you have to mark is_message_referred as true and generate referred_message_keywords which is a string of relevant text / keywords having maximum semantic overlap with the referred message, which then is used to retrieved from the message history. \n
    c. If no, then respond with is_message_referred as false and keep the referred_message_keywords field empty or null. \n
    d. All Feedbacks by Evaluator: {message_retrieval_feedback}. If feedback is provided, then you have to take that into account while making the plan. \n
    e. For example, if the feedback asks to add more keywords or references, then you have to modify the plan accordingly. \n

3. is_tool_required and selected_tools - \n
    a. You will be provided with a list of available tools and their functionalities, you have to decide whether any of these tools are required to process the user query or not.
    b. If yes, then respond with is_tool_required as true and provide the list of selected tools. \n
    c. If not, then respond with is_tool_required as false and keep the selected_tools field empty or null. \n
    d. Each selected tool in the list must be in following format:
    ```json
    {{
        "tool_id": "the unique id of the tool. select it from the available tools list",
        "instructions": "Specific instructions for the tool to follow (can be null)"
    }}
    ```
    e. tool_id must exactly match one id from the available tools list. Do not invent tool ids, class names, aliases, or new tool names. \n
    
    ### Note for Tool Instructions:
    1. Since you have better understanding of the user query, preferences, behaviour, emotional profile and the context, you can provide specific instructions to the tool to make it more effective and personalized. \n
    2. While building the instruction, remember that manager has no access to user preferences. It only knows the user query and your instructions.
    3. For example, for web search tool, one of the instruction (only a example) can be "Also search for sweet dishes as user is in sad mood, and prefers sweet dishes when he is sad".
    4. Simialrly, you can have instruction of your choice for this as well as other tools.
    5. Any examples in this prompt are illustrative only. Never copy example wording into your output. \n
    6. Instructions can be null as well if you think no specific instructions are required for the tool. \n

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
{format_instructions}
"""

CORTEX_MAIN_PLAN_EVALUATION_PROMPT = """
# Context:
For a given user query, the orchestrator has generated a plan. The plan includes the following: \n
1. user_knowledge_retrieval_keywords - It contains a list of strings where each string is relevant enough to fetch a specific piece of user knowledge. Each string semantic meaning is different from the others. \n
2. referred_message_keywords - The string of relevnat keywords generated based on current query that will be used to fetch the messages from the past conversation done \n
3. is_message_referred - If true, referred_message_keywords are used to retrieve the relevant messages from the past conversation and are provided later. If false, then referred_message_keywords will be empty or null. \n

# Objective:
You are a smart evaluator, whose job is to evaluate the plan generated by the Orchestrator based on the user query and the context provided above, and provide the relevant feedback.\n

# Input Format:
1. User Query \n
2. Orchestration Plan - Includes the user_knowledge_retrieval_keywords, referred_message_keywords and is_message_referred fields. \n
3. Retrieved User Knowledge - The relevant user knowledge retrieved from the database based on the user_knowledge_retrieval_keywords provided by the Orchestrator. \n
4. Retrieved Messages - The relevant messages retrieved from the message history based on the message retrieval plan provided by the Orchestrator. (If is_message_referred is true else null) \n
5. List of previous feedbacks provided by you for the same query (if any in past).
6. User current Mood (from the query) (can be happy, sad, angry, etc.) \n
7. User's previous emotional profile (if any else null) -
    a. Emotional Level (1-10) - Intensity of user emotions at that point of time and how much they prefer emotional responses \n
    b. Logical Level (1-10) - How logically the user thinks and prefers logical discussions. \n
    c. Social Level (1-10) - How socially active the user is and how much they are influenced by their social interactions.
    d. Context Summary - The respective pattern, preferences and behavior summary of the user for that particular combination of mood and time of the day. \n

# Evaluation Instructions:
1. Evaluate the user query, the orchestration plan and the retrieved data based on the plan. \n
2. Also take into account the previous feedbacks provided by you for the same query (if any provided) and the user's emotional state and preferences. \n
3. Based on this, you have to evaluate and decide the feedback \n

# Feedback Instructions:
### USER KNOWLEDGE BASE \n
    a. Check whether the current retrieved User Knowledge is relevant and sufficient for generating the response. \n
    b. If not, then provide specific feedback on what kind of knowledge is missing or irrelevant \n
    c. It should include instructions to either add more specific keywords, remove previously selected keywords from user_knowledge_retrieval_keywords \n
    d. If its relevant and sufficient, then keep it empty or null. \n
    
### MESSAGE RETRIEVAL \n
    a. Check whether the current retrieved messages are relevant and sufficient for generating the response. \n
    b. If not, then provide specific feedback on what kind of messages are missing or irrelevant. \n
    c. It should include instructions to either add the reference to the message, remove the reference to the message or modify the referred_message_keywords for message retrieval. \n
    d. If its relevant and sufficient, then keep it empty or null. \n

# Strict Guidelines for Feedback:
1. If you have added any feedback for either of the above two parts, then provide `is_feedback_required` as `True`, else `False`. \n
2. Your feedback must not lead to loss of information in further response generations. \n
3. Don't repeat the same feedback again and again in the future evaluations. \n

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
Your output must only include the following fields in the JSON format: \n
is_feedback_required - whether any feedback is given or not (True or False) \n
user_knowledge_retrieval_feedback - User Knowledge Retrieval Feedback \n
message_retrieval_feedback - Message Retrieval Feedback \n
Don't print any function, or conversation, or extra message. Strictly respond with the JSON having above mentioned fields only. \n
# Format Instructions:
{format_instructions}
"""

CORTEX_MAIN_FINAL_RESPONSE_PROMPT = """
You are a response generator, whose job is to generate the final response for the user query based on the orchestration plan, the retrieved user knowledge and messages. \n

# Input Format:
1. User Query \n
2. STM Summary - Summary of the conversation so far, and the user's preferences or traits extracted from the conversation. Can be null if not available. \n
3. STM Preferences - The extracted preferences of the user from the conversation, which can include their preferred response style, tone, or any specific instructions. Can be null if not available. \n
4. User current Mood (from the query) (can be happy, sad, angry, etc.) and Time of the day (Morning, Afternoon, Evening, etc.) - Help you to understand the user's emotional state based on the time of day. \n
5. User's previous emotional profile (if any else null) - For the above combination of mood and time of the day, it will give you an idea about:
    a. Emotional Level (1-10) - Intensity of user emotions at that point of time and how much they prefer emotional responses \n
    b. Logical Level (1-10) - How logically the user thinks and prefers logical discussions. \n
    c. Social Level (1-10) - How socially active the user is and how much they are influenced by their social interactions.
    d. Context Summary - The respective pattern, preferences and behavior summary of the user for that particular combination of mood and time of the day. \n
6. Retrieved User Knowledge - The relevant user knowledge telling the relevant preferences, traits, facts and behaviors of the user that can be used for generating the response. (can be null) \n
7. Retrieved Messages - The relevant messages from the past conversation that can be used for generating the response. (can be null) \n
8. Tool Result - If any tool is executed based on the orchestration plan, then the result of the tool execution is also provided as input for generating the response. (can be null) \n
9. Feedback from the Evaluator (if any) - to make the plan more effective. \n

# Objective:
You have to generate the final response for the user query based on the plan.

# Instructions:
1. Understand the user preferences, traits and behaviors using stm summary, stm preferences and the retrieved user knowledge. \n
2. Try to align your response with the user's emotional state and preferences, to make it more personalized and effective. \n
3. Also consider user's current mood and time of the day to make the response more contextually relevant. \n
4. Your response must feel natural, human-like and should not sound like its generated by an AI. \n
5. If user is asking for any specific information, then try to provide it using the retrieved messages, user knowledge and the respective tools results. \n
6. If the feedback from the evaluator is provided, then take that into account while generating the response. \n

# Important Note: \n
1. Before your final response, a fallback response is already shared with the user, for better user experience. \n
For example, fallback_response: "Ok sure let me check and get back to you on this." \n
2. So your response must look like a natural follow up to the fallback response, and should not sound like a standalone response. \n
3. Strictly follow the feedback if provided by the evaluator. \n

# Input: \n
User Query: {user_query}
STM Summary: {stm_summary}
STM Preferences: {stm_preferences}
User Mood: {user_mood}
Time of the day: {user_time}
User Previous Emotional Profile: {user_emotional_profile}
Retrieved User Knowledge: {retrieved_user_knowledge}
Retrieved Messages: {retrieved_messages}
Tool Result: {tool_result}
feedback from Evaluator: {previous_feedback}

# Response:
Generate the final response following the instructions and important note, and responsds with a single string without any additional text or explanation. \n

# Format Instructions:
{format_instructions}
"""

CORTEX_MAIN_FINAL_RESPONSE_EVALUATION_PROMPT = """
# Context: \n
Based on the user query, relevant context and information, a final response is generated by the response generator. \n

# Input Format:
1. User Query \n
2. Final Response - The final response generated by the response generator for the user query. \n
3. STM Summary - Summary of the conversation so far, and the user's preferences or traits extracted from the conversation. Can be null if not available. \n
4. STM Preferences - The extracted preferences of the user from the conversation, which can include their preferred response style, tone, or any specific instructions. Can be null if not available. \n
5. User current Mood (from the query) (can be happy, sad, angry, etc.) and Time of the day (Morning, Afternoon, Evening, etc.) - Help you to understand the user's emotional state based on the time of day. \n
6. User's previous emotional profile (if any else null) - For the above combination of mood and time of the day, it will give you an idea about:
    a. Emotional Level (1-10) - Intensity of user emotions at that point of time and how much they prefer emotional responses \n
    b. Logical Level (1-10) - How logically the user thinks and prefers logical discussions. \n
    c. Social Level (1-10) - How socially active the user is and how much they are influenced by their social interactions.
    d. Context Summary - The respective pattern, preferences and behavior summary of the user for that particular combination of mood and time of the day. \n
7. Retrieved User Knowledge - The relevant user knowledge telling the relevant preferences, traits, facts and behaviors of the user that can be used for generating the response. (can be null) \n
8. Retrieved Messages - The relevant messages from the past conversation that can be used for generating the response. (can be null) \n
9. Tool Result - The result of any tool execution based on the orchestration plan. (can be null) \n
10. Feedback from you - If any given by you in the past evaluations. Can be null if not available. \n

# Objective:
1. You are a smart evaluator, whose job is to evaluate the final response generated by the response generator based on the user query and the context provided above, and provide the relevant feedback.\n

# Instructions:
1. Understand the user query, stm summary, stm preferences, and the retrieved user knowledge, messages and tool results. \n
2. Understand the user's emotional state and preferences using the stm preferences, user emotional profile, current mood and time. \n
3. Based on the above understanding, evaluate the final response on the following parameters: \n
    a. Relevance - How relevant the response is to the user query and the context. \n
    b. Personalization - How well the response is personalized based on the user's preferences, traits and emotional state. \n
    c. Naturalness - How natural and human-like the response is. \n
    d. Alignment - how aligned the response is with the user's emotional state and current mood. \n

# Feedback Instructions:
1. If response is good and aligned with user query, then mark is_feedback_required as False and keep the feedback field empty or null. \n
2. If response is not good and not aligned with user query, then mark is_feedback_required as True and provide specific feedback on what is wrong with the response and how it can be improved. \n
3. Your feedback must not lead to loss of information in further response generations. \n
4. Don't repeat the same feedback again and again in the future evaluations. \n

# Input: \n
User Query: {user_query}
Final Response: {final_response}
STM Summary: {stm_summary}
STM Preferences: {stm_preferences}
User Mood: {user_mood}
Time of the day: {user_time}
User Previous Emotional Profile: {user_emotional_profile}
Retrieved User Knowledge: {retrieved_user_knowledge}
Retrieved Messages: {retrieved_messages}
Tool Result: {tool_result}
Previous Feedbacks: {previous_feedback}

# Response:
Your response must strictly follow the below format without any additional text or explanation. \n
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
    elif type == "final_response_generation":
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
                "format_instructions"
            ],
        )
        return prompt.partial(format_instructions=parser.get_format_instructions()), parser
