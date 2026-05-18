from cortex_cm.pg.models import Tool
from cortex_cm.pg.req import crud
from sqlmodel import Session
from cortex_cm.pg import engine
from uuid import UUID
from typing import Optional

class UserService:
    def get_tool_id_by_name(self, tool_name: str) -> Optional[UUID]:
        with Session(engine) as session:
            tool = crud.get_one(session, Tool, tool_name=tool_name)
            return tool.tool_id if tool else None

user_service = UserService()
