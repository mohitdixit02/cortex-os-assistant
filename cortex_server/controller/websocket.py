from fastapi.routing import APIRouter
from fastapi import WebSocket, WebSocketDisconnect, Query
from cortex_server.service.stream.event import StreamEvent, ResponseKey, StreamEventResponse
from cortex_server.service.stream.main import StreamClient
from cortex_server.service.stream.state_manager import voice_state_manager
import json
import asyncio

router = APIRouter()

@router.websocket("/event")
async def ws_event(websocket: WebSocket, user_id: str = Query(...)):
    """
    ***Event Stream Socket***
    Handles real-time events (JSON) and state management.
    """
    await websocket.accept()
    state = voice_state_manager.get_state(user_id)
    state.event_socket = websocket
    
    streamEvent = StreamEvent(user_id=user_id)
    state.stream_event = streamEvent # Link to state
    
    streamEventResponse = StreamEventResponse(
        websocket=websocket,
        streamEvent=streamEvent
    )
    streamClient = StreamClient(
        websocket=websocket,
        streamEvent=streamEvent,
        user_id=user_id
    )
    streamClient.start_background_tasks()

    try:
        while True:
            text_payload = await websocket.receive_text()
            try:
                payload = json.loads(text_payload)
            except json.JSONDecodeError:
                continue

            msg_type = payload.get("type")
            
            if msg_type == "UserSpeechStartEvent":
                state.is_user_speaking = True
                if state.stream_event:
                    await state.stream_event.cancel("User started speaking")
                await streamEventResponse.send_response(response=ResponseKey.START_LISTENING)
            
            elif msg_type == "UserSpeechEndEvent":
                state.is_user_speaking = False
                await streamEventResponse.send_response(response=ResponseKey.FINISH_LISTENING)
            
            elif msg_type == "AIStartSpeakingEvent":
                state.is_ai_speaking = True
            
            elif msg_type == "AIStopSpeakingEvent":
                state.is_ai_speaking = False
            
            elif msg_type == "playback_done":
                stream_id = payload.get("streamId")
                streamEvent.markPlaybackDone(stream_id=stream_id)

    except WebSocketDisconnect:
        state.event_socket = None
    finally:
        await streamClient.shutdown()

@router.websocket("/audio")
async def ws_audio(websocket: WebSocket, user_id: str = Query(...)):
    """
    ***Audio Stream Socket***
    Handles raw binary PCM data.
    """
    await websocket.accept()
    state = voice_state_manager.get_state(user_id)
    state.audio_socket = websocket
    
    # Use the existing stream_event from state if available
    streamEvent = state.stream_event or StreamEvent(user_id=user_id)
    state.stream_event = streamEvent
    
    # The event socket is where we send control messages
    event_socket = state.event_socket
    
    streamEventResponse = StreamEventResponse(
        websocket=event_socket,
        streamEvent=streamEvent
    )
    
    streamClient = StreamClient(
        websocket=websocket,
        streamEvent=streamEvent,
        user_id=user_id
    )

    try:
        while True:
            res = await websocket.receive()
            if res.get("bytes") is not None:
                streamEvent.appendAudioBuffer(res.get("bytes"))
                continue
            
            text_payload = res.get("text")
            if text_payload:
                payload = json.loads(text_payload)
                msg_type = payload.get("type")
                
                if msg_type == "start_conversation":
                    streamEvent.resetAudioBuffer()
                    streamEvent.session_id = payload.get("session_id")
                    if event_socket:
                        await streamEventResponse.send_response(response=ResponseKey.CONVERSATION_START)
                
                elif msg_type == "end_conversation":
                    audio_snapshot = streamEvent.getAudioBufferBytes()
                    streamEvent.resetAudioBuffer()
                    # Trigger processing
                    streamEvent.startStreamResponse(
                        streamResponse=streamClient.stream_response,
                        audio_bytes=audio_snapshot,
                    )
                    
    except WebSocketDisconnect:
        state.audio_socket = None
