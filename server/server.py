import asyncio
from utility.config import load_config
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from controller.websocket import router as ws_router

load_config()
app = FastAPI()
app.include_router(ws_router, prefix="/ws")

