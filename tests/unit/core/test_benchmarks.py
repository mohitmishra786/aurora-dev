"""
Unit tests for RuntimeBenchmark.
"""
import pytest
from aurora_dev.core.benchmarks import RuntimeBenchmark


class TestRuntimeBenchmark:
    """Tests for RuntimeBenchmark metrics collection."""

    @pytest.fixture
    def benchmark(self):
        """Create a fresh RuntimeBenchmark instance."""
        return RuntimeBenchmark()

    def test_initialization(self, benchmark):
        """Test RuntimeBenchmark initializes cleanly."""
        assert benchmark._components == {}
        assert benchmark._task_durations == []
        assert benchmark._start_time is not None

    def test_record_latency(self, benchmark):
        """Test recording latency metrics."""
        benchmark.record_latency("llm_api", 150.0, success=True)
        benchmark.record_latency("llm_api", 200.0, success=True)
        benchmark.record_latency("llm_api", 500.0, success=False)
        
        assert "llm_api" in benchmark._components
        metrics = benchmark._components["llm_api"]
        assert metrics.total_calls == 3
        assert metrics.error_count == 1

    def test_record_tokens(self, benchmark):
        """Test recording token usage."""
        benchmark.record_tokens("agent-1", prompt=500, completion=200)
        benchmark.record_tokens("agent-1", prompt=300, completion=100)
        
        usage = benchmark._token_usage["agent-1"]
        assert usage["prompt"] == 800
        assert usage["completion"] == 300
        assert usage["total"] == 1100

    def test_record_task_completion(self, benchmark):
        """Test recording task completion times."""
        benchmark.record_task_completion(1500.0)
        benchmark.record_task_completion(2000.0)
        benchmark.record_task_completion(800.0)
        
        assert len(benchmark._task_durations) == 3

    def test_record_test_result(self, benchmark):
        """Test recording test results."""
        benchmark.record_test_result("unit", passed=10, failed=2, skipped=1)
        benchmark.record_test_result("unit", passed=5, failed=0, skipped=0)
        
        results = benchmark._test_results["unit"]
        assert results["passed"] == 15
        assert results["failed"] == 2
        assert results["skipped"] == 1

    def test_get_report(self, benchmark):
        """Test generating a complete report."""
        benchmark.record_latency("api", 100.0, success=True)
        benchmark.record_tokens("agent-1", prompt=100, completion=50)
        benchmark.record_task_completion(500.0)
        benchmark.record_test_result("unit", passed=5)
        
        report = benchmark.get_report()
        
        assert "components" in report
        assert "token_usage" in report
        assert "test_results" in report
        assert "uptime_seconds" in report

    def test_get_report_empty(self, benchmark):
        """Test report generation with no data."""
        report = benchmark.get_report()
        
        assert report["components"] == {}
        assert report["token_usage"] == {}
        assert report["uptime_seconds"] >= 0

    def test_latency_percentiles(self, benchmark):
        """Test latency percentile calculations."""
        for i in range(100):
            benchmark.record_latency("service", float(i), success=True)
        
        report = benchmark.get_report()
        component = report["components"]["service"]
        
        assert "p50" in component
        assert "p95" in component
        assert "p99" in component
        assert component["p50"] <= component["p95"]
        assert component["p95"] <= component["p99"]
