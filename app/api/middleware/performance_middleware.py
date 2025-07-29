"""Performance middleware for API rate limiting and timeout handling."""

import asyncio
import logging
import time
from collections import defaultdict
from typing import Any

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.api.middleware.agent_error_handler import AgentTimeoutError

logger = logging.getLogger(__name__)

# Rate limiting storage (in production, use Redis or similar)
request_counts: dict[str, dict[str, tuple[int, float]]] = defaultdict(
    lambda: defaultdict(lambda: (0, 0.0))
)

# Rate limits per endpoint pattern
RATE_LIMITS = {
    "/v1/documents/upload": {"requests": 10, "window": 60},  # 10 requests per minute
    "/v1/questionnaire/generate": {
        "requests": 20,
        "window": 60,
    },  # 20 requests per minute
    "/v1/admin/agents": {
        "requests": 100,
        "window": 60,
    },  # 100 requests per minute for admin
    "default": {"requests": 100, "window": 60},  # Default limit
}

# Timeout settings per endpoint pattern (in seconds)
TIMEOUTS = {
    "/v1/documents/upload": 30,  # 30 seconds for document processing
    "/v1/questionnaire/generate": 15,  # 15 seconds for questionnaire generation
    "/v1/admin/": 5,  # 5 seconds for admin operations
    "default": 10,  # Default timeout
}


def get_client_id(request: Request) -> str:
    """Extract client identifier from request."""
    # Try to get user ID from headers or use IP address
    client_id = request.headers.get("X-User-ID")
    if not client_id:
        client_id = request.client.host if request.client else "unknown"
    return client_id


def get_rate_limit_key(path: str) -> str:
    """Get rate limit configuration key for path."""
    for pattern in RATE_LIMITS.keys():
        if pattern != "default" and path.startswith(pattern):
            return pattern
    return "default"


def get_timeout_key(path: str) -> str:
    """Get timeout configuration key for path."""
    for pattern in TIMEOUTS.keys():
        if pattern != "default" and path.startswith(pattern):
            return pattern
    return "default"


def check_rate_limit(client_id: str, path: str) -> bool:
    """Check if request is within rate limits."""
    current_time = time.time()
    rate_key = get_rate_limit_key(path)
    config = RATE_LIMITS[rate_key]

    # Get current count and window start time
    count, window_start = request_counts[client_id][rate_key]

    # Reset window if expired
    if current_time - window_start >= config["window"]:
        request_counts[client_id][rate_key] = (1, current_time)
        return True

    # Check if within limit
    if count < config["requests"]:
        request_counts[client_id][rate_key] = (count + 1, window_start)
        return True

    return False


async def performance_middleware(request: Request, call_next: Any) -> JSONResponse:
    """Middleware for performance requirements including timeouts and rate limiting."""

    # Skip middleware for health check endpoints
    if request.url.path in ["/", "/health", "/docs", "/openapi.json"]:
        return await call_next(request)

    client_id = get_client_id(request)
    path = request.url.path

    # Rate limiting check
    if not check_rate_limit(client_id, path):
        rate_key = get_rate_limit_key(path)
        config = RATE_LIMITS[rate_key]
        logger.warning(f"Rate limit exceeded for client {client_id} on path {path}")

        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": "rate_limit_exceeded",
                "message": (
                    f"Rate limit exceeded. Maximum {config['requests']} requests "
                    f"per {config['window']} seconds."
                ),
                "retry_after": config["window"],
            },
            headers={
                "Retry-After": str(config["window"]),
                "X-RateLimit-Limit": str(config["requests"]),
                "X-RateLimit-Window": str(config["window"]),
            },
        )

    # Get timeout for this endpoint
    timeout_key = get_timeout_key(path)
    timeout_seconds = TIMEOUTS[timeout_key]

    # Execute request with timeout
    start_time = time.time()
    try:
        response = await asyncio.wait_for(call_next(request), timeout=timeout_seconds)

        # Add performance headers
        processing_time = time.time() - start_time
        response.headers["X-Processing-Time"] = str(round(processing_time, 3))
        response.headers["X-Timeout-Limit"] = str(timeout_seconds)

        return response

    except TimeoutError:
        processing_time = time.time() - start_time
        logger.error(
            f"Request timeout after {processing_time:.2f}s for {path} "
            f"(limit: {timeout_seconds}s)"
        )

        return JSONResponse(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            content={
                "error": "request_timeout",
                "message": f"Request timed out after {timeout_seconds} seconds",
                "timeout_limit": timeout_seconds,
                "processing_time": round(processing_time, 3),
            },
        )

    except Exception as e:
        processing_time = time.time() - start_time
        logger.error(
            f"Error during request processing: {str(e)} (time: {processing_time:.2f}s)"
        )
        raise


async def timeout_wrapper(
    coro, timeout_seconds: float, operation_name: str = "operation"
) -> Any:
    """Wrapper to add timeout to any async operation."""
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except TimeoutError as e:
        raise AgentTimeoutError(
            f"{operation_name} timed out after {timeout_seconds} seconds",
            error_code="OPERATION_TIMEOUT",
        ) from e


def get_performance_metrics() -> dict[str, Any]:
    """Get current performance metrics."""
    current_time = time.time()
    active_clients = 0
    total_requests = 0

    for _client_id, client_data in request_counts.items():
        client_active = False
        for rate_key, (_count, window_start) in client_data.items():
            if current_time - window_start < RATE_LIMITS[rate_key]["window"]:
                total_requests += _count
                if not client_active:
                    active_clients += 1
                    client_active = True

    return {
        "active_clients": active_clients,
        "total_requests": total_requests,
        "rate_limits": RATE_LIMITS,
        "timeouts": TIMEOUTS,
    }


def cleanup_expired_entries() -> None:
    """Clean up expired rate limiting entries."""
    current_time = time.time()
    clients_to_remove = []

    for client_id, client_data in request_counts.items():
        keys_to_remove = []
        for rate_key, (_count, window_start) in client_data.items():
            if current_time - window_start >= RATE_LIMITS[rate_key]["window"]:
                keys_to_remove.append(rate_key)

        for key in keys_to_remove:
            del client_data[key]

        if not client_data:
            clients_to_remove.append(client_id)

    for client_id in clients_to_remove:
        del request_counts[client_id]
