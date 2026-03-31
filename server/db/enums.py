from enum import Enum

class RoleType(str, Enum):
    USER = "USER"
    AI = "AI"

class AIClientType(str, Enum):
    VOICE_CLIENT = "VOICE_CLIENT"
    CORE_MAIN_CLIENT = "CORE_MAIN_CLIENT"

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

class TraitCategory(str, Enum):
    LIKE = "LIKE"
    DISLIKE = "DISLIKE"
    HABIT = "HABIT"
    FACT = "FACT"
    STRICT_PREFERENCE = "STRICT_PREFERENCE"

class MoodTrend(str, Enum):
    STABLE = "STABLE"
    INCREASING = "INCREASING"
    DECREASING = "DECREASING"

class TaskStatus(str, Enum):
    INITIALIZED = "INITIALIZED"
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
