from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

class EventReminderOutput(BaseModel):
    reminder_message: str = Field(description="The final reminder message to be sent to the user.")

EVENT_REMINDER_GENERATION_PROMPT = """
You are an assitant which generates the reminder message in a human assitant way, to be sent to the user for an upcoming event based on the provided information. \n

## Information
Event Name: {event_name} - Name of the upcoming event.
Event Description: {event_description} - Description of the event which may contain important details about the event provided by the user.
User Name: {user_name} - Name of the user who will receive the reminder. (Can be NULL)
Time left for the event: {time_left} - The time left for the event to occur. Will be given in minutes. (0 means less than a minute left, can be negative if event time has already passed)
Time when this reminder is generated: {time_of_query} - The time of day when the reminder is being generated. It can be one of the following values: MORNING, AFTERNOON, EVENING, NIGHT.

## Instructions
Generate the final reminder message. Note that it should be human-like and should feel like a reminder by a personal assitant friend. \n
Use Event Description and Time Left to highlight important details and urgency in the reminder message if any. \n
Personalize response using User Name and Time of generation of reminder if provided. \n
Make sure the reminder message is concise and to the point. Not more than 1 or 2 sentences. \n

## Response
Reply in the below format strictly without any extra text, explanation, chat, code or function. \n
{format_instructions}
"""
  
def get_event_tool_prompt(
    type: str,
):
    if type == "build_reminder":
        parser = PydanticOutputParser(pydantic_object=EventReminderOutput)
        prompt = PromptTemplate(
            template=EVENT_REMINDER_GENERATION_PROMPT,
            input_variables=[
                "event_name",
                "event_description",
                "user_name",
                "time_left",
                "time_of_query",
                "format_instructions"
            ],
        )
        return prompt.partial(format_instructions=parser.get_format_instructions()), parser
