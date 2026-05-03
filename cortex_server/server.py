import asyncio
import cortex_cm.utility.config
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from cortex_server.controller.websocket import router as ws_router
from cortex_server.controller.main import router as main_router
from cortex_server.controller.auth import router as auth_router
from cortex_server.controller.chat_controller import router as chat_router
from cortex_server.controller.task_controller import router as task_router
from cortex_server.controller.user_controller import router as user_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins="http://localhost:3000",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ws_router, prefix="/ws")
app.include_router(main_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(chat_router, prefix="/api")
app.include_router(task_router, prefix="/api")
app.include_router(user_router, prefix="/api")

