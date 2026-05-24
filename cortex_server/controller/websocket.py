from fastapi.routing import APIRouter
from fastapi import WebSocket, WebSocketDisconnect, Query
from cortex_server.service.stream.event import StreamEvent, ResponseKey, StreamEventResponse
from cortex_server.service.stream.main import StreamClient
from cortex_server.service.stream.state_manager import voice_state_manager
import json

router = APIRouter()

@router.websocket("/event")
async def ws_event(websocket: WebSocket, user_id: str = Query(...)):
    """
    ***Event Stream Socket***
    Reserved strictly for backend-to-client notifications (Reminders).
    All voice interaction logic has been moved to the /audio socket.
    """
    await websocket.accept()
    state = voice_state_manager.get_state(user_id)
    state.event_socket = websocket
    
    try:
        while True:
            res = await websocket.receive_text()
            print(f"Received on /event socket (user_id={user_id}): {res}")
            
            try:
                payload = json.loads(res)
                msg_type = payload.get("type")
                
                if msg_type == "WEBSOCKET_OPEN_TRUE":
                    state.audio_ws_success = True
                    state.audio_ws_opened_event.set()
                    
                elif msg_type == "WEBSOCKET_OPEN_FALSE":
                    state.audio_ws_success = False
                    state.audio_ws_opened_event.set()
                    
            except json.JSONDecodeError:
                continue
                
    except WebSocketDisconnect:
        state.event_socket = None

@router.websocket("/audio")
async def ws_audio(websocket: WebSocket, user_id: str = Query(...)):
    """
    ***Audio Stream Socket***
    Handles raw binary PCM data AND all voice-related control events.
    """
    await websocket.accept()
    state = voice_state_manager.get_state(user_id)
    state.audio_socket = websocket
    
    streamEvent = state.stream_event or StreamEvent(user_id=user_id)
    state.stream_event = streamEvent
    
    streamEventResponse = StreamEventResponse(
        websocket=websocket,
        streamEvent=streamEvent
    )
    
    state.stream_client = StreamClient(
        websocket=websocket,
        streamEvent=streamEvent,
        user_id=user_id
    )

    try:
        while True:
            res = await websocket.receive()
            
            if res.get("type") == "websocket.disconnect":
                break

            print(f"Received on /audio socket (user_id={user_id}): {res.keys()}")
            if "text" in res:
                print(f"Text payload: {res['text']}")

            # Handle Binary Data (Audio Chunks)
            if res.get("bytes") is not None:
                if state.is_user_speaking:
                    streamEvent.appendAudioBuffer(res.get("bytes"))
                else:
                    print(f"Ignoring audio chunk from user_id={user_id} because user is not marked as speaking")
                continue
            
            # Handle Text Data (JSON Events)
            text_payload = res.get("text")
            if text_payload:
                try:
                    payload = json.loads(text_payload)
                except json.JSONDecodeError:
                    continue
                    
                msg_type = payload.get("type")
                
                # Conversation Lifecycle
                if msg_type == "ConversationStart":
                    streamEvent.resetAudioBuffer()
                    streamEvent.session_id = payload.get("session_id")
                    print(f"Sending response key: {ResponseKey.CONVERSATION_START} to user_id={user_id}")
                    await streamEventResponse.send_response(response=ResponseKey.CONVERSATION_START)
                
                elif msg_type == "ConversationEnd":
                    streamEvent.resetAudioBuffer()
                    print(f"Sending response key: {ResponseKey.CONVERSATION_END} to user_id={user_id}")
                    await streamEventResponse.send_response(response=ResponseKey.CONVERSATION_END)

                # VAD & Interruption Events
                elif msg_type == "UserSpeechStartEvent":
                    state.is_user_speaking = True
                    print(f"Sending response key: {ResponseKey.START_LISTENING} to user_id={user_id}")
                    await streamEvent.cancel("User started speaking")
                    await streamEventResponse.send_response(response=ResponseKey.START_LISTENING)
                
                elif msg_type == "UserSpeechEndEvent":
                    state.is_user_speaking = False
                    print(f"Sending response key: {ResponseKey.WAITING_FOR_FURTHER_AUDIO} to user_id={user_id}")
                    await streamEventResponse.send_response(response=ResponseKey.WAITING_FOR_FURTHER_AUDIO)
                    audio_snapshot = streamEvent.getAudioBufferBytes()
                    streamEvent.resetAudioBuffer()
                    streamEvent.startStreamResponse(
                        streamResponse=state.stream_client.stream_response,
                        audio_bytes=audio_snapshot,
                    )

                # AI State Tracking
                elif msg_type == "AIStartSpeakingEvent":
                    state.is_ai_speaking = True
                
                elif msg_type == "AIStopSpeakingEvent":
                    stream_id = payload.get("streamId")
                    print(f"Received AIStopSpeakingEvent for user_id={user_id}, streamId={stream_id}")
                    
                    # Validate streamId before unlocking the stream
                    if stream_id is None or stream_id == streamEvent.current_stream_id:
                        state.is_ai_speaking = False
                    else:
                        print(f"Ignoring stale AIStopSpeakingEvent (expected {streamEvent.current_stream_id}, got {stream_id})")

    except WebSocketDisconnect:
        state.audio_socket = None
    finally:
        state.is_user_speaking = False
        state.is_ai_speaking = False
        if state.stream_client:
            await state.stream_client.shutdown()
