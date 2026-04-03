from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, SystemMessagePromptTemplate, HumanMessagePromptTemplate, PromptTemplate
from pydantic import BaseModel, Field
from typing import Annotated, Literal, Any, Dict
from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from cortex.graph.state import ConversationState, UserSTM, MemoryEmotionalProfile, UserKnowledge, MemoryUserKnowledge, MemoryUserKnowledgeList

MEMORY_CLIENT_BUILD_STM = """
You are a Short Term Memory (STM) builder for a conversational AI system. Your task is to create a concise summary of the recent interactions and context of the user, which can be used by the AI system to generate more relevant and context-aware responses. \n
# You will be given:
1. User's current query \n
2. AI response to the user's query \n
3. Emootion of the user for the current query \n
4. Previous stm_memory (if any else null) and session_preferences (if any else null) \n

# Information to consider while building STM and session preferences:
User Query: {user_query} \n
AI Response: {ai_response} \n
User Emotion: {user_emotion} \n
Previous STM Memory: {previous_stm_memory} \n
Previous Session Preferences: {previous_session_preferences} \n

# Your task:
Based on the above information, create 
1. stm_memory: 
    a. A concise summary of the recent interactions and context of the user. \n
    b. It contains summary of both human and AI responses, user emotions, and any relevant information that can help in understanding conversation context. \n
2. session_preferences: \n
    a. A summary of the user's preferences and behavior during the current session. \n
    b. It should contain info relevant to user only "user_preferences". \n
    c. Some of the examples for session preferences are: "user_likes", "user_dislikes", "user_emotions", etc. \n
    d. It must not have info regarding AI behaviour. \n

# Important Notes:
1. Your response will be used to overwrite the existing stm_memory and session_preferences for the user, so make sure to include all relevant information in your summary. \n
2. You have to decide which piece of information is repeated, which is no longer required, which is more important, and accordingly build the summary. \n
3. If you think that everything in previous stm_memory or session_preferences is still relevant and important, you can choose to keep it as it is in the new summary, and append your new information to it. \n
4. Remember that quality of summary and information is more important than quantity, even if summary is becoming long \n

# Response: \n
Format response as JSON with the following structure:
{format_instructions}
"""

MEMORY_CLIENT_BUILD_EMOTIONAL_PROFILE = """
You are a Emotional Context Understander and Analyzer for a conversational AI system.
You will be provided with following information:
1. User's current query. It can be any of the one thing- \n
    a. Question (Can you tell me about my friend?)
    b. Statement (I have a friend named John who loves hiking) \n
    c. Command (Remember that I don't like ice cream) \n
    d. Feedback (Your last response was not relevant to my query) \n
2. User's STM summary and session preferences - It will give you an idea about the user's current context, preferences, and emotional state. \n
3. User current Mood (from the query) (can be happy, sad, angry, etc.) and Time of the day (Morning, Afternoon, Evening, etc.) - It will help you to understand the user's emotional state based on the time of day. \n
4. User's previous emotional profile (if any else null) - For the above combination of mood and time of the day, it will give you an idea about:
    a. Emotional Level (1-10) - Give you an idea about the intensity of their emotions at that point in time. \n
    b. Logical Level (1-10) - Give you an idea about how logically the user is thinking and how much they are influenced by their emotions. \n
    c. Social Level (1-10) - Give you an idea about how socially active the user is and how much they are influenced by their social interactions. \n
    d. Context Summary - The respective pattern, preferences and behavior summary of the user for that particular combination of mood and time of the day. \n

# Task:
From the Above information, you have to analayze the user behaviour in various fields (emotional, logical, social) and build the emotional profile. \n

#Steps to follow:
1. Analyze the user's current query and understand the emotion and intent behind it. \n
    a. Is he/she happy? Sad? Angry? Neutral? \n
    b. Is it a question, statement, command, or feedback? \n
2. Compare user intent with the STM summary and session preferences to understand the user's current context and preferences. \n
    a. Is user response is because of not meeting their expectations? \n
    b. Is response is because of some change in user's preferences or context? \n
3. Compare user intent with the previous emotional profile (if present) \n
    a. Is user preference was different but now changed? \n
    b. Is user different levels increasing or decreasing? \n
4. Based on the above analysis, build the updated emotional profile for the user for that particular combination of mood and time of the day. \n

# Notes regarding Context Summary
1. Context Summary must tell user preferences, habits, or factual information based on a given mood and time of the day.
2. Don't mention value of emotional level, logical level, or social level in the context summary. \n
3. Don't mention the user query, emotion, or time of the day in the context summary. \n
4. Content should be in a way that it can help in generating better response in future given mood and time of the day. \n
5. If user wants to remember something for a particular time, then content should include that information also. \n

# Response: \n
Format response as JSON with the following structure:
{format_instructions}

# Input
1. User's current query {user_query} \n
2. User's STM summary {stm_summary} \n
3. User's Session preferences {session_preferences} \n
4. User's current Mood {user_emotion} \n
5. User's current Time of the day {user_time_of_day} \n
6. User's previous emotional profile {previous_emotional_profile} \n
"""

MEMORY_CLIENT_BUILD_USER_KNOWLEDGE = """
You are a smart builder of user knowledge for a conversational AI system.
You will be provided with following information:
1. User's current query. It can be any of the one thing- \n
    a. Question (Can you tell me about my friend?)
    b. Statement (I have a friend named John who loves hiking) \n
    c. Command (Remember that I don't like ice cream) \n
    d. Feedback (Your last response was not relevant to my query) \n
2. User's STM summary and session preferences - It will give you an idea about the user's current context, preferences, and emotional state. \n
3. User current Mood (from the query) (can be happy, sad, angry, etc.). It will help you to understand the user's emotional state. \n

# Task:
From the Above information, you have to build the user knowledge. \n

# Steps
1. Analyze the user's current query and understand the emotion and intent behind it. \n
    a. Is he/she happy? Sad? Angry? Neutral? \n
    b. Is it a question, statement, command, or feedback? \n
    c. What he wants to remember?
    d. What information he wants to forget? \n
    e. What preferences he has? \n
2. Check for User's current context and preferences from STM summary and session preferences. \n
3. Based on the above information and analysis, build the user knowledge providing the category, strictness level, and content. \n

# Usage of Categories: \n
LIKE - Things that user likes or prefers \n
DISLIKE - Things that user dislikes or does not prefer \n
HABIT - Things that user does regularly or has a habit of doing \n
FACT - Factual information about the user that can be useful for response generation (e.g. User has a friend named John who loves hiking) \n
STRICT_PREFERENCE - Strong preferences of the user that should be strictly followed while generating responses (e.g. User does not like ice cream) \n

# Usage of Strictness Levels: \n
MUST - Information that must be followed at highest priority. **Hard Constraint** and cannot be violated - (Example, "User MUST have responses under 50 words.") \n
SHOULD - Information that should be followed while generating responses, **Strong Preference** but can be violated in rare cases if it conflicts with other stronger preferences or important information (For example, User prefers to have a morning workout routine) \n
CAN - Information that user can follow (be a habit, like or dislike), **Optional** and can be easily violated without any significant impact on the user or response quality (e.g. User can eat ice cream, but prefers not to) \n
CANNOT - Similar to Must, but in negative way. Include Information, which User does not want and should be strictly avoided while generating responses. **Strict Forbidden** and cannot be violated - (For example, User CANNOT be asked about their personal information) \n

# NOTE:
1. Always use MUST or CANNOT if category is STRICT_PREFERENCE. \n
2. For other categories, you can use any of the strictness levels based on the importance and relevance of that information. \n

# Response:
Format response in the following format:
{format_instructions}

# Input
1. User's current query {user_query} \n
2. User's STM summary {stm_summary} \n
3. User's Session preferences {session_preferences} \n
4. User's current Mood {user_emotion} \n
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
                "ai_response",
                "user_emotion",
                "previous_stm_memory",
                "previous_session_preferences",
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
                "stm_summary",
                "session_preferences",
                "user_emotion",
                "user_time_of_day",
                "previous_emotional_profile",
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
                "stm_summary",
                "session_preferences",
                "user_emotion",
                "format_instructions"
            ],
        )
        return prompt.partial(format_instructions=parser.get_format_instructions()), parser
