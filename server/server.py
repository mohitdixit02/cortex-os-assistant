import asyncio
from utility.config import load_config
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from cortex.main import listen_and_respond
import json
import io
import wave

app = FastAPI()

load_config()

def pcm16le_to_wav_bytes(pcm_bytes: bytes, sample_rate: int = 16000, channels: int = 1) -> bytes:
    with io.BytesIO() as wav_buffer:
        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_bytes)
        return wav_buffer.getvalue()

# input
# ws.send(JSON.stringify({ type: "start", mime: recorder.mimeType }));

# temp reference
# start_conversation - conversation start signal
# interruption : event = speech-start - user starts speaking
# interruption : event = speech-end - user stops speaking
# end_conversation - conversation end signal
# close_connection - signal to close websocket connection from client side

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    is_user_speaking = False
    audio_buffer = bytearray()
    send_lock = asyncio.Lock()
    response_task: asyncio.Task | None = None
    response_cancel_event: asyncio.Event | None = None

    async def send_json(payload: dict):
        async with send_lock:
            await websocket.send_json(payload)

    async def send_bytes(payload: bytes):
        async with send_lock:
            await websocket.send_bytes(payload)

    async def cancel_response(reason: str):
        nonlocal response_task, response_cancel_event
        if response_cancel_event is not None:
            response_cancel_event.set()

        if response_task is not None and not response_task.done():
            print(f"Cancelling current response task: {reason}")
            response_task.cancel()
            try:
                await response_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                print("Response task cancellation error:", e)

        response_task = None
        response_cancel_event = None

    async def stream_response(wav_bytes: bytes, cancel_event: asyncio.Event):
        try:
            await send_json(
                {
                    "type": "audio_meta",
                    "sampleRate": 24000,
                    "channels": 1,
                    "format": "f32le",
                }
            )

            chunk_idx = 0
            async for audio_chunk in listen_and_respond(wav_bytes, cancel_event=cancel_event):
                if cancel_event.is_set():
                    print("Response streaming stopped by cancel event")
                    return
                chunk_idx += 1
                await send_bytes(audio_chunk.tobytes())

            print("Total TTS chunks sent:", chunk_idx)
            if not cancel_event.is_set():
                await send_json({"type": "done"})
        except asyncio.CancelledError:
            print("Response task cancelled")
            raise
        except Exception as e:
            print("Response streaming error:", e)
            await send_json({"type": "error", "message": str(e)})

    try:
        while True:
            res = await websocket.receive()
            if res.get("bytes") is not None:
                if is_user_speaking:
                    print("Adding chunk of audio data to buffer, size:", len(res.get("bytes")))
                    audio_buffer.extend(res.get("bytes"))
                continue

            text_payload = res.get("text")
            if text_payload is None:
                continue

            if text_payload == "close_connection":
                print("Received close connection signal, closing websocket")
                await cancel_response("client requested close")
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
                audio_buffer.clear()
                await send_json({"type": "acknowledged", "stage": "started"})
            
            if msg_type == "interruption":
                event = payload.get("event")
                print(f"Received interruption event: {event}")
                if event == "speech-start":
                    print("User started speaking, clearing audio buffer for new input")
                    await cancel_response("barge-in speech-start")
                    audio_buffer.clear()
                    is_user_speaking = True
                    await send_json({"type": "new audio starts listening", "stage": f"interruption_{event}"})
                elif event == "speech-end":
                    print("User stopped speaking, ready to process audio buffer of size:", len(audio_buffer))
                    is_user_speaking = False
                    await send_json({"type": "finished listening", "stage": f"interruption_{event}"})
                    
                    if not audio_buffer or len(audio_buffer) == 0:
                        print("No audio data received during interruption, sending error response")
                        await send_json({"type": "error", "message": "No audio data received during interruption"})
                    else:
                        wav_bytes = pcm16le_to_wav_bytes(bytes(audio_buffer), sample_rate=16000, channels=1)
                        await cancel_response("new speech-end request")
                        response_cancel_event = asyncio.Event()
                        response_task = asyncio.create_task(stream_response(wav_bytes, response_cancel_event))
                        audio_buffer.clear()
            
            if msg_type == "end_conversation":
                print("Received stop signal, processing complete audio data of size:", len(audio_buffer))
                await cancel_response("end_conversation")
                audio_buffer.clear()
                await send_json({"type": "acknowledged", "stage": "ended"})

            if msg_type == "close_connection":
                print("Received close connection signal, closing websocket")
                await cancel_response("close_connection message")
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
        await cancel_response("websocket endpoint finalized")
