from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate, HumanMessagePromptTemplate, PromptTemplate
from pydantic import BaseModel, Field
from typing import Annotated, Literal, Any, Dict
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from cortex.graph.state import ConversationState, UserSTM, MemoryEmotionalProfile, UserKnowledge, MemoryUserKnowledge, MemoryUserKnowledgeList

MEMORY_CLIENT_BUILD_STM = """
You are a Short Term Memory (STM) builder for a conversational AI system. Your task is to create a concise summary of the recent interactions and context of the user, which can be used by the AI system to generate more relevant and context-aware responses. \n
# You will be given:
1. User's current query \n
2. Emotion of the user for the current query \n
3. Previous stm_memory (if any else null) and session_preferences (if any else null) \n
4. Recent conversation history (if any else null) \n

# Your task:
Based on the information provided, create \n
1. stm_memory:
    a. A concise summary of the recent interactions and context of the user. \n
    b. It contains summary of both human and AI responses, user emotions, and any relevant information that can help in understanding conversation context. \n
    c. Extend the previous stm_memory with the recent conversation. \n
2. session_preferences (can be null if nothing new or important to save): \n
    a. User guidelines, recommendatios, or instructions that he/she ask to follow for the current session. \n
    b. Any specific preferences or behavior of the user that can help in generating better responses during the current session. \n
    c. Some of the examples for session preferences are: "user_likes", "user_dislikes", "user_emotions", etc. \n

# Important Instructions - stm memory:
1. Your response will be used to overwrite the existing stm_memory (if exists) for the user, so make sure to include all relevant information in your summary. \n
2. You have to decide which piece of information is repeated, which is no longer required, which is more important, and accordingly build the summary. \n
3. If you think that everything in previous stm_memory is still relevant and important, you can choose to keep it as it is in the new summary, and append your new information to it. \n
4. Remember that quality of summary and information is more important than quantity, even if summary is becoming long \n

# Important Instructions - session_preferences:
1. If you think no new session preference is required to be added, you can keep session_preferences as null. \n
2. If you think of some new session preference to be added, you have to: \n
    a. Pick the existing session preferences (if exists) and re-build the session preferences with the updated information. \n
    b. You can modify the existing session preference if you think some information is repeated or no-longer required. \n
3. If you give non-null session preferences, then it will overwrite the existing session preferences (if exists), so make sure to include all relevant information in your new session preferences. \n

# Information to consider while building STM and session preferences:
User Query: {user_query} \n
User Emotion: {user_emotion} \n
Previous STM Memory: {previous_stm_memory} \n
Previous Session Preferences: {previous_session_preferences} \n
Recent Conversation: {recent_conversation} \n

# Strict Guidelines - session_preferences:
    a. It must not have any information related to AI \n
    b. It must not have "user_query", "user_response", "messages", etc.\n
    c. Session preference is only for session specific user instructions, and not to store history. \n

# Response: \n
Format response as JSON strictly following the structure below:
{format_instructions}
No other text, function call, chat message, etc. \n
"""

MEMORY_CLIENT_BUILD_EMOTIONAL_PROFILE = """
You are a Emotional Context Understander and Analyzer for a conversational AI system.
You will be provided with following information:
1. User's current query. It can be any of the one thing- \n
    a. Question (Can you tell me about my friend?) \n
    b. Statement (I have a friend named John who loves hiking) \n
    c. Command (Remember that I don't like ice cream) \n
    d. Feedback (Your last response was not relevant to my query) \n
2. User current Mood (from the query) and Time of the day (Morning, Afternoon, Evening, or Night) - It will help you to understand the user's emotional state based on the time of day. \n
3. User's previous emotional profile (if any else null) - For the above combination of mood and time of the day, it will give you an idea about:
    a. Emotional Level (1-10) - Intensity of user emotions at that point of time and how much they prefer emotional responses \n
    b. Logical Level (1-10) - How logically the user thinks and prefers logical discussions. \n
    c. Social Level (1-10) - How socially active the user is and how much they are influenced by their social interactions. Introvert, Ambivert or Extrovert\n
    d. Context Summary - The respective pattern, preferences and behavior summary of the user for that particular combination of mood and time of the day. \n
4. Recent Conversation history (if any else null) \n

# Task:
From the Above information, you have to analayze the user behaviour in various fields (emotional, logical, social) and build the emotional profile. \n

#Steps to follow:
1. Analyze the user's current query and understand the emotion and intent behind it. \n
    a. Is he/she happy? Sad? Angry? Neutral? \n
    b. Is it a question, statement, command, or feedback? \n
2. Compare user intent with the recent conversation history to understand the user's current context and preferences. \n
    a. Is user response is because of not meeting their expectations? \n
    b. Is response is because of some change in user's preferences or context? \n
3. Compare user intent with the previous emotional profile (if present) \n
    a. Is user preference was different but now changed? \n
    b. Is user different levels (emotional, logical, social) increasing or decreasing? \n
4. Based on the above analysis, build the updated emotional profile for the user for that particular combination of mood and time of the day. \n

# Notes regarding Context Summary
1. Context Summary must include only user preferences, behaviour or habits related information based on a given mood and time of the day.
2. Don't mention value of emotional level, logical level, or social level in the context summary. \n
3. Don't mention the user query, emotion, or time of the day in the context summary. \n
4. Content should be in a way that it can help in generating better response in future given mood and time of the day. \n
5. If user wants to remember something for a particular time or particular mood, then content should include that information also. \n

# Input
1. User's current query {user_query} \n
2. User's current Mood {user_emotion} \n
3. User's current Time of the day {user_time_of_day} \n
4. User's previous emotional profile {previous_emotional_profile} \n
5. Recent conversation history: {recent_conversation} \n

# Response: \n
Format response as JSON strictly following the structure below:
{format_instructions}
Don't mention any other text, function call, chat message, explanation, code, etc. \n
"""

MEMORY_CLIENT_BUILD_USER_KNOWLEDGE = """
# Context \n
You will be provided with following information:
1. User's current query. It can be any of the one thing- \n
    a. Question (Can you tell me about my friend?)
    b. Statement (I have a friend named John who loves hiking) \n
    c. Command (Remember that I don't like ice cream) \n
    d. Feedback (Your last response was not relevant to my query) \n
2. User current Mood (from the query) and Time of the day (Morning, Afternoon, Evening, or Night) - It will help you to understand the user's emotional state based on the time of day. \n
3. Previous user long term memory (if any) \n
4. Recent conversation history (if any else null) \n

# Objective:
You are a smart builder of user's long term memory from the conversations. From the provided information, you have to provide a set of instructions to build the long term user memory.\n

# How to decide what information to include in long term memory: \n
## Analysis: \n
1. Analyze the user's current query and understand the emotion and intent behind it. \n
a. Is he/she happy? Sad? Angry? Neutral? \n
b. Is it a question, statement, command, or feedback? \n
c. If he/she wants to remember or forget something?
2. Check for User's current context and preferences based on the recent conversation if provided. \n
3. If previous user memory is given, then also compare the new memory with the previous memory. \n

## Decision: \n
Based on the above information and analysis, you have to decide the correct scenario: \n
### Scenario 1: If nothing is relevant enough to be added or updated in long term memory, then simply respond with an empty list. \n

### Scenario 2: Relevant info is available to add and no "previous user long term memory" exists. \n
In this case, trait_id will be null, so action must be "add" for all the memory items. \n Follow same instructions as in Sub-Scenario 2.2 mentioned below for building the memory items. \n

### Scenario 3: Relevant info is available to add and "previous user long term memory" exists. \n
In this case, you have to compare the new memory items with the previous memory items. We have two sub-scenarios here: \n
    #### Sub-Scenario 2.1: \n
    a. If the previous memory item is similar with new knowledge, then always try to update the existing memory item first. \n
    b. First check whether the corresponding trait_id of that previous memory item is present or not.
        i. If present, mark action as "update" and provide the trait_id of the respective "previous user long term memory". (trait_id is UUID of the memory item which is required to update that memory item in database) \n
        ii. If trait_id is missing or not provided discard the sub-scenario 2.1 flow, Mark action as "add" and follow sub-scenario 2.2 guidelines immediately. \n
    c. Make sure that update action must not lead to loss of previous useful information. \n
    d. You can combine previous and new information in case you are not sure about the importance of any piece of information. \n
    e. Only discard previous information if you are sure that it is no longer relevant or useful. \n
    
    #### Strict Guidelines for trait_id: \n
    a. You are strictly not allowed to create a new trait_id on your own in any case. \n
    b. Any use of invalid trait_id or creation of new trait_id on your own will be considered as a violation of guidelines and can lead to termination of the application. \n

    #### Sub-Scenario 2.2: \n
    1. If nothing something similar exists, or if new information is required to be added, always keep similar things together and create less number of memory items by combining the information. \n
    2. Don't create similar memory items again and again. \n
    3. Information should be concise but still relevant and useful for future response generation. \n
### If nothing is relevant enough to be added or updated in long term memory, then simply respond with an empty list. \n

# How to allocate Strictness Levels: \n
1. Before allocating any level, keep in mind that "Strictiness Level" determines the priority of one memory item over the other. For example, if there is a conflict between two memory items, then the one with higher strictness level will be followed. \n
### Each Strictness level with examples: \n
*MUST* - "Meaning: Always do this". Hard Constraint and cannot be violated - For example, "Always reply with examples", "Always call me by my name" etc. \n
*CANNOT* - "Meaning: Never do this". Hard Constraint and cannot be violated - For example, "I don't like long explanations", "I hate crowded places", "I have a dog allergy", etc. \n
*SHOULD* - "Meaning: Generally prefer this". **Strong Preference** but can be violated in rare cases if it conflicts with other stronger preferences - For example, "It will be better if you keep your responses concise.", etc. \n
*CAN* - "Meaning: Optionally do this". Can be easily violated without any significant impact - includes Habits/ Curiosities - For example, "Sometimes I like to listen to music while working.", etc. \n

2. Strictness Level impact on response generation: \n
MUST (Positive Rule) = CANNOT (Negavtive Rule) > SHOULD > CAN \n

# Instructions for content: \n
1. Content must not include user query or AI responses. \n
2. Content must not include any information about AI behaviour. \n
3. Content must not include things like "user ask this, user ask that". \n
4. Content must include only user preferences, behaviour, habits or facts related information. \n
5. Seleted content must be relevant and useful for long run holding only and not for short term context understanding. \n
6. Short term context handling is done by STM Builder, You are Long Term Memory builder, so you must focus on building long term memory only. \n

# Input
1. User's current query {user_query} \n
2. User's current Mood {user_emotion} \n
3. User's current Time of the day {user_time_of_day} \n
4. Previous user long term memory {previous_user_knowledge} \n
5. Recent conversation history: {recent_conversation} \n

# Response:
Return ONLY valid JSON array, no other text, function call, chat message \n
Example of JSON array: \n
```json
[
    {{
        "action": "add",
        "trait_id": null,
        "strictness": "MUST",
        "content": "your content here"
    }}
]
```
Follow the format instructions strictly below:
{format_instructions}
"""

def get_memory_client_prompts(
    type: str,
):
    if type == "build_stm":
        parser = PydanticOutputParser(pydantic_object=UserSTM)
        prompt = PromptTemplate(
            template=MEMORY_CLIENT_BUILD_STM,
            input_variables=[
                "user_query",
                "user_emotion",
                "previous_stm_memory",
                "previous_session_preferences",
                "recent_conversation",
                "format_instructions"
            ],
        )
        return prompt.partial(format_instructions=parser.get_format_instructions()), parser
    elif type == "build_emotional_profile":
        parser = PydanticOutputParser(pydantic_object=MemoryEmotionalProfile)
        prompt = PromptTemplate(
            template=MEMORY_CLIENT_BUILD_EMOTIONAL_PROFILE,
            input_variables=[
                "user_query",
                "user_emotion",
                "user_time_of_day",
                "previous_emotional_profile",
                "recent_conversation",
                "format_instructions"
            ],
        )
        return prompt.partial(format_instructions=parser.get_format_instructions()), parser
    elif type == "build_user_knowledge":
        parser = PydanticOutputParser(pydantic_object=MemoryUserKnowledgeList)
        prompt = PromptTemplate(
            template=MEMORY_CLIENT_BUILD_USER_KNOWLEDGE,
            input_variables=[
                "user_query",
                "user_emotion",
                "user_time_of_day",
                "previous_user_knowledge",
                "recent_conversation",
                "format_instructions"
            ],
        )
        return prompt.partial(format_instructions=parser.get_format_instructions()), parser
