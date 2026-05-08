from fastapi import FastAPI
from cortex_queue.controllers.task import task_router
import uvicorn

app = FastAPI(title="Cortex Task Queue Service")
app.include_router(task_router, prefix="/api/queue")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
