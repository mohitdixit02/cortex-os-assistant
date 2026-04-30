from pydantic import BaseModel, Field
from typing import Annotated, Optional
from cortex.graph.state import ConversationState, OrchestrationState, CortexToolList

class InternalPlanKnowledge(BaseModel):
    reasoning: Annotated[str, Field(description="The reasoning behind the selection of keywords and acceptance threshold for user knowledge retrieval. It should be based on the user query, context and feedback from evaluator if any. Not more than 80 words.")]
    user_knowledge_retrieval_keywords: Annotated[list[str], Field(description="List of keywords relevant enough to retrieve user knowledge base for the current query")] = []
    user_knowledge_acceptance_threshold: Annotated[float, Field(le=0.6, ge=0.2, description="Similarity threshold for accepting user knowledge items retrieved based on the keywords")]

class InternalPlanMessages(BaseModel):
    reasoning: Annotated[str, Field(description="The reasoning behind the selection of keywords and acceptance threshold for user knowledge retrieval. It should be based on the user query, context and feedback from evaluator if any. Not more than 80 words.")]
    is_message_referred: Annotated[bool, Field(description="Whether the user query is referring to any past message in the conversation or not")]
    referred_message_keywords: Annotated[Optional[str], Field(description="Keywords from the referred message")] = None

class InternalPlanTools(BaseModel):
    reasoning: Annotated[str, Field(description="The reasoning behind the selection of tools for processing the user query. It should be based on the user query, context and feedback from evaluator if any. Not more than 80 words.")]
    is_tool_required: Annotated[bool, Field(description="Whether any tool is required to process the user query or not")]
    selected_tools: Annotated[Optional[CortexToolList], Field(description="List of selected tools")] = None

CORTEX_MAIN_ORCHESTRATOR_KNOWLEDGE_PROMPT = """
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

# Input
User Query: {user_query}
STM Summary: {stm_summary}
STM Preferences: {stm_preferences}
User Mood: {user_mood}
User Time of the day: {user_time}
User Previous Emotional Profile: {user_emotional_profile}

# Objective:
You are a smart decision planner for knowledge retrieval, you have to understand the given user query, context provided based on all the input fields and instructions, and decide user_knowledge_retrieval_keywords and user_knowledge_acceptance_threshold: \n

## Guidelines - \n
a. Key facts, preferences, traits and behaviours for the user are captured in the database. You have to provide two things: \n
i. Relevant keywords for retrieving the corresponding user knowledge from the database. \n
ii. user_knowledge_acceptance_threshold, which is the similarity threshold for accepting the user knowledge items retrieved based on the keywords. It must be a float between 0.2 and 0.6. \n
b. All Feedbacks by Evaluator: {user_knowledge_retrieval_feedback}. If feedback is provided, then you must have to take that into account while making the plan. \n
c. Feedback may ask, 
i. To add or remove some keywords to a string or group of strings. \n
ii. To increase or decrease the user_knowledge_acceptance_threshold. \n

### user_knowledge_acceptance_threshold guidance:
- Higher threshold makes more documents rejected and result more strict.
- If evaluator has given user_knowledge_acceptance_threshold, use that strictly, and don't change it. \n
- If no feedback is given then use it as per following: \n
- For general knowledge retrieval: Use 0.25 to 0.45 (lower for broader matches)
- For specific/strict knowledge: Use 0.45 to 0.6

### Response: 
1. Provide: \n
i. user_knowledge_retrieval_keywords - a list of strings, where each string contains keywords for retrieving a specific piece of user knowledge. \n
ii. user_knowledge_acceptance_threshold - a float between 0.2 and 0.6, representing the similarity threshold for accepting user knowledge items. \n
2. The keywords should be relevant enough to fetch the useful information from the user knowledge base for generating the response. \n
3. Note that, each string of keywords will be used to retrieve a specific type of user knowledge, so keep similar keywords in one string and each string semantic meaning should be as different as possible, to cover different aspects of the user knowledge base. \n
4. Strictky follow the feedback if any. \n
5. You have to provide the reasoning behind your decision in the `reasoning` field of the response. \n

# Response
Follow the below format strictly and only respond with the format mentioned without any additional text or explanation. \n
{format_instructions}
"""

CORTEX_MAIN_ORCHESTRATOR_MESSAGES_PROMPT = """
# Input Format:
1. User Query \n
2. STM Summary - Summary of the conversation so far, and the user's preferences or traits extracted from the conversation. Can be null if not available. \n
3. STM Preferences - The extracted preferences of the user from the conversation, which can include their preferred response style, tone, or any specific instructions. Can be null if not available. \n
4. User current Mood (from the query) (can be happy, sad, angry, etc.) and Time of the day (Morning, Afternoon, Evening, etc.) - Help you to understand the user's emotional state based on the time of day. \n
5. User's Long term Memory - Relevant facts, preferences, traits and behavious of the user persisted based on past interactions.
6. Feedback from the Evaluator (if any) - to make the plan more effective. \n

# Input
User Query: {user_query}
STM Summary: {stm_summary}
STM Preferences: {stm_preferences}
User Mood: {user_mood}
User Time of the day: {user_time}
User's Long term Memory: {retrieved_user_knowledge}

# Objective:
You are a smart decision planner for old conversation messages retrieval, you have to understand the given user query, context provided based on all the input fields and instructions, and decide: \n
## is_message_referred and referred_message_keywords - \n
a. From the user query, you have to understand whether the user query is related to past conversations or not. For example, \n
    i. User ask about some past activity or interaction with you.
    ii. User recall some information that you have shared in past.
    iii. User ask you to continue, act or do something, which you are not sure of, then it is in previous conversation.
b. If yes, then you have to mark is_message_referred as true and generate referred_message_keywords. \n
i. referred_message_keywords should be a string of keywords having maximum semantic overlap with the referred message / user query. \n
ii. keywords should be relevant yet diversified enough to fetch the relevant messages from the past conversation. \n
iii. Keep minimum 3 and atmost 7 keywords in the referred_message_keywords string. \n
c. If no, then respond with is_message_referred as false and keep the referred_message_keywords field empty or null. \n
d. All Feedbacks by Evaluator: {message_retrieval_feedback}. If feedback is provided, then you must have to take that into account while making the plan. \n
e. For example, if the feedback asks to add more keywords or references, then you have to modify the plan accordingly. \n

### You have to provide the reasoning behind your decision in the `reasoning` field of the response. \n

# Response
Follow the below format strictly and only respond with the format mentioned without any additional text or explanation. \n
{format_instructions}
"""

CORTEX_MAIN_ORCHESTRATOR_TOOLS_PROMPT = """
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
6. User's Long term Memory - Relevant facts, preferences, traits and behavious of the user persisted based on past interactions.
7. User's Relevant Conversation History - Relevant past conversation messages based on the user query (if any).
8. Feedback from the Evaluator (if any) - to make the plan more effective. \n
9. Date/Time of the query

# Input
User Query: {user_query}
STM Summary: {stm_summary}
STM Preferences: {stm_preferences}
User Mood: {user_mood}
User Time of the day: {user_time}
User Previous Emotional Profile: {user_emotional_profile}
User's Long term Memory: {retrieved_user_knowledge}
User's Relevant Conversation History: {retrieved_messages}
Current Date/Time of the Query: {timestamp}

# Objective:
You are a smart decision planner for tools selection, you have to understand the given user query, context provided based on all the input fields and instructions, and decide what type of tools are required to answer the user query. \n
Your selected tool-id and instructions are used by the `tool executor` to execute the respective tool and provide the output. \n

## Guidelines for is_tool_required and selected_tools - \n
a. You will be provided with a list of available tools and their functionalities, you have to decide whether any of these tools are required to process the user query or not.
b. If yes, then respond with is_tool_required as true and provide the list of selected tools. \n
c. If not, then respond with is_tool_required as false and keep the selected_tools field empty or null. \n
d. Each selected tool in the list must be in following format:
```json
[
{{
    "tool_id": "the unique id of the tool. select it from the available tools list",
    "instructions": "Specific instructions for the tool to follow (can be null)"
}},
]
```
e. tool_id must exactly match one id from the available tools list. Do not invent tool ids, class names, aliases, or new tool names. \n
f. You can select one tool, multiple tools or no tool at all based on the user query and context. \n

### Note for Tool Instructions:
1. Since you have better understanding of the user query, preferences, behaviour, emotional profile and the context, you can provide specific instructions to the tool to make it more effective and personalized. \n
2. `Important`: While building the instruction, strictly note that tool executor don't know user's preferences or what user like or dislike. It only knows your instructions. So your instructions must be specific.
3. For example, for web search tool, one of the instruction (only a example) can be "Also search for sweet dishes as user is in sad mood, and prefers sweet dishes when he is sad", and not "Search for user's favourite dishes, because he is sad" \n
4. Simialrly, you can have instruction of your choice for tools that you select.
5. Any examples in this prompt are illustrative only. Never copy example wording into your output. \n
6. Instructions can be null as well if you think no specific instructions are required for the tool. \n
7. If any feedback from evaluator is providing regarding tool selection or tool instructions, then you must have to follow that feedback strictly while making the plan. \n

### You have to provide the reasoning behind your decision in the `reasoning` field of the response. \n

# Available Tools: 
{available_tools}

### Feedback from Evaluator:
{tool_selection_feedback}

# Response
Follow the below format strictly and only respond with the format mentioned without any additional text or explanation. \n
{format_instructions}
"""

