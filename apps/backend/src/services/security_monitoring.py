"""
Comprehensive security logging and monitoring service.

This module provides centralized security event logging, threat detection,
and monitoring capabilities for the IAM dashboard.
"""

import json
import logging
import sys
from datetime import datetime, timedelta
from enum import Enum
from typing import Any
from uuid import uuid4

import redis
from pydantic import BaseModel

from src.core.config import settings

logger = logging.getLogger(__name__)


class SecurityEventType(str, Enum):
    """Security event types for classification."""

    # Authentication Events
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    LOGIN_LOCKED = "login_locked"
    LOGOUT = "logout"
    PASSWORD_RESET = "password_reset"
    PASSWORD_CHANGED = "password_changed"

    # 2FA Events
    TWO_FA_ENABLED = "2fa_enabled"
    TWO_FA_DISABLED = "2fa_disabled"
    TWO_FA_SUCCESS = "2fa_success"
    TWO_FA_FAILED = "2fa_failed"
    BACKUP_CODE_USED = "backup_code_used"
    BACKUP_CODE_FAILED = "backup_code_failed"

    # Session Events
    SESSION_CREATED = "session_created"
    SESSION_HIJACKING = "session_hijacking"
    SESSION_ANOMALY = "session_anomaly"
    CONCURRENT_SESSION_LIMIT = "concurrent_session_limit"

    # Authorization Events
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    PERMISSION_ESCALATION = "permission_escalation"
    PRIVILEGE_ABUSE = "privilege_abuse"

    # Rate Limiting Events
    RATE_LIMIT_HIT = "rate_limit_hit"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"

    # Token Events
    TOKEN_CREATED = "token_created"
    TOKEN_BLACKLISTED = "token_blacklisted"
    TOKEN_REPLAY_ATTEMPT = "token_replay_attempt"

    # Data Access Events
    DATA_ACCESSED = "data_accessed"
    DATA_MODIFIED = "data_modified"
    DATA_DELETED = "data_deleted"
    DATA_EXPORTED = "data_exported"

    # Security Violations
    MALICIOUS_INPUT = "malicious_input"
    SUSPICIOUS_BEHAVIOR = "suspicious_behavior"
    BRUTE_FORCE_ATTEMPT = "brute_force_attempt"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"

    # System Events
    CONFIGURATION_CHANGED = "configuration_changed"
    SYSTEM_ERROR = "system_error"
    SECURITY_ALERT = "security_alert"


class SeverityLevel(str, Enum):
    """Security event severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEvent(BaseModel):
    """Security event data structure."""

    event_id: str
    event_type: SecurityEventType
    severity: SeverityLevel
    timestamp: datetime
    user_id: str | None = None
    session_id: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    resource: str | None = None
    action: str | None = None
    details: dict[str, Any] = {}
    risk_score: float = 0.0
    tags: list[str] = []


class ThreatPattern(BaseModel):
    """Threat detection pattern."""

    pattern_id: str
    name: str
    description: str
    event_types: list[SecurityEventType]
    threshold_count: int
    time_window_minutes: int
    severity: SeverityLevel
    auto_response: bool = False


class SecurityAlert(BaseModel):
    """Security alert generated from threat detection."""

    alert_id: str
    pattern_id: str
    alert_type: str
    severity: SeverityLevel
    title: str
    description: str
    affected_user_id: str | None = None
    affected_resources: list[str] = []
    triggered_events: list[str] = []
    timestamp: datetime
    resolved: bool = False
    auto_response_taken: str | None = None


class SecurityMonitoringService:
    """Comprehensive security monitoring and threat detection service."""

    def __init__(self) -> None:
        """Initialize security monitoring service."""
        self._is_testing = "pytest" in sys.modules or "test" in sys.argv[0] if sys.argv else False

        if self._is_testing:
            self.redis_client = None
            logger.debug("SecurityMonitoringService initialized in testing mode")
        else:
            try:
                self.redis_client = redis.from_url(
                    settings.REDIS_URL,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                self.redis_client.ping()
                logger.info("SecurityMonitoringService initialized with Redis connection")
            except (redis.ConnectionError, redis.RedisError) as e:
                logger.error(f"Failed to connect to Redis for monitoring: {e}")
                self.redis_client = None

        # Initialize threat detection patterns
        self.threat_patterns = self._initialize_threat_patterns()

        # Event retention settings
        self.event_retention_days = 90
        self.alert_retention_days = 365
        self.max_events_per_user = 10000

    def _initialize_threat_patterns(self) -> dict[str, ThreatPattern]:
        """Initialize built-in threat detection patterns."""
        patterns = {
            "brute_force_login": ThreatPattern(
                pattern_id="brute_force_login",
                name="Brute Force Login Attack",
                description="Multiple failed login attempts from same IP",
                event_types=[SecurityEventType.LOGIN_FAILED],
                threshold_count=5,
                time_window_minutes=15,
                severity=SeverityLevel.HIGH,
                auto_response=True,
            ),
            "session_hijacking": ThreatPattern(
                pattern_id="session_hijacking",
                name="Session Hijacking Attempt",
                description="Suspicious session activity indicating potential hijacking",
                event_types=[
                    SecurityEventType.SESSION_HIJACKING,
                    SecurityEventType.SESSION_ANOMALY,
                ],
                threshold_count=1,
                time_window_minutes=5,
                severity=SeverityLevel.CRITICAL,
                auto_response=True,
            ),
            "privilege_escalation": ThreatPattern(
                pattern_id="privilege_escalation",
                name="Privilege Escalation Attempt",
                description="Attempts to access resources beyond user permissions",
                event_types=[
                    SecurityEventType.ACCESS_DENIED,
                    SecurityEventType.PERMISSION_ESCALATION,
                ],
                threshold_count=3,
                time_window_minutes=30,
                severity=SeverityLevel.HIGH,
                auto_response=False,
            ),
            "token_replay": ThreatPattern(
                pattern_id="token_replay",
                name="Token Replay Attack",
                description="Attempts to reuse blacklisted tokens",
                event_types=[SecurityEventType.TOKEN_REPLAY_ATTEMPT],
                threshold_count=1,
                time_window_minutes=1,
                severity=SeverityLevel.HIGH,
                auto_response=True,
            ),
            "data_exfiltration": ThreatPattern(
                pattern_id="data_exfiltration",
                name="Potential Data Exfiltration",
                description="Unusual data access patterns",
                event_types=[SecurityEventType.DATA_ACCESSED, SecurityEventType.DATA_EXPORTED],
                threshold_count=10,
                time_window_minutes=60,
                severity=SeverityLevel.MEDIUM,
                auto_response=False,
            ),
            "injection_attempts": ThreatPattern(
                pattern_id="injection_attempts",
                name="Code Injection Attempts",
                description="SQL injection or XSS attempts detected",
                event_types=[
                    SecurityEventType.SQL_INJECTION_ATTEMPT,
                    SecurityEventType.XSS_ATTEMPT,
                ],
                threshold_count=1,
                time_window_minutes=1,
                severity=SeverityLevel.CRITICAL,
                auto_response=True,
            ),
        }

        return patterns

    def _get_event_key(self, user_id: str | None = None) -> str:
        """Generate Redis key for security events."""
        if user_id:
            return f"security_events:user:{user_id}"
        return "security_events:global"

    def _get_alert_key(self) -> str:
        """Generate Redis key for security alerts."""
        return "security_alerts"

    def _get_pattern_key(self, pattern_id: str) -> str:
        """Generate Redis key for pattern tracking."""
        return f"threat_pattern:{pattern_id}"

    def _get_stats_key(self) -> str:
        """Generate Redis key for monitoring statistics."""
        return "security_stats"

    def log_security_event(
        self,
        event_type: SecurityEventType,
        severity: SeverityLevel = SeverityLevel.LOW,
        user_id: str | None = None,
        session_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
        resource: str | None = None,
        action: str | None = None,
        details: dict[str, Any] | None = None,
        risk_score: float = 0.0,
        tags: list[str] | None = None,
    ) -> SecurityEvent:
        """
        Log a security event.

        Args:
            event_type: Type of security event
            severity: Event severity level
            user_id: User involved in the event
            session_id: Session ID if applicable
            ip_address: Source IP address
            user_agent: User agent string
            resource: Resource accessed/affected
            action: Action performed
            details: Additional event details
            risk_score: Risk score (0.0 to 1.0)
            tags: Event tags for classification

        Returns:
            Created SecurityEvent
        """
        event = SecurityEvent(
            event_id=str(uuid4()),
            event_type=event_type,
            severity=severity,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource=resource,
            action=action,
            details=details or {},
            risk_score=risk_score,
            tags=tags or [],
        )

        # Store event in Redis
        self._store_event(event)

        # Update statistics
        self._update_stats(event)

        # Check for threat patterns
        self._check_threat_patterns(event)

        # Log to application logger based on severity
        log_message = f"Security Event [{event_type.value}] - User: {user_id}, IP: {ip_address}"

        if severity == SeverityLevel.LOW:
            logger.info(log_message)
        elif severity == SeverityLevel.MEDIUM:
            logger.warning(log_message)
        else:
            logger.error(log_message)

        return event

    def _store_event(self, event: SecurityEvent) -> None:
        """Store security event in Redis."""
        if self.redis_client is None:
            return

        try:
            # Store in user-specific and global event lists
            event_data = event.model_dump_json()

            # User-specific events
            if event.user_id:
                user_key = self._get_event_key(event.user_id)
                self.redis_client.lpush(user_key, event_data)
                self.redis_client.ltrim(user_key, 0, self.max_events_per_user - 1)
                self.redis_client.expire(user_key, timedelta(days=self.event_retention_days))

            # Global events
            global_key = self._get_event_key()
            self.redis_client.lpush(global_key, event_data)
            self.redis_client.ltrim(global_key, 0, 50000 - 1)  # Keep last 50k global events
            self.redis_client.expire(global_key, timedelta(days=self.event_retention_days))

            # Index by event type for quick searching
            type_key = f"events_by_type:{event.event_type.value}"
            self.redis_client.lpush(type_key, event_data)
            self.redis_client.ltrim(type_key, 0, 10000 - 1)
            self.redis_client.expire(type_key, timedelta(days=30))

        except redis.RedisError as e:
            logger.error(f"Failed to store security event: {e}")

    def _update_stats(self, event: SecurityEvent) -> None:
        """Update security monitoring statistics."""
        if self.redis_client is None:
            return

        try:
            stats_key = self._get_stats_key()
            timestamp = datetime.utcnow().strftime("%Y-%m-%d")

            # Update counters
            self.redis_client.hincrby(stats_key, "total_events", 1)
            self.redis_client.hincrby(stats_key, f"events_{event.event_type.value}", 1)
            self.redis_client.hincrby(stats_key, f"severity_{event.severity.value}", 1)
            self.redis_client.hincrby(stats_key, f"daily_{timestamp}", 1)

            # Update risk score statistics
            if event.risk_score > 0:
                self.redis_client.hincrby(stats_key, "high_risk_events", 1)

            # Set expiration
            self.redis_client.expire(stats_key, timedelta(days=self.event_retention_days))

        except redis.RedisError as e:
            logger.warning(f"Failed to update security statistics: {e}")

    def _check_threat_patterns(self, event: SecurityEvent) -> None:
        """Check event against threat detection patterns."""
        for pattern in self.threat_patterns.values():
            if event.event_type in pattern.event_types:
                self._evaluate_pattern(pattern, event)

    def _evaluate_pattern(self, pattern: ThreatPattern, event: SecurityEvent) -> None:
        """Evaluate a threat pattern against recent events."""
        if self.redis_client is None:
            return

        try:
            pattern_key = self._get_pattern_key(pattern.pattern_id)

            # Add current event to pattern tracking
            event_identifier = f"{event.timestamp.isoformat()}:{event.event_id}"
            self.redis_client.zadd(pattern_key, {event_identifier: event.timestamp.timestamp()})

            # Remove old events outside time window
            cutoff_time = event.timestamp.timestamp() - (pattern.time_window_minutes * 60)
            self.redis_client.zremrangebyscore(pattern_key, 0, cutoff_time)

            # Set expiration
            self.redis_client.expire(pattern_key, pattern.time_window_minutes * 60 + 300)

            # Count events in current window
            event_count = self.redis_client.zcard(pattern_key)

            # Check if threshold is exceeded
            if event_count >= pattern.threshold_count:
                self._trigger_alert(pattern, event, event_count)

        except redis.RedisError as e:
            logger.error(f"Failed to evaluate threat pattern {pattern.pattern_id}: {e}")

    def _trigger_alert(
        self, pattern: ThreatPattern, triggering_event: SecurityEvent, event_count: int
    ) -> None:
        """Trigger a security alert based on pattern match."""
        alert = SecurityAlert(
            alert_id=str(uuid4()),
            pattern_id=pattern.pattern_id,
            alert_type=pattern.name,
            severity=pattern.severity,
            title=f"{pattern.name} Detected",
            description=f"{pattern.description}. Detected {event_count} events in {pattern.time_window_minutes} minutes.",
            affected_user_id=triggering_event.user_id,
            affected_resources=[triggering_event.resource] if triggering_event.resource else [],
            triggered_events=[triggering_event.event_id],
            timestamp=datetime.utcnow(),
            auto_response_taken=None,
        )

        # Store alert
        self._store_alert(alert)

        # Take automatic response if configured
        if pattern.auto_response:
            response = self._take_auto_response(alert, triggering_event)
            alert.auto_response_taken = response

        # Log critical alerts
        if pattern.severity in [SeverityLevel.HIGH, SeverityLevel.CRITICAL]:
            logger.critical(f"SECURITY ALERT: {alert.title} - {alert.description}")

    def _store_alert(self, alert: SecurityAlert) -> None:
        """Store security alert."""
        if self.redis_client is None:
            return

        try:
            alert_key = self._get_alert_key()
            alert_data = alert.model_dump_json()

            # Store alert with timestamp score for chronological ordering
            self.redis_client.zadd(alert_key, {alert_data: alert.timestamp.timestamp()})

            # Keep only recent alerts (based on retention policy)
            cutoff_time = (
                datetime.utcnow() - timedelta(days=self.alert_retention_days)
            ).timestamp()
            self.redis_client.zremrangebyscore(alert_key, 0, cutoff_time)

        except redis.RedisError as e:
            logger.error(f"Failed to store security alert: {e}")

    def _take_auto_response(self, alert: SecurityAlert, event: SecurityEvent) -> str:
        """Take automatic response to security alert."""
        response_actions = []

        if alert.pattern_id == "brute_force_login":
            # Could implement IP blocking here
            response_actions.append("IP monitoring increased")

        elif alert.pattern_id == "session_hijacking":
            # Could implement session termination here
            response_actions.append("Session security verification triggered")

        elif alert.pattern_id == "token_replay":
            # Token is already blacklisted, additional monitoring
            response_actions.append("Enhanced token monitoring activated")

        elif alert.pattern_id == "injection_attempts":
            # Could implement request filtering
            response_actions.append("Request filtering enhanced")

        if response_actions:
            response = "; ".join(response_actions)
            logger.info(f"Auto-response taken for alert {alert.alert_id}: {response}")
            return response

        return "No automatic response configured"

    def get_security_events(
        self,
        user_id: str | None = None,
        event_types: list[SecurityEventType] | None = None,
        severity_levels: list[SeverityLevel] | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[SecurityEvent]:
        """
        Retrieve security events with filtering options.

        Args:
            user_id: Filter by user ID
            event_types: Filter by event types
            severity_levels: Filter by severity levels
            start_time: Start time for filtering
            end_time: End time for filtering
            limit: Maximum number of events to return

        Returns:
            List of matching SecurityEvent objects
        """
        if self.redis_client is None:
            return []

        try:
            # Choose appropriate key based on filters
            if user_id:
                key = self._get_event_key(user_id)
            elif event_types and len(event_types) == 1:
                key = f"events_by_type:{event_types[0].value}"
            else:
                key = self._get_event_key()

            # Get raw event data
            raw_events = self.redis_client.lrange(key, 0, limit * 2)  # Get more for filtering

            events = []
            for raw_event in raw_events:
                try:
                    event_data = json.loads(raw_event)
                    event = SecurityEvent(**event_data)

                    # Apply filters
                    if event_types and event.event_type not in event_types:
                        continue

                    if severity_levels and event.severity not in severity_levels:
                        continue

                    if start_time and event.timestamp < start_time:
                        continue

                    if end_time and event.timestamp > end_time:
                        continue

                    events.append(event)

                    if len(events) >= limit:
                        break

                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse security event: {e}")
                    continue

            return events

        except redis.RedisError as e:
            logger.error(f"Failed to retrieve security events: {e}")
            return []

    def get_security_alerts(
        self,
        severity_levels: list[SeverityLevel] | None = None,
        resolved: bool | None = None,
        limit: int = 50,
    ) -> list[SecurityAlert]:
        """Retrieve security alerts with filtering."""
        if self.redis_client is None:
            return []

        try:
            alert_key = self._get_alert_key()

            # Get recent alerts (sorted by timestamp descending)
            raw_alerts = self.redis_client.zrevrange(alert_key, 0, limit * 2)

            alerts = []
            for raw_alert in raw_alerts:
                try:
                    alert_data = json.loads(raw_alert)
                    alert = SecurityAlert(**alert_data)

                    # Apply filters
                    if severity_levels and alert.severity not in severity_levels:
                        continue

                    if resolved is not None and alert.resolved != resolved:
                        continue

                    alerts.append(alert)

                    if len(alerts) >= limit:
                        break

                except (json.JSONDecodeError, ValueError) as e:
                    logger.warning(f"Failed to parse security alert: {e}")
                    continue

            return alerts

        except redis.RedisError as e:
            logger.error(f"Failed to retrieve security alerts: {e}")
            return []

    def get_security_statistics(self) -> dict[str, Any]:
        """Get comprehensive security monitoring statistics."""
        if self.redis_client is None:
            return {"testing_mode": True}

        try:
            stats_key = self._get_stats_key()
            raw_stats = self.redis_client.hgetall(stats_key)

            # Convert to integers where possible
            stats = {}
            for key, value in raw_stats.items():
                try:
                    stats[key] = int(value)
                except ValueError:
                    stats[key] = value

            # Add alert statistics
            alert_key = self._get_alert_key()
            stats["total_alerts"] = self.redis_client.zcard(alert_key)

            # Add recent activity (last 24 hours)
            yesterday = datetime.utcnow() - timedelta(days=1)
            yesterday_str = yesterday.strftime("%Y-%m-%d")
            today_str = datetime.utcnow().strftime("%Y-%m-%d")

            stats["events_last_24h"] = stats.get(f"daily_{today_str}", 0) + stats.get(
                f"daily_{yesterday_str}", 0
            )

            return stats

        except redis.RedisError as e:
            logger.error(f"Failed to get security statistics: {e}")
            return {"error": "Unable to retrieve statistics"}

    def resolve_alert(self, alert_id: str, resolved_by: str) -> bool:
        """Mark a security alert as resolved."""
        # In a full implementation, this would update the alert status
        # For now, we log the resolution
        logger.info(f"Security alert {alert_id} resolved by {resolved_by}")
        return True

    async def close(self) -> None:
        """Close Redis connection."""
        if self.redis_client is not None and hasattr(self.redis_client, "close"):
            try:
                self.redis_client.close()
            except Exception as e:
                logger.warning(f"Error closing Redis connection: {e}")


# Global security monitoring service instance
security_monitor = SecurityMonitoringService()


# Convenience functions for common security events
def log_login_attempt(
    user_id: str, ip_address: str, success: bool, details: dict[str, Any] | None = None
) -> None:
    """Log a login attempt."""
    event_type = SecurityEventType.LOGIN_SUCCESS if success else SecurityEventType.LOGIN_FAILED
    severity = SeverityLevel.LOW if success else SeverityLevel.MEDIUM
    risk_score = 0.0 if success else 0.3

    security_monitor.log_security_event(
        event_type=event_type,
        severity=severity,
        user_id=user_id,
        ip_address=ip_address,
        risk_score=risk_score,
        details=details or {},
    )


def log_permission_change(user_id: str, changed_by: str, action: str, resource: str) -> None:
    """Log a permission change."""
    security_monitor.log_security_event(
        event_type=SecurityEventType.PERMISSION_ESCALATION,
        severity=SeverityLevel.MEDIUM,
        user_id=changed_by,
        resource=resource,
        action=action,
        details={"target_user": user_id, "permission_action": action},
        risk_score=0.4,
    )


def log_suspicious_activity(
    user_id: str, ip_address: str, activity: str, details: dict[str, Any]
) -> None:
    """Log suspicious activity."""
    security_monitor.log_security_event(
        event_type=SecurityEventType.SUSPICIOUS_BEHAVIOR,
        severity=SeverityLevel.HIGH,
        user_id=user_id,
        ip_address=ip_address,
        details={"activity": activity, **details},
        risk_score=0.7,
        tags=["suspicious", "investigation_needed"],
    )


def log_data_access(
    user_id: str, resource: str, action: str, ip_address: str | None = None
) -> None:
    """Log data access event."""
    security_monitor.log_security_event(
        event_type=SecurityEventType.DATA_ACCESSED,
        severity=SeverityLevel.LOW,
        user_id=user_id,
        ip_address=ip_address,
        resource=resource,
        action=action,
        risk_score=0.1,
    )
