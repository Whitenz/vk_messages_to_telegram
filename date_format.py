from datetime import datetime, timezone, timedelta

TIMEZONE = timezone(timedelta(hours=5))


def get_date(timestamp: str) -> str:
    return datetime.fromtimestamp(
        int(timestamp), TIMEZONE).strftime('%d.%m.%Y, %H:%M')
