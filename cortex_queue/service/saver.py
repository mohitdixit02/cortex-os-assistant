from fastapi import HTTPException
from cortex_queue.dto import AddTaskRequest
from cortex_cm.pg import RoleType, AIClientType
from cortex_queue.service.utility import _get_memory_saver

def save_conversation_messages(request: AddTaskRequest):
    """
    Extracts and saves user and voice client messages from an AddTaskRequest.
    Returns the saved user message object.
    """
    memory_saver = _get_memory_saver()
    user_id = request.metadata.get("user_id")
    session_id = request.metadata.get("session_id")
    voice_client_response = request.metadata.get("voice_client_response")
    
    if not user_id or not session_id:
        raise HTTPException(status_code=400, detail="Missing User ID or Session ID in task metadata")
    
    query = request.payload.get("query", "")
    original_query = request.payload.get("original_query")
    is_refined_query = request.payload.get("is_refined_query", False)
    
    # Logic from _add_vc_task_to_queue
    content_to_save = original_query if is_refined_query and original_query else query
    refined_query_to_save = query if is_refined_query else None

    user_msg = memory_saver.save_message(
        session_id=session_id,
        user_id=user_id,
        content=content_to_save,
        role=RoleType.USER,
        ai_client=None,
        is_tool_used=False,
        tool_id=None,
        is_refined_query=is_refined_query,
        refined_query=refined_query_to_save
    )
    
    memory_saver.save_message(
        session_id=session_id,
        user_id=user_id,
        content=voice_client_response if voice_client_response else "",
        role=RoleType.AI,
        ai_client=AIClientType.VOICE_CLIENT,
        is_tool_used=False,
        tool_id=None
    )
    
    return user_msg
