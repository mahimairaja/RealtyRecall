"""A tracing decorator for the agent's @function_tool methods.

Wraps a tool coroutine to emit one structured log line per call (tool name, tenant,
redacted args, a short result summary, latency in ms, ok/failed) and a matching
Sentry breadcrumb, so a booking or search bug is one log query away instead of a
log-tail hunt. It never swallows the tool's return value or its exceptions, and it
preserves the wrapped function's signature (via functools.wraps) so livekit-agents
still generates the correct tool schema.

Apply INSIDE @function_tool::

    @function_tool
    @traced_tool
    async def book_showing(self, context, ...): ...
"""

from __future__ import annotations

import functools
import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

import sentry_sdk

logger = logging.getLogger("agent")

# Argument names whose values are caller PII and must never be logged verbatim.
_REDACT_KEYS = frozenset({"phone", "name"})

R = TypeVar("R")


def _redact(kwargs: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in kwargs.items():
        if key in _REDACT_KEYS:
            out[key] = "***" if value else value
        elif isinstance(value, str) and len(value) > 60:
            out[key] = value[:57] + "..."
        else:
            out[key] = value
    return out


def _summarize(result: Any) -> str:
    text = result if isinstance(result, str) else str(result)
    return text[:80]


def traced_tool(fn: Callable[..., Awaitable[R]]) -> Callable[..., Awaitable[R]]:
    """Trace one async tool method: structured log + Sentry breadcrumb, return/raise
    passed through untouched. ``self`` supplies the tenant; the LLM-filled args arrive
    as kwargs and are redacted before logging."""

    @functools.wraps(fn)
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> R:
        name = fn.__name__
        tenant = getattr(self, "_tenant_id", None)
        redacted = _redact(kwargs)
        start = time.perf_counter()
        try:
            result = await fn(self, *args, **kwargs)
        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            logger.warning(
                "tool %s FAILED tenant=%s latency_ms=%.0f args=%s err=%s",
                name,
                tenant,
                latency_ms,
                redacted,
                exc,
            )
            sentry_sdk.add_breadcrumb(
                category="tool",
                message=name,
                level="error",
                data={
                    "tenant": tenant,
                    "latency_ms": round(latency_ms),
                    "args": redacted,
                },
            )
            raise
        latency_ms = (time.perf_counter() - start) * 1000
        logger.info(
            "tool %s ok tenant=%s latency_ms=%.0f args=%s result=%r",
            name,
            tenant,
            latency_ms,
            redacted,
            _summarize(result),
        )
        sentry_sdk.add_breadcrumb(
            category="tool",
            message=name,
            level="info",
            data={"tenant": tenant, "latency_ms": round(latency_ms), "args": redacted},
        )
        return result

    return wrapper
