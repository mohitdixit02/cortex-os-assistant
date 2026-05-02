from fastapi import APIRouter, Depends, HTTPException, Body
from service.auth.auth_dependency import get_current_user_id
from service.user_service import user_service
from controller.requestModels import ToolSubscriptionRequest

router = APIRouter(prefix="/v1/user", tags=["User Settings"])

@router.post("/tools/{tool_name}/subscription")
async def toggle_tool_subscription(
    tool_name: str,
    request: ToolSubscriptionRequest,
    user_id: str = Depends(get_current_user_id)
):
    """
    Enable or disable a specific AI tool for the current user.
    Example tool_name: 'google_calendar'
    """
    tool_id = user_service.get_tool_id_by_name(tool_name)
    if not tool_id:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    subscription = user_service.toggle_tool_subscription(
        user_id, 
        str(tool_id), 
        request.is_subscribed
    )
    return {
        "tool_name": tool_name,
        "is_subscribed": subscription.is_subscribed,
        "message": "Subscription updated successfully"
    }
