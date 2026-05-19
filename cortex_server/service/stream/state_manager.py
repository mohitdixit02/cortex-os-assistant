import asyncio
from typing import Dict
from dataclasses import dataclass, field

@dataclass
class UserVoiceState:
    is_user_speaking: bool = False
    is_ai_speaking: bool = False
    stream_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    event_socket: any = None  # Store WebSocket object for event stream
    audio_socket: any = None  # Store WebSocket object for audio stream
    stream_event: any = None  # Store active StreamEvent object
    stream_client: any = None # Store active StreamClient object
    audio_ws_opened_event: asyncio.Event = field(default_factory=asyncio.Event)
    audio_ws_success: bool = False

class VoiceStateManager:
    _instance = None
    _states: Dict[str, UserVoiceState] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VoiceStateManager, cls).__new__(cls)
        return cls._instance

    def get_state(self, user_id: str) -> UserVoiceState:
        if user_id not in self._states:
            self._states[user_id] = UserVoiceState()
        return self._states[user_id]

    def remove_state(self, user_id: str):
        if user_id in self._states:
            del self._states[user_id]

voice_state_manager = VoiceStateManager()
