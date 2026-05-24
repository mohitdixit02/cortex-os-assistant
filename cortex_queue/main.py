from fastapi import FastAPI
from cortex_queue.controllers.task import task_router
from cortex_queue.service.utility import _get_memory_saver
import uvicorn
from contextlib import asynccontextmanager
from cortex_cm.utility.logger import get_logger
logger = get_logger("TASK_QUEUE")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Pre-initialize memory saver and models on startup
    logger.info("Pre-loading models and memory saver...")
    _get_memory_saver()
    logger.info("Cortex Queue ready.")
    yield

app = FastAPI(title="Cortex Task Queue Service", lifespan=lifespan)
app.include_router(task_router, prefix="/api/queue")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
