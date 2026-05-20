from fastapi import APIRouter, Depends, HTTPException
from uuid import UUID
from typing import Dict, Any
from cortex_server.service.config_service import config_service
from cortex_cm.pg import UserConfig
from pydantic import BaseModel

router = APIRouter(prefix="/v1/user/config", tags=["Config"])

class ConfigUpdate(BaseModel):
    voice_client_timeout_seconds: int | None = None
    force_open_websocket: bool | None = None
    reminder_minutes_before_trigger_time: int | None = None
    timezone: str | None = None
    timezone_mode: str | None = None

@router.get("/{user_id}")
async def get_config(user_id: str):
    try:
        uid = UUID(user_id)
        config = config_service.get_user_config(uid)
        return config
    except Exception as e:
        print(f"Error in get_config: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}")
async def update_config(user_id: str, config_update: ConfigUpdate):
    try:
        print(f"Updating config for user {user_id}: {config_update}")
        uid = UUID(user_id)
        # Filter out None values to avoid overwriting with defaults if not provided
        update_data = {k: v for k, v in config_update.model_dump().items() if v is not None}
        config = config_service.update_user_config(uid, update_data)
        return {"status": "success", "config": config}
    except Exception as e:
        print(f"Error in update_config: {e}")
        raise HTTPException(status_code=500, detail=str(e))
