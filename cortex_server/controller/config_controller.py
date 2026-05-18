from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from typing import Dict, Any
from cortex_server.service.config_service import config_service
from cortex_cm.pg import UserConfig
from pydantic import BaseModel

router = APIRouter(tags=["Config"])

class ConfigUpdate(BaseModel):
    voice_client_timeout: int | None = None
    force_open_websocket: bool | None = None
    reminder_before_trigger_time: int | None = None
    timezone: str | None = None
    timezone_mode: str | None = None

@router.get("/user/config/{user_id}")
async def get_config(user_id: UUID):
    try:
        config = config_service.get_user_config(user_id)
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/user/config/{user_id}")
async def update_config(user_id: UUID, config_update: ConfigUpdate):
    try:
        # Filter out None values to avoid overwriting with defaults if not provided
        update_data = {k: v for k, v in config_update.model_dump().items() if v is not None}
        config = config_service.update_user_config(user_id, update_data)
        return {"status": "success", "config": config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
