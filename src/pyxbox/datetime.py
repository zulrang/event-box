from datetime import datetime, timedelta, timezone


def utcnow() -> datetime:
    """Get the current JSON serializable UTC datetime with millisecond precision."""
    now = datetime.now(timezone.utc)
    ms = round(now.microsecond, -3)
    if ms >= 1000000:
        ms = 0
        now += timedelta(seconds=1)
    return now.replace(microsecond=ms).replace(tzinfo=None)
