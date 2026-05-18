from fastapi import APIRouter, Depends, HTTPException, Body
from service.auth.auth_dependency import get_current_user_id
from service.user_service import user_service

router = APIRouter(prefix="/v1/user", tags=["User Settings"])
