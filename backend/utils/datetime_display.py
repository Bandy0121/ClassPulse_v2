"""
将库内 naive UTC 时间格式化为前端展示的东八区时间。

DateTime 列按 datetime.utcnow 写入且无 tz 信息时，按 UTC 解释再转换。
统计按「自然日」聚合时使用 local_date_to_utc_naive_range，与东八区日历对齐。
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from typing import Optional, Tuple

UTC = timezone.utc
DISPLAY_TZ = timezone(timedelta(hours=8))


def format_stored_utc_as_local(
    dt: Optional[datetime],
    fmt: str = '%Y-%m-%d %H:%M:%S',
) -> Optional[str]:
    """
    naive UTC（或 aware）格式化为东八区时间字符串。

    Args:
        dt: 数据库取出的时间；naive 时视为 UTC。
        fmt: strftime 格式。

    Returns:
        格式化字符串；dt 为 None 时返回 None。
    """
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(DISPLAY_TZ).strftime(fmt)
    aware_utc = dt.replace(tzinfo=UTC)
    return aware_utc.astimezone(DISPLAY_TZ).strftime(fmt)


def local_today() -> date:
    """东八区当前日历日期。"""
    return datetime.now(DISPLAY_TZ).date()


def parse_client_datetime_to_utc_naive(value) -> datetime:
    """
    解析教师/学生端提交的时间字符串，得到与库内一致的 **UTC naive**。

    - 字符串 **不带时区**（如前端 ``YYYY-MM-DD HH:mm:ss``）：按 **东八区** 理解，再转为 UTC。
    - 带 ``Z`` 或 ``±HH:MM``：按标注时区解析后转 UTC。

    与 ``format_stored_utc_as_local`` 配对：先按本函数入库，再按该函数展示，界面与库内 UTC 一致。
    """
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
    """
    东八区某日 00:00:00～23:59:59.999999 对应的 naive UTC 起止，用于与库内 UTC naive 字段比较。
    """
    start_local = datetime.combine(d, datetime.min.time(), tzinfo=DISPLAY_TZ)
    end_local = datetime.combine(d, datetime.max.time(), tzinfo=DISPLAY_TZ)
    start_utc = start_local.astimezone(UTC).replace(tzinfo=None)
    end_utc = end_local.astimezone(UTC).replace(tzinfo=None)
    return start_utc, end_utc
