from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional, Tuple

UTC = timezone.utc
DISPLAY_TZ = timezone(timedelta(hours=8))


def format_stored_utc_as_local(
    dt: Optional[datetime],
    fmt: str = '%Y-%m-%d %H:%M:%S',
) -> Optional[str]:
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(DISPLAY_TZ).strftime(fmt)
    aware_utc = dt.replace(tzinfo=UTC)
    return aware_utc.astimezone(DISPLAY_TZ).strftime(fmt)


def local_today() -> date:
    return datetime.now(DISPLAY_TZ).date()


def parse_client_datetime_to_utc_naive(value) -> datetime:
    if value is None:
        raise ValueError('empty')
    s = str(value).strip()
    if not s:
        raise ValueError('empty')
    s = s.replace('Z', '+00:00')
    if ' ' in s and len(s) >= 19 and 'T' not in s[:19]:
        s = s.replace(' ', 'T', 1)
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is not None:
        return dt.astimezone(UTC).replace(tzinfo=None)
    return dt.replace(tzinfo=DISPLAY_TZ).astimezone(UTC).replace(tzinfo=None)


def local_date_to_utc_naive_range(d: date) -> Tuple[datetime, datetime]:
    start_local = datetime.combine(d, datetime.min.time(), tzinfo=DISPLAY_TZ)
    end_local = datetime.combine(d, datetime.max.time(), tzinfo=DISPLAY_TZ)
    start_utc = start_local.astimezone(UTC).replace(tzinfo=None)
    end_utc = end_local.astimezone(UTC).replace(tzinfo=None)
    return start_utc, end_utc
