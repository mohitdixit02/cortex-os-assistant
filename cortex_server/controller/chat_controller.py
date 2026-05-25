from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List
from cortex_server.service.auth.auth_dependency import get_current_user_id
from cortex_server.service.chat_service import chat_service
from cortex_server.controller.requestModels import ChatThreadResponse, MessageResponse
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

@router.put("/threads/{thread_id}/summary", response_model=ChatThreadResponse)
async def update_thread_summary(
    thread_id: str,
    payload: dict,
    user_id: str = Depends(get_current_user_id)
):
    """Update the summary of a specific thread."""
    summary = payload.get("summary")
    if summary is None:
        raise HTTPException(status_code=400, detail="Summary is required")
    thread = chat_service.update_thread_summary(thread_id, summary)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    return thread

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
