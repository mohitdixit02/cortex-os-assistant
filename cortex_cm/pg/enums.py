from enum import Enum

class RoleType(str, Enum):
    USER = "USER"
    AI = "AI"

class AIClientType(str, Enum):
    VOICE_CLIENT = "VOICE_CLIENT"
    CORTEX_MAIN_CLIENT = "CORTEX_MAIN_CLIENT"

class PreferenceLevel(str, Enum):
    MUST = "MUST"
    SHOULD = "SHOULD"
    CAN = "CAN"
    CANNOT = "CANNOT"

class TimeOfDay(str, Enum):
    MORNING = "MORNING"
    AFTERNOON = "AFTERNOON"
    EVENING = "EVENING"
    NIGHT = "NIGHT"

class TaskStatus(str, Enum):
    INITIALIZED = "INITIALIZED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class EventStatus(str, Enum):
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    DONE = "DONE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class TaskOwner(str, Enum):
    VOICE_CLIENT = "VOICE_CLIENT"
    EVENT_TOOL = "EVENT_TOOL"
    OTHER = "OTHER"
