"""
Audit logging for AURORA-DEV enterprise features.

Provides comprehensive audit trails for compliance and security.
"""
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from aurora_dev.core.logging import get_logger


class AuditLevel(Enum):
    """Audit event severity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditEvent:
    """Represents a single audit event."""

    def __init__(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        level: AuditLevel = AuditLevel.INFO,
    ) -> None:
        """Initialize audit event.

        Args:
            event_type: Type of event (e.g., "user_login", "code_change")
            user_id: User who performed the action
            project_id: Project affected
            resource_id: Resource affected
            action: Specific action performed
            details: Additional event details
            level: Severity level
        """
        self.event_id = str(uuid4())
        self.timestamp = datetime.now(timezone.utc)
        self.event_type = event_type
        self.user_id = user_id
        self.project_id = project_id
        self.resource_id = resource_id
        self.action = action
        self.details = details or {}
        self.level = level

    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "event_type": self.event_type,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "resource_id": self.resource_id,
            "action": self.action,
            "details": self.details,
            "level": self.level.value,
        }

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict(), default=str)


class AuditLogger:
    """Logs audit events for compliance and security."""

    def __init__(
        self,
        project_id: Optional[str] = None,
        log_file: Optional[str] = "audit.log",
    ) -> None:
        """Initialize audit logger.

        Args:
            project_id: Project identifier for namespacing
            log_file: File to write audit logs to
        """
        self.project_id = project_id
        self.log_file = log_file
        self._logger = get_logger("audit")

        # In-memory storage for recent events
        self._events: list[AuditEvent] = []
        self._max_events = 1000

    def log(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        level: AuditLevel = AuditLevel.INFO,
    ) -> AuditEvent:
        """Log an audit event.

        Args:
            event_type: Type of event
            user_id: User who performed the action
            resource_id: Resource affected
            action: Specific action performed
            details: Additional event details
            level: Severity level

        Returns:
            The logged audit event
        """
        event = AuditEvent(
            event_type=event_type,
            user_id=user_id,
            project_id=self.project_id,
            resource_id=resource_id,
            action=action,
            details=details,
            level=level,
        )

        # Add to in-memory storage
        self._events.append(event)
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events :]

        # Log to file if configured
        if self.log_file:
            try:
                with open(self.log_file, "a") as f:
                    f.write(event.to_json() + "\n")
            except Exception as e:
                self._logger.warning(f"Failed to write audit log: {e}")

        # Log to structured logger
        self._logger.info(
            f"Audit event: {event_type}",
            extra={
                "event_id": event.event_id,
                "user_id": user_id,
                "project_id": self.project_id,
                "resource_id": resource_id,
                "action": action,
                "details": details,
                "level": level.value,
            },
        )

        return event

    def get_events(
        self,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[AuditEvent]:
        """Get filtered audit events.

        Args:
            event_type: Filter by event type
            user_id: Filter by user
            start_time: Filter by start time
            end_time: Filter by end time

        Returns:
            List of matching audit events
        """
        events = self._events

        if event_type:
            events = [e for e in events if e.event_type == event_type]

        if user_id:
            events = [e for e in events if e.user_id == user_id]

        if start_time:
            events = [e for e in events if e.timestamp >= start_time]

        if end_time:
            events = [e for e in events if e.timestamp <= end_time]

        return events

    def get_audit_trail(
        self,
        resource_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[AuditEvent]:
        """Get complete audit trail for a resource.

        Args:
            resource_id: Resource identifier
            start_time: Start time for trail
            end_time: End time for trail

        Returns:
            Complete audit trail for the resource
        """
        return self.get_events(
            resource_id=resource_id,
            start_time=start_time,
            end_time=end_time,
        )
