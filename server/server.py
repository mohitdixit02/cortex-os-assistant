import os
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
import json

app = FastAPI()

load_dotenv()
cache_dir = os.getenv("HF_CACHE_DIR", "./hf_cache")
os.environ['HF_HOME'] = cache_dir
os.environ['TRANSFORMERS_CACHE'] = cache_dir
os.environ['HF_DATASETS_CACHE'] = cache_dir
os.environ["SENTENCE_TRANSFORMERS_HOME"] = cache_dir
os.makedirs(cache_dir, exist_ok=True)

from cortex.main import listen_and_respond

# input
# ws.send(JSON.stringify({ type: "start", mime: recorder.mimeType }));

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()

    audio_buffer = bytearray()
    while True:
        res = await websocket.receive()
        if res.get("bytes") is not None:
            print("Adding chunk of audio data to buffer, size:", len(res.get("bytes")))
            audio_buffer.extend(res.get("bytes"))
            continue
        
        if res.get("text") is not None:
            payload = json.loads(res.get("text"))
            msg_type = payload.get("type")
            if msg_type == "start":
                print("Received start signal, initializing audio buffer")
                audio_buffer.clear()
                await websocket.send_json({"type": "ack", "stage": "started"})
                
            if msg_type == "stop":
                print("Received stop signal, processing complete audio data of size:", len(audio_buffer))
                # audio bytes
                if not audio_buffer or len(audio_buffer) == 0:
                    print("No audio data received, sending error response")
                    await websocket.send_json({"type": "error", "message": "No audio data received"})
                    continue
            
                text_generator = listen_and_respond(bytes(audio_buffer))

                await websocket.send_json(
                    {
                        "type": "audio_meta",
                        "sampleRate": 24000,
                        "channels": 1,
                        "format": "f32le",
                    }
                )

                chunk_idx = 0
                async for audio_chunk in text_generator:
                    chunk_idx += 1
                    await websocket.send_bytes(audio_chunk.tobytes())
                print("Total TTS chunks sent:", chunk_idx)
                
                await websocket.send_json({"type": "done"})
                audio_buffer.clear()