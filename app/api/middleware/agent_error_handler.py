"""Agent error handling middleware for consistent API responses."""

import logging
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AgentError(Exception):
    """Base exception for agent-related errors."""

    def __init__(
        self, message: str, agent_id: str | None = None, error_code: str | None = None
    ):
        self.message = message
        self.agent_id = agent_id
        self.error_code = error_code
        super().__init__(message)


class AgentNotFoundError(AgentError):
    """Exception raised when agent is not found."""

    pass


class AgentNotActiveError(AgentError):
    """Exception raised when agent is not active."""

    pass


class AgentProcessingError(AgentError):
    """Exception raised during agent processing."""

    pass


class AgentTimeoutError(AgentError):
    """Exception raised when agent processing times out."""

    pass


class AgentHealthCheckError(AgentError):
    """Exception raised during agent health checks."""

    pass


async def agent_error_handler(request: Request, call_next: Any) -> JSONResponse:
    """Middleware to handle agent-specific errors and convert them to HTTP responses."""
    try:
        response = await call_next(request)
        return response

    except AgentNotFoundError as e:
        logger.error(f"Agent not found error: {e.message} (Agent: {e.agent_id})")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": "agent_not_found",
                "message": e.message,
                "agent_id": e.agent_id,
                "error_code": e.error_code or "AGENT_NOT_FOUND",
            },
        )

    except AgentNotActiveError as e:
        logger.error(f"Agent not active error: {e.message} (Agent: {e.agent_id})")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "agent_not_active",
                "message": e.message,
                "agent_id": e.agent_id,
                "error_code": e.error_code or "AGENT_NOT_ACTIVE",
            },
        )

    except AgentTimeoutError as e:
        logger.error(f"Agent timeout error: {e.message} (Agent: {e.agent_id})")
        return JSONResponse(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            content={
                "error": "agent_timeout",
                "message": e.message,
                "agent_id": e.agent_id,
                "error_code": e.error_code or "AGENT_TIMEOUT",
            },
        )

    except AgentProcessingError as e:
        logger.error(f"Agent processing error: {e.message} (Agent: {e.agent_id})")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "agent_processing_error",
                "message": e.message,
                "agent_id": e.agent_id,
                "error_code": e.error_code or "AGENT_PROCESSING_ERROR",
            },
        )

    except AgentHealthCheckError as e:
        logger.error(f"Agent health check error: {e.message} (Agent: {e.agent_id})")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": "agent_health_error",
                "message": e.message,
                "agent_id": e.agent_id,
                "error_code": e.error_code or "AGENT_HEALTH_ERROR",
            },
        )

    except AgentError as e:
        logger.error(f"Generic agent error: {e.message} (Agent: {e.agent_id})")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "agent_error",
                "message": e.message,
                "agent_id": e.agent_id,
                "error_code": e.error_code or "GENERIC_AGENT_ERROR",
            },
        )

    except Exception as e:
        logger.error(f"Unhandled error in agent middleware: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "internal_server_error",
                "message": "An unexpected error occurred",
                "error_code": "INTERNAL_SERVER_ERROR",
            },
        )


def map_agent_error_to_http(
    error: Exception, agent_id: str | None = None
) -> HTTPException:
    """Map agent errors to appropriate HTTP exceptions."""

    if isinstance(error, AgentNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent not found: {error.message}",
        )

    elif isinstance(error, AgentNotActiveError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Agent not active: {error.message}",
        )

    elif isinstance(error, AgentTimeoutError):
        return HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail=f"Agent timeout: {error.message}",
        )

    elif isinstance(error, AgentProcessingError):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent processing error: {error.message}",
        )

    elif isinstance(error, AgentHealthCheckError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Agent health check failed: {error.message}",
        )

    elif isinstance(error, AgentError):
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent error: {error.message}",
        )

    else:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(error)}",
        )
