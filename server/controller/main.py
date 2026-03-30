import asyncio

from fastapi.routing import APIRouter
from pydantic import BaseModel
from cortex.voice import VoiceClient
from fastapi.responses import StreamingResponse
from logger import logger

router = APIRouter()
voice_client = VoiceClient()

class QueryRequest(BaseModel):
    query: str

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

@router.post("/query/")
async def query_endpoint(request: QueryRequest):
    """Process user query and stream response tokens."""
    logger.info("Processing query: %s", request.query)
    
    response = ""
    async for token in voice_client.read_and_respond(request.query):
        response += token
        logger.info("Generated token: %s", token)
        
    logger.info("Final response: %s", response)
    return {"response": response}
    
    # async def response_stream():
    #     try:
    #         async for token in voice_client.read_and_respond(request.query):
    #             # SSE frame format: one event per token chunk
    #             yield f"data: {token}\n\n"
    #     except Exception as e:
    #         logger.error("Error streaming response: %s", e)
    #         yield f"event: error\ndata: {str(e)}\n\n"

    # return StreamingResponse(
    #     response_stream(),
    #     media_type="text/event-stream",
    #     headers={
    #         "Cache-Control": "no-cache",
    #         "Connection": "keep-alive",
    #         "X-Accel-Buffering": "no",
    #     },
    # )
