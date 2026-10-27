
from datetime import datetime, timezone
from time import perf_counter

import requests


def check_http_service(
    name: str,
    url: str,
    timeout: float = 3.0,
) -> dict:
    """Check an HTTP service and return its operational status."""
    checked_at = datetime.now(timezone.utc).isoformat()
    started = perf_counter()

    try:
        response = requests.get(url, timeout=timeout)
        response_time_ms = round(
            (perf_counter() - started) * 1000,
            2,
        )

        healthy = 200 <= response.status_code < 400

        return {
            "name": name,
            "url": url,
            "status": "healthy" if healthy else "unhealthy",
            "status_code": response.status_code,
            "response_time_ms": response_time_ms,
            "checked_at": checked_at,
            "error": None,
        }

    except requests.RequestException as exc:
        response_time_ms = round(
            (perf_counter() - started) * 1000,
            2,
        )

        return {
            "name": name,
            "url": url,
            "status": "unhealthy",
            "status_code": None,
            "response_time_ms": response_time_ms,
            "checked_at": checked_at,
            "error": type(exc).__name__,
        }
