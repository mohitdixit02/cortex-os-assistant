from fastapi.routing import APIRouter
from fastapi import WebSocket, WebSocketDisconnect
from service.stream.event import StreamEvent, ResponseKey, StreamEventResponse
from service.stream.main import StreamClient
import json

router = APIRouter()

@router.websocket("/stream")
async def ws_stream(websocket: WebSocket):
    """
    ***WebSocket endpoint for handling real-time audio streaming and conversation management between User and AI Application.***\n
    **Input**: Binary Audio | JSON | Control Messages \n
    **Output**: JSON Responses indicating conversation state and processing results.
    """
    await websocket.accept()
    streamEvent = StreamEvent()
    streamEventResponse = StreamEventResponse(
        websocket=websocket,
        streamEvent=streamEvent
    )
    streamClient = StreamClient(
        websocket=websocket,
        streamEvent=streamEvent
    )

    try:
        while True:
            res = await websocket.receive()
            if res.get("bytes") is not None:
                if streamEvent.isUserSpeaking():
                    print("Adding chunk of audio data to buffer, size:", len(res.get("bytes")))
                    streamEvent.appendAudioBuffer(res.get("bytes"))
                continue

            text_payload = res.get("text")
            if text_payload is None:
                continue

            if text_payload == "close_connection":
                print("Received close connection signal, closing websocket")
                await streamEvent.cancel("client requested close")
                await websocket.close()
                break

            try:
                payload = json.loads(text_payload)
            except json.JSONDecodeError:
                print("Received non-JSON text payload, ignoring:", text_payload)
                continue

            msg_type = payload.get("type")
            if msg_type == "start_conversation":
                print("Received start signal, initializing audio buffer")
                streamEvent.resetAudioBuffer()
                streamEvent.user_id = payload.get("user_id")
                streamEvent.session_id = payload.get("session_id")
                await streamEventResponse.send_response(response=ResponseKey.CONVERSATION_START)

            if msg_type == "playback_done":
                stream_id = payload.get("streamId")
                try:
                    stream_id = int(stream_id) if stream_id is not None else None
                except (TypeError, ValueError):
                    stream_id = None
                accepted = streamEvent.markPlaybackDone(stream_id=stream_id)
                if not accepted:
                    print(f"Ignoring playback_done for stale streamId={stream_id}")
                continue
            
            if msg_type == "interruption":
                event = payload.get("event")
                print(f"Received interruption event: {event}")
                if event == "speech-start":
                    print("User started speaking, clearing audio buffer for new input")
                    await streamEvent.cancel("barge-in speech-start")
                    streamEvent.resetAudioBuffer()
                    streamEvent.setUserSpeaking(True)
                    await streamEventResponse.send_response(response=ResponseKey.START_LISTENING)
                elif event == "speech-end":
                    print("User stopped speaking, ready to process audio buffer of size:", streamEvent.getAudioBufferSize())
                    streamEvent.setUserSpeaking(False)
                    await streamEventResponse.send_response(response=ResponseKey.FINISH_LISTENING)

                    if not streamEvent.isAudioBuffer():
                        print("No audio data received during interruption, sending error response")
                        await streamEventResponse.send_response(response=ResponseKey.NO_AUDIO)
                    else:
                        audio_snapshot = streamEvent.getAudioBufferBytes()
                        streamEvent.resetAudioBuffer()
                        await streamEvent.cancel("new speech-end request")
                        streamEvent.startStreamResponse(
                            streamResponse=streamClient.stream_response,
                            audio_bytes=audio_snapshot,
                        )

            if msg_type == "end_conversation":
                print("Received stop signal, processing complete audio data of size:", streamEvent.getAudioBufferSize())
                await streamEvent.cancel("end_conversation")
                streamEvent.resetAudioBuffer()
                await streamEventResponse.send_response(response=ResponseKey.CONVERSATION_END)

            if msg_type == "close_connection":
                print("Received close connection signal, closing websocket")
                await streamEvent.cancel("close_connection message")
                await websocket.close()
                break
    except WebSocketDisconnect:
        print("WebSocket disconnected")
    except Exception as e:
        print("WebSocket endpoint error:", e)
        try:
            if websocket.client_state.name != "DISCONNECTED":
                await websocket.close()
        except Exception:
            pass
    finally:
        await streamEvent.cancel("websocket endpoint finalized")
        await streamClient.shutdown()
