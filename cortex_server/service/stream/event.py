import asyncio
from fastapi import WebSocket
from enum import Enum
from typing import Awaitable, Callable

from .state_manager import voice_state_manager

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
    audio_buffer: bytearray
    transcribed_buffer: list[str]
    send_lock: asyncio.Lock
    response_task: asyncio.Task | None
    response_cancel_event: asyncio.Event | None
    current_stream_id: int
    user_id: str | None
    session_id: str | None
    detected_language: str | None

    def __init__(self, user_id: str | None = None):
        self.audio_buffer = bytearray()
        self.transcribed_buffer = []
        self.send_lock = asyncio.Lock()
        self.response_task = None
        self.response_cancel_event = None
        self.current_stream_id = 0
        self.user_id = user_id
        self.session_id = None
        self.detected_language = None

    def increment_stream_id(self) -> int:
        """Generate a new unique ID for the next audio stream."""
        self.current_stream_id += 1
        return self.current_stream_id

    @property
    def user_state(self):
        if not self.user_id:
            return None
        return voice_state_manager.get_state(self.user_id)
    
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
        return bool(self.response_cancel_event and self.response_cancel_event.is_set())
    
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
    
    # ***** Transcribed Buffer Management ***** #
    def appendTranscribedBuffer(self, text: str):
        """Append transcribed text to the buffer."""
        if text and text.strip():
            self.transcribed_buffer.append(text.strip())
            
    def getTranscribedText(self) -> str:
        """Get the combined transcribed text from the buffer."""
        return " ".join(self.transcribed_buffer)
        
    def resetTranscribedBuffer(self):
        """Clear the transcribed buffer."""
        self.transcribed_buffer.clear()
    
    # ***** User Speaking State Management ***** #
    def isUserSpeaking(self) -> bool:
        """Check if the user is currently speaking, used to manage conversation flow and interruptions."""
        state = self.user_state
        return state.is_user_speaking if state else False

    def setUserSpeaking(self, speaking: bool):
        """Set the user's speaking status"""
        state = self.user_state
        if state:
            state.is_user_speaking = speaking
    
    # ***** Response Task Management ***** #
    def startStreamResponse(self, streamResponse: Callable[..., Awaitable[None]], *args, **kwargs):
        """**Start the asynchronous task for generating and sending responses based on the current conversation state.** \n
        This method initializes the response task and cancellation event, and should be called when starting to process a new conversation or after an interruption."""
        # Cancel previous task if exists
        if self.response_task is not None and not self.response_task.done():
            self.response_task.cancel()
            
        self.response_cancel_event = asyncio.Event()
        self.response_task = asyncio.create_task(streamResponse(*args, **kwargs))

class ResponseKey(str, Enum):
    """
    Predefined response keys for standardizing the types of responses sent back to the client.
    Use these keys for Websocket Audio Response feature
    """
    CONVERSATION_START = "conversation_start"
    CONVERSATION_END = "conversation_end"
    START_LISTENING = "start_listening"
    FINISH_LISTENING = "finish_listening"
    WAITING_FOR_FURTHER_AUDIO = "waiting_for_further_audio"
    AI_AUDIO_STREAM_START = "ai_audio_stream_start"
    AI_AUDIO_STREAM_END = "ai_audio_stream_end"
    REMINDER_TRIGGERED = "reminder_triggered"
    OPEN_AUDIO_WEBSOCKET = "open_audio_websocket"
    NO_AUDIO = "no_audio"

EVENT_RESPONSE_MAP = {
    ResponseKey.CONVERSATION_START: {
        "status": "ok",
        "type": "conversation",
        "stage": "started",
        "message": "Conversation started, ready to receive audio"
    },
    ResponseKey.CONVERSATION_END: {
        "status": "ok",
        "type": "conversation",
        "stage": "ended",
        "message": "Conversation ended successfully"
    },
    ResponseKey.START_LISTENING: {
        "status": "ok",
        "type": "interruption",
        "stage": "started",
        "message": "User started speaking, ready to receive audio"
    },
    ResponseKey.FINISH_LISTENING: {
        "status": "ok",
        "type": "interruption",
        "stage": "finished",
        "message": "User finished speaking, processing audio"
    },
    ResponseKey.WAITING_FOR_FURTHER_AUDIO: {
        "status": "ok",
        "type": "interruption",
        "stage": "waiting",
        "message": "User paused, waiting for further audio"
    },
    ResponseKey.AI_AUDIO_STREAM_START: {
        "status": "ok",
        "type": "ai_stream",
        "stage": "started",
        "message": "AI started streaming audio"
    },
    ResponseKey.AI_AUDIO_STREAM_END: {
        "status": "ok",
        "type": "ai_stream",
        "stage": "ended",
        "message": "AI finished streaming audio"
    },
    ResponseKey.REMINDER_TRIGGERED: {
        "status": "ok",
        "type": "reminder",
        "stage": "triggered",
        "message": "A reminder has been triggered"
    },
    ResponseKey.OPEN_AUDIO_WEBSOCKET: {
        "status": "ok",
        "type": "audio_socket",
        "stage": "open_request",
        "message": "Requesting to open audio websocket"
    },
    ResponseKey.NO_AUDIO: {
        "status": "error",
        "type": "response",
        "stage": "no_audio",
        "message": "No audio data received"
    }
}
        
class StreamEventResponse:
    """
    ### Stream Event Response \n
    Helper class for sending standardized JSON responses based on predefined response keys. \n
    Check ***`ResponseKey`*** Class for available response keys and their corresponding payloads. \n
    
    **`__init__()`** requires:
    - The current `Websocket object` on which responses will be sent back to the client.
    - The corresponding `StreamEvent object` for handling streaming events.
    """
    
    def __init__(self, websocket: WebSocket | None = None, streamEvent: StreamEvent | None = None):
        self.websocket = websocket
        self.streamEvent = streamEvent
    
    async def send_response(self, response: ResponseKey, message: str | None = None):
        """Send a standardized JSON response based on the provided response key (thread-safe) \n"""
        if response not in EVENT_RESPONSE_MAP:
            raise ValueError(f"Invalid response key: {response}")
        
        payload = EVENT_RESPONSE_MAP[response].copy()
        if message:
            payload["message"] = message

        async with self.streamEvent.getLock():
            await self.websocket.send_json(payload)
