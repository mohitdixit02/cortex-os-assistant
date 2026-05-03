from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List
from service.auth.auth_dependency import get_current_user_id
from service.chat_service import chat_service
from controller.requestModels import ChatThreadResponse, MessageResponse
from uuid import UUID

router = APIRouter(prefix="/v1/chat", tags=["Chat"])

@router.post("/threads", response_model=ChatThreadResponse)
async def create_thread(user_id: str = Depends(get_current_user_id)):
    """Initialize a new conversation thread."""
    thread = chat_service.create_thread(user_id)
    return thread

@router.get("/threads", response_model=List[ChatThreadResponse])
async def list_threads(
    user_id: str = Depends(get_current_user_id),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Retrieve a paginated list of all past chat sessions."""
    offset = (page - 1) * limit
    threads = chat_service.list_threads(user_id, offset=offset, limit=limit)
    return threads

@router.get("/threads/{thread_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    thread_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Fetch all messages within a specific thread."""
    messages = chat_service.get_messages(thread_id)
    return messages

@router.delete("/threads/{thread_id}")
async def delete_thread(
    thread_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Archive or delete a specific thread."""
    success = chat_service.delete_thread(thread_id)
    if not success:
        raise HTTPException(status_code=404, detail="Thread not found")
    return {"message": "Thread deleted successfully"}
