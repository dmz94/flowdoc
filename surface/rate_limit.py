"""
In-memory per-IP rate limiter and concurrent fetch limiter.
"""
import threading
import time

import config


class RateLimitError(Exception):
    """Client has exceeded the rate limit."""
    error_type = "rate_limit"

    @property
    def user_message(self) -> str:
        return (
            "You've converted several pages recently. "
            "Please wait a few minutes before trying again."
        )


# ---------------------------------------------------------------------------
# Per-IP rate limiting
# ---------------------------------------------------------------------------

_lock = threading.Lock()
_requests: dict[str, list[float]] = {}


def check_rate_limit(ip: str) -> bool:
    """
    Check if a request from this IP is allowed.

    Returns True if allowed, False if rate limited.
    Cleans up stale entries on each call.
    """
    now = time.monotonic()
    cutoff = now - config.RATE_LIMIT_WINDOW_SECONDS

    with _lock:
        # Cleanup stale entries
        stale_keys = [
            k for k, timestamps in _requests.items()
            if not timestamps or timestamps[-1] < cutoff
        ]
        for k in stale_keys:
            del _requests[k]

        # Check and update this IP
        timestamps = _requests.get(ip, [])
        timestamps = [t for t in timestamps if t >= cutoff]

        if len(timestamps) >= config.RATE_LIMIT_MAX_REQUESTS:
            _requests[ip] = timestamps
            return False

        timestamps.append(now)
        _requests[ip] = timestamps
        return True


# ---------------------------------------------------------------------------
# Concurrent fetch limiter
# ---------------------------------------------------------------------------

_fetch_semaphore = threading.Semaphore(config.MAX_CONCURRENT_FETCHES)


def acquire_fetch_slot() -> bool:
    """Try to acquire a fetch slot (non-blocking). Returns True if acquired."""
    return _fetch_semaphore.acquire(blocking=False)


def release_fetch_slot() -> None:
    """Release a previously acquired fetch slot."""
    _fetch_semaphore.release()
