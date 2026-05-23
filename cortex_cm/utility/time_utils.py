from datetime import datetime, timezone
import zoneinfo
from dateutil import tz
from cortex_cm.pg.enums import TimeOfDay

def get_time_of_day(dt: datetime) -> TimeOfDay:
    """Determine the TimeOfDay enum based on the hour of the provided datetime."""
    hour = dt.hour
    if 5 <= hour < 12:
        return TimeOfDay.MORNING
    elif 12 <= hour < 17:
        return TimeOfDay.AFTERNOON
    elif 17 <= hour < 21:
        return TimeOfDay.EVENING
    else:
        return TimeOfDay.NIGHT

def _get_tz(timezone_str: str):
    """Internal helper to get timezone object with fallback to dateutil."""
    try:
        return zoneinfo.ZoneInfo(timezone_str)
    except Exception:
        # Fallback for Windows or systems without tzdata
        return tz.gettz(timezone_str)

def get_local_time(dt: datetime, timezone_str: str) -> datetime:
    """Convert a datetime to a specific timezone."""
    try:
        target_tz = _get_tz(timezone_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(target_tz)
    except Exception:
        # Fallback if both fail
        return dt

def get_utc_time(dt: datetime, timezone_str: str) -> datetime:
    """Convert a local datetime to UTC, ignoring any existing timezone offset on the object."""
    try:
        target_tz = _get_tz(timezone_str)
        # Always strip existing tzinfo to ensure we use the provided timezone_str as the source of truth
        dt = dt.replace(tzinfo=None)
        dt = dt.replace(tzinfo=target_tz)
        return dt.astimezone(timezone.utc)
    except Exception:
        return dt

def parse_iso_to_utc(iso_str: str, timezone_str: str) -> datetime:
    """Parse an ISO format string and convert it to UTC based on the provided timezone."""
    try:
        dt = datetime.fromisoformat(iso_str)
        return get_utc_time(dt, timezone_str)
    except Exception:
        return datetime.now(timezone.utc)

UTC_NOW = lambda: datetime.now(timezone.utc)
