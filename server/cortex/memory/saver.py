from sqlalchemy.engine import Engine
from cortex.memory.model import MemoryModel
from cortex.graph import state
from utility.logger import get_logger
from db import Message, TaskStatus, Task, RoleType, AIClientType
from enum import Enum
from db.req import (
    create_one,
    update_one,
    get_one
)
from typing import Optional, Any
from sqlmodel import Session

class MemorySaver:
    """
    Save Application Memory data to the database. \n
    """
    def __init__(self, engine: Engine, model: MemoryModel):
        self.engine = engine
        self.model = model
        self.logger = get_logger("CORTEX_MEMORY")
        
    def save_message(
        self,
        session_id: str,
        user_id: str,
        content: str,
        role: str,
        ai_client: Optional[str] = None,
        is_tool_used: Optional[bool] = False,
        tool_id: Optional[str] = None,
    ) -> Message:
        """
        ### Save a message to the database. \n
        **Input**: \n
        - `session_id`: The ID of the conversation session. \n
        - `user_id`: The ID of the user. \n
        - `content`: The content of the message. \n
        - `role`: The role of the message sender (e.g., "user", "assistant"). \n
        - `ai_client`: (Optional) The AI client that generated the message, if applicable. \n
        - `is_tool_used`: (Optional) Whether a tool was used in generating the message. Default is False. \n
        - `tool_id`: (Optional) The ID of the tool used, if applicable. \n
        **Output**: The created message object
        """
        # Implement database saving logic here using self.engine
        self.logger.info("Saving message for session_id: %s, user_id: %s, role: %s", session_id, user_id, role)
        embedding = self.model.generate_embeddings(content)
        try:
            if role is Enum:
                role = role.value
            if ai_client and ai_client is Enum:
                ai_client = ai_client.value
            with Session(self.engine) as session:
                state = Message(
                        session_id=session_id,
                        user_id=user_id,
                        content=content,
                        role=role,
                        ai_client=ai_client,
                        is_tool_used=is_tool_used,
                        tool_id=tool_id,
                        embedding=embedding
                    )
                message_obj = create_one(
                    session=session,
                    obj_in=state,
                    commit=True
                )
                self.logger.info("Message with message_id: %s, user_id: %s saved successfully.", session_id, user_id)
                return message_obj
        except Exception as e:
            self.logger.error("Error saving message for session_id: %s, user_id: %s. Error: %s", session_id, user_id, str(e))
            raise e
        
    def add_new_task(
        self,
        message_id: str,
        tool_id: Optional[str],
        task_name: str,
        status: TaskStatus,
        payload: dict,
        status_response: Optional[dict[str, Any]] = None,
        task_metadata: Optional[dict[str, Any]] = None
    ) -> Task:
        """
        ### Add a new task to the database. \n
        **Input**: \n
        - `message_id`: The ID of the message associated with the task. \n
        - `tool_id`: (Optional) The ID of the tool associated with the task, if applicable. \n
        - `task_name`: The name of the task. \n
        - `status`: The status of the task (e.g., INITIALIZED, QUEUED). \n
        - `payload`: The input arguments for the task (e.g., {"number": "123", "text": "Hi"}). \n
        - `status_response`: (Optional) The response data associated with the task status, if applicable. \n
        - `task_metadata`: (Optional) Additional metadata for the task, if applicable. \n
        **Output**: The created task object
        """
        self.logger.info("Adding new task for message_id: %s, task_name: %s", message_id, task_name)
        try:
            if status is Enum:
                status = status.value
            with Session(self.engine) as session:
                task_state = Task(
                    message_id=message_id,
                    tool_id=tool_id,
                    task_name=task_name,
                    status=status,
                    payload=payload,
                    status_response=status_response,
                    task_metadata=task_metadata
                )
                task_obj = create_one(
                    session=session,
                    obj_in=task_state,
                    commit=True
                )
                self.logger.info("Task with task_id: %s for message_id: %s saved successfully.", task_obj.task_id, message_id)
                return task_obj
        except Exception as e:
            self.logger.error("Error adding task for message_id: %s, task_name: %s. Error: %s", message_id, task_name, str(e))
            raise e
    
    def update_task(
        self,
        task_id: str,
        tool_id: Optional[str] = None,
        status: Optional[TaskStatus] = None,
        status_response: Optional[dict[str, Any]] = None
    ) -> Optional[Task]:
        """
        ### Update an existing task in the database. \n
        **Input**: \n
        - `task_id`: The ID of the task to update. \n
        - `tool_id`: (Optional) The new tool ID to associate with the task, if applicable. \n
        - `status`: (Optional) The new status of the task, if applicable. \n
        - `status_response`: (Optional) The new response data associated with the task status, if applicable. \n
        **Output**: The updated task object, or None if the task was not found.
        """
        self.logger.info("Updating task with task_id: %s", task_id)
        try:
            if status is Enum:
                status = status.value
            with Session(self.engine) as session:
                task_obj = get_one(
                    session=session,
                    model=Task,
                    task_id=task_id
                )
                if not task_obj:
                    self.logger.warning("Task with task_id: %s not found for update.", task_id)
                    return None
                
                update_data = {}
                if tool_id is not None:
                    update_data["tool_id"] = tool_id
                if status is not None:
                    update_data["status"] = status
                if status_response is not None:
                    update_data["status_response"] = status_response
                
                updated_task = update_one(
                    session=session,
                    db_obj=task_obj,
                    obj_in=update_data,
                    commit=True
                )
                self.logger.info("Task with task_id: %s updated successfully.", task_id)
                return updated_task
        except Exception as e:
            self.logger.error("Error updating task with task_id: %s. Error: %s", task_id, str(e))
            raise e