"""
Budget Manager for AURORA-DEV.

Tracks and enforces token usage limits across agents and tasks.
Prevents runaway API costs by halting agents that exceed their
allocated token budgets.

Gap B5: Missing budget management / token enforcement.
"""
import time
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class TokenBudget:
    """Token budget allocation for an agent or project."""
    
    max_prompt_tokens: int = 500_000
    max_completion_tokens: int = 200_000
    max_total_tokens: int = 700_000
    warning_threshold: float = 0.8  # Warn at 80%
    
    used_prompt: int = 0
    used_completion: int = 0
    
    @property
    def used_total(self) -> int:
        return self.used_prompt + self.used_completion
    
    @property
    def remaining_total(self) -> int:
        return max(0, self.max_total_tokens - self.used_total)
    
    @property
    def utilization(self) -> float:
        if self.max_total_tokens == 0:
            return 0.0
        return self.used_total / self.max_total_tokens
    
    @property
    def is_exceeded(self) -> bool:
        return self.used_total >= self.max_total_tokens
    
    @property
    def is_warning(self) -> bool:
        return self.utilization >= self.warning_threshold


@dataclass
class CostEstimate:
    """Estimated cost for a set of API calls."""
    
    prompt_tokens: int = 0
    completion_tokens: int = 0
    model: str = "gpt-4o"
    cost_per_1k_prompt: float = 0.005
    cost_per_1k_completion: float = 0.015
    
    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens
    
    @property
    def estimated_cost_usd(self) -> float:
        return (
            (self.prompt_tokens / 1000) * self.cost_per_1k_prompt
            + (self.completion_tokens / 1000) * self.cost_per_1k_completion
        )


class BudgetManager:
    """Manages token budgets across agents and projects.
    
    Provides:
    - Per-agent budget allocation and tracking
    - Per-project aggregate budget enforcement
    - Cost estimation and reporting
    - Warning and hard-stop thresholds
    
    Example:
        >>> budget = BudgetManager(project_budget=1_000_000)
        >>> budget.allocate_agent("architect", max_tokens=200_000)
        >>> budget.record_usage("architect", prompt=500, completion=200)
        >>> if budget.can_proceed("architect"):
        ...     agent.execute(task)
    """
    
    def __init__(
        self,
        project_budget: int = 2_000_000,
        warn_at: float = 0.8,
    ) -> None:
        self._project_budget = TokenBudget(
            max_total_tokens=project_budget,
            warning_threshold=warn_at,
        )
        self._agent_budgets: dict[str, TokenBudget] = {}
        self._usage_log: list[dict[str, Any]] = []
        self._start_time = time.time()
    
    def allocate_agent(
        self,
        agent_id: str,
        max_tokens: int = 500_000,
        max_prompt: Optional[int] = None,
        max_completion: Optional[int] = None,
    ) -> TokenBudget:
        """Allocate a token budget for an agent.
        
        Args:
            agent_id: Unique agent identifier.
            max_tokens: Total token limit.
            max_prompt: Prompt token limit (default: 70% of total).
            max_completion: Completion token limit (default: 30% of total).
            
        Returns:
            The allocated budget.
        """
        budget = TokenBudget(
            max_prompt_tokens=max_prompt or int(max_tokens * 0.7),
            max_completion_tokens=max_completion or int(max_tokens * 0.3),
            max_total_tokens=max_tokens,
        )
        self._agent_budgets[agent_id] = budget
        
        logger.info(
            f"Budget allocated for {agent_id}: {max_tokens:,} tokens"
        )
        
        return budget
    
    def record_usage(
        self,
        agent_id: str,
        prompt: int = 0,
        completion: int = 0,
    ) -> bool:
        """Record token usage for an agent.
        
        Args:
            agent_id: Agent identifier.
            prompt: Prompt tokens used.
            completion: Completion tokens used.
            
        Returns:
            True if within budget, False if exceeded.
        """
        # Update agent budget
        if agent_id in self._agent_budgets:
            self._agent_budgets[agent_id].used_prompt += prompt
            self._agent_budgets[agent_id].used_completion += completion
        else:
            # Auto-allocate with default budget
            self.allocate_agent(agent_id)
            self._agent_budgets[agent_id].used_prompt += prompt
            self._agent_budgets[agent_id].used_completion += completion
        
        # Update project budget
        self._project_budget.used_prompt += prompt
        self._project_budget.used_completion += completion
        
        # Log usage
        self._usage_log.append({
            "agent_id": agent_id,
            "prompt": prompt,
            "completion": completion,
            "timestamp": time.time(),
        })
        
        agent_budget = self._agent_budgets[agent_id]
        
        if agent_budget.is_warning and not agent_budget.is_exceeded:
            logger.warning(
                f"Agent {agent_id} at {agent_budget.utilization:.0%} "
                f"of token budget"
            )
        
        if agent_budget.is_exceeded:
            logger.error(
                f"Agent {agent_id} exceeded token budget: "
                f"{agent_budget.used_total:,}/{agent_budget.max_total_tokens:,}"
            )
            return False
        
        return True
    
    def can_proceed(self, agent_id: str) -> bool:
        """Check if an agent can continue working.
        
        Args:
            agent_id: Agent to check.
            
        Returns:
            True if agent is within budget.
        """
        if self._project_budget.is_exceeded:
            return False
        
        if agent_id in self._agent_budgets:
            return not self._agent_budgets[agent_id].is_exceeded
        
        return True
    
    def get_agent_budget(self, agent_id: str) -> Optional[TokenBudget]:
        """Get budget details for an agent."""
        return self._agent_budgets.get(agent_id)
    
    def get_project_budget(self) -> TokenBudget:
        """Get overall project budget."""
        return self._project_budget
    
    def get_cost_report(self) -> dict[str, Any]:
        """Generate a cost report for the project.
        
        Returns:
            Report with per-agent and aggregate cost data.
        """
        agent_costs = {}
        for agent_id, budget in self._agent_budgets.items():
            estimate = CostEstimate(
                prompt_tokens=budget.used_prompt,
                completion_tokens=budget.used_completion,
            )
            agent_costs[agent_id] = {
                "tokens_used": budget.used_total,
                "tokens_remaining": budget.remaining_total,
                "utilization": f"{budget.utilization:.1%}",
                "estimated_cost_usd": f"${estimate.estimated_cost_usd:.4f}",
                "exceeded": budget.is_exceeded,
            }
        
        project_estimate = CostEstimate(
            prompt_tokens=self._project_budget.used_prompt,
            completion_tokens=self._project_budget.used_completion,
        )
        
        return {
            "project": {
                "total_tokens_used": self._project_budget.used_total,
                "total_budget": self._project_budget.max_total_tokens,
                "utilization": f"{self._project_budget.utilization:.1%}",
                "estimated_cost_usd": f"${project_estimate.estimated_cost_usd:.4f}",
                "exceeded": self._project_budget.is_exceeded,
                "elapsed_seconds": time.time() - self._start_time,
            },
            "agents": agent_costs,
            "total_api_calls": len(self._usage_log),
        }
    
    def reset_agent(self, agent_id: str) -> None:
        """Reset an agent's token usage (keep budget limits)."""
        if agent_id in self._agent_budgets:
            self._agent_budgets[agent_id].used_prompt = 0
            self._agent_budgets[agent_id].used_completion = 0
