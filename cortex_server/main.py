# Monkey-patch MainTaskQueue to use RemoteTaskQueue
import os
import cortex_queue
from cortex_queue.remote_client import RemoteTaskQueue

# Set this before importing any controller/service that uses MainTaskQueue
os.environ["USE_REMOTE_QUEUE"] = "true"
cortex_queue.MainTaskQueue = RemoteTaskQueue()

from cortex_server.server import app
import uvicorn

if __name__ == "__main__":
    print("Starting Cortex Server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
