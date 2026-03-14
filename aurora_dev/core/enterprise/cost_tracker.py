"""
Cost tracking for AURORA-DEV enterprise features.

Tracks API costs and provides budget alerts.
"""
from datetime import datetime, timezone
from typing import Any, Optional
from enum import Enum

from aurora_dev.core.logging import get_logger


class CostAlert(Enum):
    """Cost alert levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class CostTracker:
    """Tracks API costs and manages budgets."""

    def __init__(
        self,
        project_id: Optional[str] = None,
        monthly_budget: float = 100.0,
    ) -> None:
        """Initialize cost tracker.

        Args:
            project_id: Project identifier
            monthly_budget: Monthly budget limit in USD
        """
        self.project_id = project_id
        self.monthly_budget = monthly_budget
        self._logger = get_logger("cost_tracker")

        # Cost tracking
        self._total_cost = 0.0
        self._monthly_cost = 0.0
        self._last_reset = datetime.now(timezone.utc)

        # Token tracking
        self._input_tokens = 0
        self._output_tokens = 0

        # Alert history
        self._alerts: list[tuple[datetime, CostAlert, str]] = []

    def add_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model: str = "unknown",
        cost_usd: Optional[float] = None,
    ) -> None:
        """Add cost from an API call.

        Args:
            input_tokens: Input tokens used
            output_tokens: Output tokens used
            model: Model used
            cost_usd: Optional explicit cost in USD
        """
        # Calculate cost if not provided
        if cost_usd is None:
            # Simplified pricing (adjust based on actual model)
            input_cost_per_m = 0.25  # $0.25 per 1M tokens (Haiku)
            output_cost_per_m = 1.25  # $1.25 per 1M tokens (Haiku)
            cost_usd = (input_tokens / 1_000_000) * input_cost_per_m + (
                output_tokens / 1_000_000
            ) * output_cost_per_m

        # Update tracking
        self._total_cost += cost_usd
        self._monthly_cost += cost_usd
        self._input_tokens += input_tokens
        self._output_tokens += output_tokens

        # Log the cost
        self._logger.info(
            f"Added cost: ${cost_usd:.4f} for {model}",
            extra={
                "project_id": self.project_id,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model": model,
                "cost_usd": cost_usd,
            },
        )

        # Check budget
        self._check_budget()

    def _check_budget(self) -> None:
        """Check if budget limits are exceeded."""
        if self._monthly_cost > self.monthly_budget:
            alert_msg = f"Monthly budget exceeded: ${self._monthly_cost:.2f} / ${self.monthly_budget:.2f}"
            self._alerts.append(
                (datetime.now(timezone.utc), CostAlert.CRITICAL, alert_msg)
            )
            self._logger.warning(alert_msg)
        elif self._monthly_cost > self.monthly_budget * 0.8:
            alert_msg = f"Monthly budget 80% used: ${self._monthly_cost:.2f} / ${self.monthly_budget:.2f}"
            self._alerts.append(
                (datetime.now(timezone.utc), CostAlert.WARNING, alert_msg)
            )
            self._logger.warning(alert_msg)

    def get_current_cost(self) -> float:
        """Get total cost so far."""
        return self._total_cost

    def get_monthly_cost(self) -> float:
        """Get cost this month."""
        return self._monthly_cost

    def get_token_usage(self) -> dict[str, int]:
        """Get total token usage."""
        return {
            "input_tokens": self._input_tokens,
            "output_tokens": self._output_tokens,
        }

    def reset_monthly(self) -> None:
        """Reset monthly cost tracking."""
        self._monthly_cost = 0.0
        self._last_reset = datetime.now(timezone.utc)
        self._logger.info("Monthly cost tracking reset")

    def get_alerts(
        self, since: Optional[datetime] = None
    ) -> list[tuple[datetime, CostAlert, str]]:
        """Get cost alerts since a given time."""
        if since is None:
            return self._alerts
        return [alert for alert in self._alerts if alert[0] >= since]
