import cortex_cm.utility.config
from fastapi import FastAPI
from cortex_server.controller.websocket import router as ws_router
from cortex_server.controller.main import router as main_router
from cortex_server.controller.auth import router as auth_router
from cortex_server.controller.chat_controller import router as chat_router
from cortex_server.controller.task_controller import router as task_router
from cortex_server.controller.event_controller import router as event_router
from cortex_server.controller.config_controller import router as config_router
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from cortex_server.service.stream.result_worker import result_stream_worker
import uvicorn

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the background result worker
    result_stream_worker.start()
    yield
    # Shutdown: Stop the background result worker
    await result_stream_worker.stop()

app = FastAPI(lifespan=lifespan)

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
app.include_router(event_router, prefix="/api")
app.include_router(config_router, prefix="/api")

if __name__ == "__main__":
    print("Starting Cortex Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
