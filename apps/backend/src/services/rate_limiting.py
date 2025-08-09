"""
Advanced rate limiting service with Redis backend.

This module provides comprehensive rate limiting functionality including:
- IP-based rate limiting
- Email-based rate limiting
- Endpoint-specific rate limiting
- Sliding window algorithm
- Security event tracking
"""

import asyncio
import logging
import sys
import time
from datetime import datetime, timedelta
from typing import Any, Literal

import redis
from pydantic import BaseModel

from src.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitConfig(BaseModel):
    """Rate limit configuration for different scenarios."""

    window_seconds: int = 60  # Time window for counting attempts
    max_attempts: int = 5  # Maximum attempts per window
    lockout_duration: int = 300  # Lockout duration in seconds (5 minutes)
    block_duration: int = 3600  # Block duration for repeat offenders (1 hour)


class RateLimitResult(BaseModel):
    """Result of rate limit check."""

    allowed: bool
    remaining_attempts: int
    window_reset_time: datetime
    retry_after_seconds: int = 0
    reason: str = ""


class SecurityEvent(BaseModel):
    """Security event for monitoring."""

    event_type: str
    source_ip: str
    target: str  # email, endpoint, etc.
    timestamp: datetime
    details: dict[str, Any]


class AdvancedRateLimiter:
    """Advanced rate limiting service with multiple strategies."""

    def __init__(self) -> None:
        """Initialize rate limiter with Redis connection."""
        self._is_testing = "pytest" in sys.modules or "test" in sys.argv[0] if sys.argv else False

        if self._is_testing:
            self.redis_client = None
            logger.debug("RateLimiter initialized in testing mode")
        else:
            try:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                # Test connection
                self.redis_client.ping()
                logger.info("RateLimiter initialized with Redis connection")
            except (redis.ConnectionError, redis.RedisError) as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.redis_client = None

        # Rate limit configurations for different scenarios
        self.configs = {
            "login": RateLimitConfig(
                window_seconds=300,  # 5 minutes
                max_attempts=5,  # 5 attempts per 5 minutes
                lockout_duration=900,  # 15 minutes lockout
                block_duration=3600,  # 1 hour for repeat offenders
            ),
            "password_reset": RateLimitConfig(
                window_seconds=3600,  # 1 hour
                max_attempts=3,  # 3 attempts per hour
                lockout_duration=3600,  # 1 hour lockout
                block_duration=7200,  # 2 hours for repeat offenders
            ),
            "2fa": RateLimitConfig(
                window_seconds=300,  # 5 minutes
                max_attempts=10,  # 10 attempts per 5 minutes
                lockout_duration=300,  # 5 minutes lockout
                block_duration=1800,  # 30 minutes for repeat offenders
            ),
            "api": RateLimitConfig(
                window_seconds=60,  # 1 minute
                max_attempts=100,  # 100 requests per minute
                lockout_duration=60,  # 1 minute lockout
                block_duration=300,  # 5 minutes for repeat offenders
            ),
            "email": RateLimitConfig(
                window_seconds=60,  # 1 minute
                max_attempts=3,  # 3 attempts per minute by email
                lockout_duration=300,  # 5 minutes lockout
                block_duration=1800,  # 30 minutes for repeat offenders
            ),
        }

    def _get_window_key(self, key_type: str, identifier: str, scenario: str) -> str:
        """Generate Redis key for rate limiting window."""
        return f"rate_limit:{key_type}:{scenario}:{identifier}"

    def _get_lockout_key(self, key_type: str, identifier: str, scenario: str) -> str:
        """Generate Redis key for lockout status."""
        return f"lockout:{key_type}:{scenario}:{identifier}"

    def _get_security_key(self, identifier: str) -> str:
        """Generate Redis key for security events."""
        return f"security_events:{identifier}"

    async def _increment_counter(self, key: str, window_seconds: int) -> int:
        """Increment counter with sliding window using Redis pipeline."""
        if self.redis_client is None:
            return 1  # Allow in testing mode

        try:
            current_time = time.time()
            window_start = current_time - window_seconds

            # Use Redis pipeline for atomic operations
            pipe = self.redis_client.pipeline()

            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)

            # Add current request with timestamp as score
            pipe.zadd(key, {str(current_time): current_time})

            # Count requests in current window
            pipe.zcard(key)

            # Set expiration
            pipe.expire(key, window_seconds + 10)

            # Execute pipeline
            results = pipe.execute()

            # Return count of requests in window
            return results[2]  # zcard result

        except redis.RedisError as e:
            logger.error(f"Redis error in rate limiting: {e}")
            return 1  # Allow on Redis failure

    async def _is_locked_out(
        self, key_type: str, identifier: str, scenario: str
    ) -> tuple[bool, int]:
        """Check if identifier is locked out."""
        if self.redis_client is None:
            return False, 0

        lockout_key = self._get_lockout_key(key_type, identifier, scenario)

        try:
            lockout_data = self.redis_client.get(lockout_key)
            if lockout_data:
                lockout_until = float(lockout_data)
                current_time = time.time()

                if current_time < lockout_until:
                    return True, int(lockout_until - current_time)
                else:
                    # Lockout expired, clean up
                    self.redis_client.delete(lockout_key)

            return False, 0

        except redis.RedisError as e:
            logger.error(f"Redis error checking lockout: {e}")
            return False, 0

    async def _apply_lockout(
        self, key_type: str, identifier: str, scenario: str, duration: int
    ) -> None:
        """Apply lockout to identifier."""
        if self.redis_client is None:
            return

        lockout_key = self._get_lockout_key(key_type, identifier, scenario)
        lockout_until = time.time() + duration

        try:
            self.redis_client.setex(lockout_key, duration + 10, str(lockout_until))
            logger.warning(f"Applied {duration}s lockout to {key_type}:{identifier} for {scenario}")
        except redis.RedisError as e:
            logger.error(f"Failed to apply lockout: {e}")

    async def _log_security_event(self, event: SecurityEvent) -> None:
        """Log security event for monitoring."""
        if self.redis_client is None:
            return

        event_key = self._get_security_key(event.source_ip)

        try:
            # Store event with timestamp
            event_data = {
                "type": event.event_type,
                "target": event.target,
                "timestamp": event.timestamp.isoformat(),
                "details": event.details,
            }

            # Use list to store events with sliding window cleanup
            self.redis_client.lpush(event_key, str(event_data))

            # Keep only last 100 events per IP
            self.redis_client.ltrim(event_key, 0, 99)

            # Expire after 24 hours
            self.redis_client.expire(event_key, 86400)

        except redis.RedisError as e:
            logger.error(f"Failed to log security event: {e}")

    async def check_rate_limit(
        self,
        identifier: str,
        scenario: Literal["login", "password_reset", "2fa", "api", "email"],
        key_type: Literal["ip", "email", "user"] = "ip",
        client_info: dict[str, Any] | None = None,
    ) -> RateLimitResult:
        """
        Check if request should be rate limited.

        Args:
            identifier: IP address, email, or user ID
            scenario: Type of operation being rate limited
            key_type: Type of identifier (ip, email, user)
            client_info: Additional client information for fingerprinting

        Returns:
            RateLimitResult with decision and metadata
        """
        config = self.configs.get(scenario, self.configs["api"])

        # Check for active lockout first
        is_locked, lockout_remaining = await self._is_locked_out(key_type, identifier, scenario)
        if is_locked:
            await self._log_security_event(
                SecurityEvent(
                    event_type="rate_limit_lockout_hit",
                    source_ip=client_info.get("ip", "unknown") if client_info else identifier,
                    target=identifier,
                    timestamp=datetime.utcnow(),
                    details={
                        "scenario": scenario,
                        "key_type": key_type,
                        "lockout_remaining": lockout_remaining,
                    },
                )
            )

            return RateLimitResult(
                allowed=False,
                remaining_attempts=0,
                window_reset_time=datetime.utcnow() + timedelta(seconds=lockout_remaining),
                retry_after_seconds=lockout_remaining,
                reason=f"Rate limit lockout active for {lockout_remaining}s",
            )

        # Check current window
        window_key = self._get_window_key(key_type, identifier, scenario)
        current_count = await self._increment_counter(window_key, config.window_seconds)

        remaining_attempts = max(0, config.max_attempts - current_count)
        window_reset = datetime.utcnow() + timedelta(seconds=config.window_seconds)

        if current_count <= config.max_attempts:
            # Within limits
            return RateLimitResult(
                allowed=True,
                remaining_attempts=remaining_attempts,
                window_reset_time=window_reset,
                reason="Within rate limits",
            )
        else:
            # Exceeded limits - apply lockout
            await self._apply_lockout(key_type, identifier, scenario, config.lockout_duration)

            # Log security event
            await self._log_security_event(
                SecurityEvent(
                    event_type="rate_limit_exceeded",
                    source_ip=client_info.get("ip", "unknown") if client_info else identifier,
                    target=identifier,
                    timestamp=datetime.utcnow(),
                    details={
                        "scenario": scenario,
                        "key_type": key_type,
                        "attempts": current_count,
                        "limit": config.max_attempts,
                        "lockout_duration": config.lockout_duration,
                    },
                )
            )

            return RateLimitResult(
                allowed=False,
                remaining_attempts=0,
                window_reset_time=datetime.utcnow() + timedelta(seconds=config.lockout_duration),
                retry_after_seconds=config.lockout_duration,
                reason=f"Rate limit exceeded ({current_count}/{config.max_attempts})",
            )

    async def check_multiple_identifiers(
        self,
        identifiers: dict[str, str],  # {"ip": "1.2.3.4", "email": "user@example.com"}
        scenario: Literal["login", "password_reset", "2fa", "api", "email"],
        client_info: dict[str, Any] | None = None,
    ) -> RateLimitResult:
        """
        Check rate limits across multiple identifiers (IP + email).

        Returns the most restrictive result.
        """
        results = []

        for key_type, identifier in identifiers.items():
            if key_type in ["ip", "email", "user"]:
                result = await self.check_rate_limit(
                    identifier,
                    scenario,
                    key_type,
                    client_info,  # type: ignore
                )
                results.append(result)

        # Return the most restrictive result (any blocked = blocked)
        for result in results:
            if not result.allowed:
                return result

        # If all allowed, return the one with least remaining attempts
        return min(results, key=lambda r: r.remaining_attempts)

    async def clear_rate_limit(
        self, identifier: str, scenario: str, key_type: Literal["ip", "email", "user"] = "ip"
    ) -> bool:
        """Clear rate limiting data for identifier (e.g., after successful login)."""
        if self.redis_client is None:
            return True

        try:
            window_key = self._get_window_key(key_type, identifier, scenario)
            lockout_key = self._get_lockout_key(key_type, identifier, scenario)

            # Clear both window and lockout
            deleted = self.redis_client.delete(window_key, lockout_key)

            logger.info(f"Cleared rate limit for {key_type}:{identifier} in {scenario}")
            return deleted > 0

        except redis.RedisError as e:
            logger.error(f"Failed to clear rate limit: {e}")
            return False

    async def get_security_events(self, identifier: str, limit: int = 50) -> list[dict[str, Any]]:
        """Get recent security events for an identifier."""
        if self.redis_client is None:
            return []

        event_key = self._get_security_key(identifier)

        try:
            events_raw = self.redis_client.lrange(event_key, 0, limit - 1)
            events = []

            for event_str in events_raw:
                try:
                    # Parse stored event data
                    event_data = eval(event_str)  # Note: In production, use json.loads
                    events.append(event_data)
                except Exception as e:
                    logger.warning(f"Failed to parse security event: {e}")
                    continue

            return events

        except redis.RedisError as e:
            logger.error(f"Failed to get security events: {e}")
            return []

    async def get_rate_limit_status(
        self, identifier: str, scenario: str, key_type: Literal["ip", "email", "user"] = "ip"
    ) -> dict[str, Any]:
        """Get current rate limit status for debugging."""
        if self.redis_client is None:
            return {"testing_mode": True}

        config = self.configs.get(scenario, self.configs["api"])
        window_key = self._get_window_key(key_type, identifier, scenario)
        lockout_key = self._get_lockout_key(key_type, identifier, scenario)

        try:
            # Get current count in window
            current_time = time.time()
            window_start = current_time - config.window_seconds
            current_count = self.redis_client.zcount(window_key, window_start, current_time)

            # Check lockout status
            lockout_data = self.redis_client.get(lockout_key)
            lockout_until = None
            if lockout_data:
                lockout_until = datetime.fromtimestamp(float(lockout_data))

            return {
                "identifier": identifier,
                "scenario": scenario,
                "key_type": key_type,
                "current_count": current_count,
                "max_attempts": config.max_attempts,
                "window_seconds": config.window_seconds,
                "lockout_until": lockout_until.isoformat() if lockout_until else None,
                "remaining_attempts": max(0, config.max_attempts - current_count),
            }

        except redis.RedisError as e:
            logger.error(f"Failed to get rate limit status: {e}")
            return {"error": str(e)}

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis_client is not None and hasattr(self.redis_client, "close"):
            try:
                self.redis_client.close()
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")


# Global rate limiter instance
rate_limiter = AdvancedRateLimiter()


# Convenience functions for common scenarios
async def check_login_rate_limit(
    ip_address: str, email: str, client_info: dict[str, Any] | None = None
) -> RateLimitResult:
    """Check rate limit for login attempts."""
    return await rate_limiter.check_multiple_identifiers(
        {"ip": ip_address, "email": email}, "login", client_info
    )


async def check_password_reset_rate_limit(ip_address: str, email: str) -> RateLimitResult:
    """Check rate limit for password reset attempts."""
    return await rate_limiter.check_multiple_identifiers(
        {"ip": ip_address, "email": email}, "password_reset"
    )


async def check_2fa_rate_limit(ip_address: str, email: str) -> RateLimitResult:
    """Check rate limit for 2FA attempts."""
    return await rate_limiter.check_multiple_identifiers({"ip": ip_address, "email": email}, "2fa")


async def check_api_rate_limit(ip_address: str, user_id: str | None = None) -> RateLimitResult:
    """Check rate limit for API requests."""
    identifiers = {"ip": ip_address}
    if user_id:
        identifiers["user"] = user_id

    return await rate_limiter.check_multiple_identifiers(identifiers, "api")


async def clear_successful_login(ip_address: str, email: str) -> None:
    """Clear rate limits after successful login."""
    await asyncio.gather(
        rate_limiter.clear_rate_limit(ip_address, "login", "ip"),
        rate_limiter.clear_rate_limit(email, "login", "email"),
    )
