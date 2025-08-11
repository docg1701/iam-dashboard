"""
Custom logging middleware for request/response logging.
"""
import time
import uuid
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Start timing
        start_time = time.time()
        
        # Add request ID to context
        with structlog.contextvars.bound_contextvars(request_id=request_id):
            # Log incoming request
            logger.info(
                "Incoming request",
                method=request.method,
                url=str(request.url),
                client_ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
            )
            
            # Process request
            try:
                response = await call_next(request)
                
                # Calculate processing time
                process_time = time.time() - start_time
                
                # Log response
                logger.info(
                    "Request completed",
                    status_code=response.status_code,
                    process_time_ms=round(process_time * 1000, 2),
                )
                
                # Add request ID to response headers
                response.headers["X-Request-ID"] = request_id
                
                return response
                
            except Exception as e:
                # Calculate processing time for failed requests
                process_time = time.time() - start_time
                
                # Log error
                logger.error(
                    "Request failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    process_time_ms=round(process_time * 1000, 2),
                )
                
                # Re-raise the exception
                raise