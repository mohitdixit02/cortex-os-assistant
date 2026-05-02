from db.models import UserToolSubscription, Tool
from db.req import crud
from sqlmodel import Session
from db import engine
from uuid import UUID
from typing import Optional

class UserService:
    def toggle_tool_subscription(self, user_id: str, tool_id: str, is_subscribed: bool) -> UserToolSubscription:
        with Session(engine) as session:
            # Check if subscription already exists
            subscription = crud.get_one(
                session, 
                UserToolSubscription, 
                user_id=UUID(user_id), 
                tool_id=UUID(tool_id)
            )
            
            if subscription:
                return crud.update_one(session, subscription, {"is_subscribed": is_subscribed})
            else:
                new_subscription = UserToolSubscription(
                    user_id=UUID(user_id),
                    tool_id=UUID(tool_id),
                    is_subscribed=is_subscribed
                )
                return crud.create_one(session, new_subscription)

    def get_tool_id_by_name(self, tool_name: str) -> Optional[UUID]:
        with Session(engine) as session:
            tool = crud.get_one(session, Tool, tool_name=tool_name)
            return tool.tool_id if tool else None

user_service = UserService()
