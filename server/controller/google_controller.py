from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List
from service.auth.auth_dependency import get_current_user_id
from service.google_service import GoogleServiceBuilder, GoogleCalendarService, GoogleTasksService
from controller.requestModels import CalendarEventCreate, CalendarEventResponse, ReminderCreate, CalendarStatusResponse

router = APIRouter(prefix="/v1/calendar", tags=["Google Integration"])

def get_google_builder(user_id: str = Depends(get_current_user_id)) -> GoogleServiceBuilder:
    return GoogleServiceBuilder(user_id)

@router.get("/status", response_model=CalendarStatusResponse)
async def get_status(builder: GoogleServiceBuilder = Depends(get_google_builder)):
    """Check if the user has successfully linked their Google account."""
    try:
        builder._get_credentials()
        return CalendarStatusResponse(linked=True, token_valid=True)
    except Exception:
        return CalendarStatusResponse(linked=builder.refresh_token is not None, token_valid=False)

@router.get("/events", response_model=List[CalendarEventResponse])
async def list_events(builder: GoogleServiceBuilder = Depends(get_google_builder)):
    """List upcoming events for the next 7 days."""
    service = GoogleCalendarService(builder)
    events = await service.list_events()
    
    formatted_events = []
    for event in events:
        formatted_events.append(CalendarEventResponse(
            id=event['id'],
            summary=event.get('summary', 'No Title'),
            start_time=event['start'].get('dateTime', event['start'].get('date')),
            end_time=event['end'].get('dateTime', event['end'].get('date'))
        ))
    return formatted_events

@router.post("/events", response_model=CalendarEventResponse)
async def create_event(
    event_data: CalendarEventCreate,
    builder: GoogleServiceBuilder = Depends(get_google_builder)
):
    """Create a new calendar event."""
    service = GoogleCalendarService(builder)
    event = await service.create_event(
        summary=event_data.summary,
        start_time=event_data.start_time.isoformat(),
        end_time=event_data.end_time.isoformat(),
        description=event_data.description,
        reminders=event_data.reminders
    )
    return CalendarEventResponse(
        id=event['id'],
        summary=event['summary'],
        start_time=event['start']['dateTime'],
        end_time=event['end']['dateTime']
    )

@router.post("/reminders")
async def create_reminder(
    reminder_data: ReminderCreate,
    builder: GoogleServiceBuilder = Depends(get_google_builder)
):
    """Create a standalone reminder using Google Tasks API."""
    service = GoogleTasksService(builder)
    reminder = await service.create_reminder(
        title=reminder_data.title,
        notes=reminder_data.notes,
        due=reminder_data.due.isoformat() if reminder_data.due else None
    )
    return {"message": "Reminder created", "id": reminder['id']}

@router.delete("/events/{event_id}")
async def delete_event(
    event_id: str,
    builder: GoogleServiceBuilder = Depends(get_google_builder)
):
    """Cancel or remove an event."""
    service = GoogleCalendarService(builder)
    await service.delete_event(event_id)
    return {"message": "Event deleted successfully"}
