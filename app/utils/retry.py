"""Retry utility — tenacity is optional, falls back to simple retry loop."""
from __future__ import annotations
import asyncio
import logging
from functools import wraps
from typing import Any, Callable, Tuple, Type

logger = logging.getLogger(__name__)

try:
    from tenacity import (
        AsyncRetrying, retry_if_exception_type,
        stop_after_attempt, wait_exponential,
    )
    def async_retry(max_attempts=3, min_wait=1.0, max_wait=10.0,
                    exceptions=(Exception,)):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                async for attempt in AsyncRetrying(
                    stop=stop_after_attempt(max_attempts),
                    wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
                    retry=retry_if_exception_type(exceptions),
                    reraise=True,
                ):
                    with attempt:
                        return await func(*args, **kwargs)
            return wrapper
        return decorator

except ImportError:
    def async_retry(max_attempts=3, min_wait=1.0, max_wait=10.0,
                    exceptions=(Exception,)):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                last_exc = None
                for attempt in range(max_attempts):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as e:
                        last_exc = e
                        if attempt < max_attempts - 1:
                            await asyncio.sleep(min(min_wait * (2 ** attempt), max_wait))
                raise last_exc
            return wrapper
        return decorator
