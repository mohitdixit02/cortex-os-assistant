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
    Reserved strictly for backend-to-client notifications (Reminders).
    All voice interaction logic has been moved to the /audio socket.
    """
    await websocket.accept()
    state = voice_state_manager.get_state(user_id)
    state.event_socket = websocket
    
    try:
        # Keep the connection alive and wait for disconnect
        while True:
            res = await websocket.receive_text()
            print(f"Received on /event socket (user_id={user_id}): {res}")
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
    
    # Use the existing stream_event from state if available
    streamEvent = state.stream_event or StreamEvent(user_id=user_id)
    state.stream_event = streamEvent
    
    streamEventResponse = StreamEventResponse(
        websocket=websocket, # Now sending responses back through the audio socket
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
            
            # Handle Disconnect cleanly
            if res.get("type") == "websocket.disconnect":
                break

            print(f"Received on /audio socket (user_id={user_id}): {res.keys()}")
            if "text" in res:
                print(f"Text payload: {res['text']}")

            # Handle Binary Data (Audio Chunks)
            if res.get("bytes") is not None:
                streamEvent.appendAudioBuffer(res.get("bytes"))
                continue
            
            # Handle Text Data (JSON Events)
            text_payload = res.get("text")
            if text_payload:
                try:
                    payload = json.loads(text_payload)
                except json.JSONDecodeError:
                    continue
                    
                msg_type = payload.get("type")
                
                # 1. Conversation Lifecycle
                if msg_type == "ConversationStart":
                    streamEvent.resetAudioBuffer()
                    streamEvent.session_id = payload.get("session_id")
                    print(f"Sending response key: {ResponseKey.CONVERSATION_START} to user_id={user_id}")
                    await streamEventResponse.send_response(response=ResponseKey.CONVERSATION_START)
                
                elif msg_type == "ConversationEnd":
                    # For end_conversation, we might want to trigger one last process if buffer is full,
                    # or just cleanup.
                    streamEvent.resetAudioBuffer()
                    print(f"Sending response key: {ResponseKey.CONVERSATION_END} to user_id={user_id}")
                    await streamEventResponse.send_response(response=ResponseKey.CONVERSATION_END)

                # 2. VAD & Interruption Events (Migrated from /event)
                elif msg_type == "UserSpeechStartEvent":
                    state.is_user_speaking = True
                    print(f"Sending response key: {ResponseKey.START_LISTENING} to user_id={user_id}")
                    await streamEvent.cancel("User started speaking")
                    await streamEventResponse.send_response(response=ResponseKey.START_LISTENING)
                
                elif msg_type == "UserSpeechEndEvent":
                    state.is_user_speaking = False
                    print(f"Sending response key: {ResponseKey.WAITING_FOR_FURTHER_AUDIO} to user_id={user_id}")
                    await streamEventResponse.send_response(response=ResponseKey.WAITING_FOR_FURTHER_AUDIO)
                    # Trigger processing automatically when user stops speaking
                    audio_snapshot = streamEvent.getAudioBufferBytes()
                    streamEvent.resetAudioBuffer()
                    streamEvent.startStreamResponse(
                        streamResponse=state.stream_client.stream_response,
                        audio_bytes=audio_snapshot,
                    )

                # 3. AI State Tracking
                elif msg_type == "AIStartSpeakingEvent":
                    state.is_ai_speaking = True
                
                elif msg_type == "AIStopSpeakingEvent":
                    stream_id = payload.get("streamId")
                    print(f"Received AIStopSpeakingEvent for user_id={user_id}, streamId={stream_id}")
                    
                    # Validate streamId to prevent stale timeouts from unlocking the stream
                    if stream_id is None or stream_id == streamEvent.current_stream_id:
                        state.is_ai_speaking = False
                    else:
                        print(f"Ignoring stale AIStopSpeakingEvent (expected {streamEvent.current_stream_id}, got {stream_id})")

    except WebSocketDisconnect:
        state.audio_socket = None
    finally:
        if state.stream_client:
            await state.stream_client.shutdown()
