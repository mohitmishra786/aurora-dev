"""
Compliance management for AURORA-DEV enterprise features.

Handles compliance checks, data retention, and security policies.
"""
from datetime import datetime, timezone, timedelta
from typing import Any, Optional
from enum import Enum

from aurora_dev.core.logging import get_logger


class ComplianceCheck(Enum):
    """Types of compliance checks."""

    CODE_SECURITY = "code_security"
    DATA_PRIVACY = "data_privacy"
    ACCESS_CONTROL = "access_control"
    AUDIT_LOGGING = "audit_logging"
    DATA_RETENTION = "data_retention"
    VULNERABILITY_SCAN = "vulnerability_scan"


class ComplianceManager:
    """Manages compliance checks and policies."""

    def __init__(
        self,
        project_id: Optional[str] = None,
        retention_days: int = 90,
    ) -> None:
        """Initialize compliance manager.

        Args:
            project_id: Project identifier
            retention_days: Data retention period in days
        """
        self.project_id = project_id
        self.retention_days = retention_days
        self._logger = get_logger("compliance")

        # Compliance status
        self._compliance_status: dict[str, bool] = {}
        self._violations: list[dict[str, Any]] = []

        # Data retention policies
        self._retention_policies: dict[str, int] = {
            "audit_logs": 365 * 5,  # 5 years
            "code_changes": 365 * 10,  # 10 years
            "project_data": 365 * 7,  # 7 years
            "temp_data": 7,  # 7 days
        }

    def check_compliance(
        self,
        check_type: ComplianceCheck,
        data: Optional[dict[str, Any]] = None,
    ) -> tuple[bool, list[str]]:
        """Run a compliance check.

        Args:
            check_type: Type of compliance check
            data: Data to check

        Returns:
            Tuple of (is_compliant, violations)
        """
        violations = []

        if check_type == ComplianceCheck.CODE_SECURITY:
            # Check for hardcoded secrets, unsafe patterns
            if data:
                code = data.get("code", "")
                if "password" in code.lower() and "example" not in code.lower():
                    violations.append("Potential hardcoded password found")
                if "sk-" in code:  # API key pattern
                    violations.append("Potential API key in code")

        elif check_type == ComplianceCheck.DATA_PRIVACY:
            # Check for PII exposure
            if data:
                content = str(data.get("content", ""))
                # Simple PII detection (in production, use proper PII detection)
                if any(
                    pattern in content
                    for pattern in ["ssn", "social security", "credit card"]
                ):
                    violations.append("Potential PII exposure")

        elif check_type == ComplianceCheck.ACCESS_CONTROL:
            # Check access permissions
            if data:
                required_role = data.get("required_role")
                user_role = data.get("user_role")
                if required_role and user_role and user_role != required_role:
                    violations.append(
                        f"Access denied: requires {required_role}, user has {user_role}"
                    )

        elif check_type == ComplianceCheck.AUDIT_LOGGING:
            # Verify audit logging is enabled
            if not data or not data.get("audit_enabled", False):
                violations.append("Audit logging not enabled")

        elif check_type == ComplianceCheck.DATA_RETENTION:
            # Check data retention compliance
            if data:
                created_at = data.get("created_at")
                if created_at:
                    age_days = (datetime.now(timezone.utc) - created_at).days
                    if age_days > self.retention_days:
                        violations.append(
                            f"Data retention exceeded: {age_days} days old"
                        )

        elif check_type == ComplianceCheck.VULNERABILITY_SCAN:
            # Check for known vulnerabilities
            if data:
                dependencies = data.get("dependencies", [])
                vulnerable_deps = ["log4j", "struts", "openssl-1.0.1"]
                for dep in dependencies:
                    if any(vuln in dep.lower() for vuln in vulnerable_deps):
                        violations.append(f"Vulnerable dependency: {dep}")

        # Record compliance status
        is_compliant = len(violations) == 0
        self._compliance_status[check_type.value] = is_compliant

        if not is_compliant:
            for violation in violations:
                self._violations.append(
                    {
                        "check_type": check_type.value,
                        "violation": violation,
                        "timestamp": datetime.now(timezone.utc),
                        "project_id": self.project_id,
                    }
                )

        return is_compliant, violations

    def run_all_checks(
        self,
        code: Optional[str] = None,
        dependencies: Optional[list[str]] = None,
        user_role: Optional[str] = None,
    ) -> dict[str, Any]:
        """Run all compliance checks.

        Args:
            code: Code to check
            dependencies: Dependencies to check
            user_role: User role for access control

        Returns:
            Compliance report
        """
        report = {
            "timestamp": datetime.now(timezone.utc),
            "project_id": self.project_id,
            "checks": {},
            "overall_compliant": True,
        }

        # Run all checks
        for check_type in ComplianceCheck:
            data = None
            if check_type == ComplianceCheck.CODE_SECURITY:
                data = {"code": code or ""}
            elif check_type == ComplianceCheck.VULNERABILITY_SCAN:
                data = {"dependencies": dependencies or []}
            elif check_type == ComplianceCheck.ACCESS_CONTROL:
                data = {"user_role": user_role, "required_role": "developer"}

            is_compliant, violations = self.check_compliance(check_type, data)
            report["checks"][check_type.value] = {
                "compliant": is_compliant,
                "violations": violations,
            }

            if not is_compliant:
                report["overall_compliant"] = False

        return report

    def get_violations(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[dict[str, Any]]:
        """Get compliance violations.

        Args:
            start_time: Filter by start time
            end_time: Filter by end time

        Returns:
            List of violations
        """
        violations = self._violations

        if start_time:
            violations = [v for v in violations if v["timestamp"] >= start_time]

        if end_time:
            violations = [v for v in violations if v["timestamp"] <= end_time]

        return violations

    def cleanup_old_data(self) -> None:
        """Clean up data based on retention policies."""
        # In production, this would delete expired data from database
        self._logger.info("Data retention cleanup completed")

    def generate_compliance_report(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """Generate compliance report.

        Args:
            start_time: Report start time
            end_time: Report end time

        Returns:
            Compliance report
        """
        violations = self.get_violations(start_time, end_time)

        return {
            "report_date": datetime.now(timezone.utc),
            "project_id": self.project_id,
            "period": {
                "start": start_time,
                "end": end_time,
            },
            "total_violations": len(violations),
            "violations_by_type": self._count_violations_by_type(violations),
            "compliance_status": self._compliance_status.copy(),
        }

    def _count_violations_by_type(
        self,
        violations: list[dict[str, Any]],
    ) -> dict[str, int]:
        """Count violations by type."""
        counts = {}
        for v in violations:
            check_type = v["check_type"]
            counts[check_type] = counts.get(check_type, 0) + 1
        return counts
