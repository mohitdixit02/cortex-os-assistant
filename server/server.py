import asyncio
import utility.config
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from controller.websocket import router as ws_router
from controller.main import router as main_router

app = FastAPI()

# **************** temp disabled for internal cortex flow testig *************
# app.include_router(ws_router, prefix="/ws")

app.include_router(main_router, prefix="/api")

