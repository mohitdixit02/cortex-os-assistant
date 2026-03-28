import asyncio
from fastapi import WebSocket
from enum import Enum
from typing import Callable

class StreamEvent:
    """
        ***This Class manages the state and data of an ongoing conversation stream between a User and an AI Application.***\n 
        Tracks whether the user is currently speaking, buffers incoming audio data, and manages asynchronous tasks for processing, interrupting, and responding to the conversation in real-time. 
        
        **Key Parameters**:
        - is_user_speaking: A boolean indicating whether the user is currently speaking.
        - audio_buffer: A bytearray for buffering incoming audio data.
        - send_lock: An asyncio.Lock for synchronizing sending operations.
        - response_task: An asyncio.Task for managing the asynchronous response task.
        - response_cancel_event: An asyncio.Event for signaling cancellation of the response task.
    """
    is_user_speaking: bool
    audio_buffer: bytearray
    send_lock: asyncio.Lock
    response_task: asyncio.Task | None
    response_cancel_event: asyncio.Event | None

    def __init__(self):
        self.is_user_speaking = False
        self.audio_buffer = bytearray()
        self.send_lock = asyncio.Lock()
        self.response_task = None
        self.response_cancel_event = None
    
    # ***** Response Event Management ***** #
    async def cancel(self, reason: str):
        """
        Cancel the current response task and signal any ongoing operations to stop. \n
        Typically called when an interruption occurs (e.g., user starts speaking) or when the conversation ends.
        """
        if self.response_cancel_event is not None:
            self.response_cancel_event.set()

        if self.response_task is not None and not self.response_task.done():
            print(f"Cancelling current response task: {reason}")
            self.response_task.cancel()
            try:
                await self.response_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                print("Response task cancellation error:", e)

        self.response_task = None
        self.response_cancel_event = None
        
    def isCancelEventSet(self) -> bool:
        """Check if the response cancel event is set, indicating that the current response task should be cancelled."""
        return self.response_cancel_event.is_set()
    
    def getLock(self) -> asyncio.Lock:
        """Get the asyncio lock for synchronizing send operations. This lock should be acquired before sending any messages to ensure thread safety."""
        return self.send_lock
    
    # ***** Audio Buffer Management ***** #
    def appendAudioBuffer(self, data: bytes):
        """Append incoming audio data to the buffer. This method is typically called when new audio data is received from the user during a conversation stream."""
        self.audio_buffer.extend(data)
        
    def resetAudioBuffer(self):
        """Clear the audio buffer. This method is typically called when starting a new conversation or after processing the current audio data to prepare for new input."""
        self.audio_buffer.clear()
        
    def getAudioBufferBytes(self) -> bytes:
        """Get the current contents of the audio buffer as bytes. This method is typically called when processing the buffered audio data for transcription or other analysis."""
        return bytes(self.audio_buffer)
        
    def isAudioBuffer(self) -> bool:
        """Check if there is any audio data in the buffer"""
        if not self.audio_buffer or len(self.audio_buffer) == 0:
            return False
        return True
    
    def getAudioBufferSize(self) -> int:
        """Get the current size of the audio buffer"""
        return len(self.audio_buffer)
    
    # ***** User Speaking State Management ***** #
    def isUserSpeaking(self) -> bool:
        """Check if the user is currently speaking, used to manage conversation flow and interruptions."""
        return self.is_user_speaking

    def setUserSpeaking(self, speaking: bool):
        """Set the user's speaking status"""
        self.is_user_speaking = speaking
    
    # ***** Response Task Management ***** #
    def startStreamResponse(self, streamResponse: Callable, *args, **kwargs):
        """**Start the asynchronous task for generating and sending responses based on the current conversation state.** \n
        This method initializes the response task and cancellation event, and should be called when starting to process a new conversation or after an interruption."""
        self.response_cancel_event = asyncio.Event()
        self.response_task = asyncio.create_task(streamResponse(*args, **kwargs))
        self.resetAudioBuffer()

class ResponseKey(str, Enum):
    """
    Predefined response keys for standardizing the types of responses sent back to the client.
    Use these keys for Websocket Audio Response feature
    """
    CONVERSATION_START = "conversation_start"
    CONVERSATION_END = "conversation_end"
    START_LISTENING = "start_listening"
    FINISH_LISTENING = "finish_listening"
    NO_AUDIO = "no_audio"

EVENT_RESPONSE_MAP = {
    "conversation_start": {
        "status": "ok",
        "type": "conversation",
        "stage": "started",
        "message": "Conversation started, ready to receive audio"
    },
    "conversation_end": {
        "status": "ok",
        "type": "conversation",
        "stage": "ended",
        "message": "Conversation ended successfully"
    },
    "start_listening": {
        "status": "ok",
        "type": "interruption",
        "stage": "started",
        "message": "User started speaking, ready to receive audio"
    },
    "finish_listening": {
        "status": "ok",
        "type": "interruption",
        "stage": "finished",
        "message": "User finished speaking, processing audio"
    },
    "no_audio": {
        "status": "error",
        "type": "response",
        "stage": "no_audio",
        "message": "No audio data received"
    }
}
        
class StreamEventResponse:
    """
    Helper class for sending standardized JSON responses based on predefined response keys. \n
    Check ***`ResponseKey`*** Class for available response keys and their corresponding payloads. \n
    """
    
    def __init__(self, websocket: WebSocket | None = None, streamEvent: StreamEvent | None = None):
        self.websocket = websocket
        self.streamEvent = streamEvent
    
    async def send_response(self, response: str):
        """Send a standardized JSON response based on the provided response key (thread-safe) \n"""
        if response not in EVENT_RESPONSE_MAP.keys():
            raise ValueError(f"Invalid response key: {response}")
        
        response = EVENT_RESPONSE_MAP[response]

        async with self.streamEvent.getLock():
            await self.websocket.send_json(response)
