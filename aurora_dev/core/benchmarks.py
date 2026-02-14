"""
Runtime benchmarking and performance tracking for AURORA-DEV.

Provides real-time code quality metrics collection and reporting,
replacing static/placeholder benchmark data with actual measurements.

Metrics tracked:
- Component latency (P50, P95, P99)
- Token usage per agent
- Test pass rates
- Code quality scores
- Task completion times
"""
import time
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from aurora_dev.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class LatencyMetrics:
    """Latency statistics for a component."""
    p50: float = 0.0
    p95: float = 0.0
    p99: float = 0.0
    mean: float = 0.0
    count: int = 0


@dataclass
class ComponentMetrics:
    """Aggregated metrics for a single component."""
    name: str
    latency_samples: list[float] = field(default_factory=list)
    error_count: int = 0
    success_count: int = 0
    last_updated: Optional[datetime] = None
    
    @property
    def latency(self) -> LatencyMetrics:
        """Compute latency percentiles from samples."""
        if not self.latency_samples:
            return LatencyMetrics()
        
        sorted_samples = sorted(self.latency_samples)
        n = len(sorted_samples)
        
        return LatencyMetrics(
            p50=sorted_samples[int(n * 0.50)] if n > 0 else 0,
            p95=sorted_samples[int(n * 0.95)] if n > 1 else sorted_samples[-1],
            p99=sorted_samples[int(n * 0.99)] if n > 2 else sorted_samples[-1],
            mean=statistics.mean(sorted_samples),
            count=n,
        )
    
    @property
    def error_rate(self) -> float:
        """Compute error rate."""
        total = self.success_count + self.error_count
        if total == 0:
            return 0.0
        return self.error_count / total
    
    def record(self, duration_ms: float, success: bool = True) -> None:
        """Record a single measurement.
        
        Args:
            duration_ms: Operation duration in milliseconds.
            success: Whether the operation succeeded.
        """
        self.latency_samples.append(duration_ms)
        if success:
            self.success_count += 1
        else:
            self.error_count += 1
        self.last_updated = datetime.now()
        
        # Keep only last 1000 samples to limit memory
        if len(self.latency_samples) > 1000:
            self.latency_samples = self.latency_samples[-1000:]


class RuntimeBenchmark:
    """Runtime benchmark collector and reporter.
    
    Collects real-time performance metrics from all system components
    and provides aggregated reports for the dashboard.
    
    Example:
        >>> bench = RuntimeBenchmark()
        >>> bench.record_latency("llm_api", 1250.5, success=True)
        >>> bench.record_tokens("agent-1", prompt=500, completion=200)
        >>> report = bench.get_report()
    """
    
    def __init__(self) -> None:
        self._components: dict[str, ComponentMetrics] = {}
        self._token_usage: dict[str, dict[str, int]] = defaultdict(
            lambda: {"prompt": 0, "completion": 0, "total": 0}
        )
        self._task_durations: list[float] = []
        self._test_results: dict[str, dict[str, int]] = defaultdict(
            lambda: {"passed": 0, "failed": 0, "skipped": 0}
        )
        self._start_time = datetime.now()
        
        logger.info("RuntimeBenchmark initialized")
    
    def record_latency(
        self,
        component: str,
        duration_ms: float,
        success: bool = True,
    ) -> None:
        """Record a latency measurement for a component.
        
        Args:
            component: Component name (e.g. "llm_api", "vector_store").
            duration_ms: Duration in milliseconds.
            success: Whether the operation succeeded.
        """
        if component not in self._components:
            self._components[component] = ComponentMetrics(name=component)
        
        self._components[component].record(duration_ms, success)
    
    def record_tokens(
        self,
        agent_id: str,
        prompt: int = 0,
        completion: int = 0,
    ) -> None:
        """Record token usage for an agent.
        
        Args:
            agent_id: Agent identifier.
            prompt: Number of prompt tokens.
            completion: Number of completion tokens.
        """
        usage = self._token_usage[agent_id]
        usage["prompt"] += prompt
        usage["completion"] += completion
        usage["total"] += prompt + completion
    
    def record_task_completion(self, duration_ms: float) -> None:
        """Record a task completion duration.
        
        Args:
            duration_ms: Task duration in milliseconds.
        """
        self._task_durations.append(duration_ms)
        if len(self._task_durations) > 1000:
            self._task_durations = self._task_durations[-1000:]
    
    def record_test_result(
        self,
        suite: str,
        passed: int = 0,
        failed: int = 0,
        skipped: int = 0,
    ) -> None:
        """Record test results for a suite.
        
        Args:
            suite: Test suite name.
            passed: Number of passed tests.
            failed: Number of failed tests.
            skipped: Number of skipped tests.
        """
        results = self._test_results[suite]
        results["passed"] += passed
        results["failed"] += failed
        results["skipped"] += skipped
    
    def get_report(self) -> dict[str, Any]:
        """Generate a full benchmark report.
        
        Returns:
            Dictionary with all collected metrics.
        """
        uptime = (datetime.now() - self._start_time).total_seconds()
        
        component_report = {}
        for name, metrics in self._components.items():
            lat = metrics.latency
            component_report[name] = {
                "latency": {
                    "p50_ms": round(lat.p50, 2),
                    "p95_ms": round(lat.p95, 2),
                    "p99_ms": round(lat.p99, 2),
                    "mean_ms": round(lat.mean, 2),
                    "sample_count": lat.count,
                },
                "error_rate": round(metrics.error_rate, 4),
                "success_count": metrics.success_count,
                "error_count": metrics.error_count,
            }
        
        # Task throughput
        task_throughput = len(self._task_durations) / max(uptime, 1)
        avg_task_duration = (
            statistics.mean(self._task_durations) if self._task_durations else 0
        )
        
        # Aggregate test results
        total_passed = sum(r["passed"] for r in self._test_results.values())
        total_failed = sum(r["failed"] for r in self._test_results.values())
        total_tests = total_passed + total_failed
        test_pass_rate = total_passed / max(total_tests, 1)
        
        # Total token usage
        total_tokens = sum(u["total"] for u in self._token_usage.values())
        
        return {
            "uptime_seconds": round(uptime, 1),
            "components": component_report,
            "token_usage": {
                "by_agent": dict(self._token_usage),
                "total": total_tokens,
            },
            "tasks": {
                "completed": len(self._task_durations),
                "avg_duration_ms": round(avg_task_duration, 2),
                "throughput_per_second": round(task_throughput, 4),
            },
            "tests": {
                "pass_rate": round(test_pass_rate, 4),
                "total_passed": total_passed,
                "total_failed": total_failed,
                "suites": dict(self._test_results),
            },
            "timestamp": datetime.now().isoformat(),
        }
    
    def get_component_summary(self, component: str) -> Optional[dict[str, Any]]:
        """Get metrics summary for a specific component.
        
        Args:
            component: Component name.
            
        Returns:
            Metrics dict or None if component not tracked.
        """
        metrics = self._components.get(component)
        if not metrics:
            return None
        
        lat = metrics.latency
        return {
            "name": component,
            "latency_p50_ms": round(lat.p50, 2),
            "latency_p95_ms": round(lat.p95, 2),
            "error_rate": round(metrics.error_rate, 4),
            "total_operations": lat.count,
        }


# Singleton instance for global access
_benchmark: Optional[RuntimeBenchmark] = None


def get_benchmark() -> RuntimeBenchmark:
    """Get global benchmark instance (singleton).
    
    Returns:
        RuntimeBenchmark instance.
    """
    global _benchmark
    if _benchmark is None:
        _benchmark = RuntimeBenchmark()
    return _benchmark
