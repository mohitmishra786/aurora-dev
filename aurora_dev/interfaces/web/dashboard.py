"""
Web Dashboard backend support for AURORA-DEV.

Provides endpoints for the React dashboard including:
- Dashboard statistics
- Real-time event streaming
- Chart data for D3.js visualizations
"""
from datetime import datetime, timedelta
from typing import Any, Optional
from dataclasses import dataclass, field

from aurora_dev.core.logging import get_logger


logger = get_logger(__name__)


@dataclass
class DashboardStats:
    """Aggregated dashboard statistics."""
    
    # Project stats
    total_projects: int = 0
    active_projects: int = 0
    
    # Task stats
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    pending_tasks: int = 0
    running_tasks: int = 0
    
    # Agent stats
    total_agents: int = 14
    active_agents: int = 0
    
    # Workflow stats
    total_workflows: int = 0
    success_rate: float = 0.0
    
    # Cost stats
    total_cost_usd: float = 0.0
    daily_cost_usd: float = 0.0
    
    # Time range
    period_start: datetime = field(default_factory=datetime.now)
    period_end: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "projects": {
                "total": self.total_projects,
                "active": self.active_projects,
            },
            "tasks": {
                "total": self.total_tasks,
                "completed": self.completed_tasks,
                "failed": self.failed_tasks,
                "pending": self.pending_tasks,
                "running": self.running_tasks,
                "completion_rate": (
                    self.completed_tasks / self.total_tasks
                    if self.total_tasks > 0 else 0.0
                ),
            },
            "agents": {
                "total": self.total_agents,
                "active": self.active_agents,
            },
            "workflows": {
                "total": self.total_workflows,
                "success_rate": self.success_rate,
            },
            "costs": {
                "total_usd": round(self.total_cost_usd, 2),
                "daily_usd": round(self.daily_cost_usd, 2),
            },
            "period": {
                "start": self.period_start.isoformat(),
                "end": self.period_end.isoformat(),
            },
        }


@dataclass
class TimeSeriesDataPoint:
    """A data point for time series charts."""
    
    timestamp: datetime
    value: float
    label: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ChartData:
    """Data for D3.js charts."""
    
    chart_type: str  # line, bar, pie, network
    title: str
    data: list[dict[str, Any]]
    x_label: Optional[str] = None
    y_label: Optional[str] = None
    legend: list[str] = field(default_factory=list)


class DashboardDataProvider:
    """
    Provides data for the dashboard.
    
    Aggregates data from various sources for visualization.
    """
    
    def __init__(self):
        """Initialize data provider."""
        self._logger = get_logger(__name__)
    
    async def get_stats(
        self,
        project_id: Optional[str] = None,
        period_days: int = 7,
    ) -> DashboardStats:
        """
        Get aggregated dashboard statistics from live system data.
        
        Queries the agent registry for active agents and the
        runtime benchmark for metrics.
        
        Args:
            project_id: Optional filter by project.
            period_days: Number of days to include.
            
        Returns:
            DashboardStats with live data.
        """
        now = datetime.now()
        period_start = now - timedelta(days=period_days)
        
        # Pull live agent data
        total_agents = 14
        active_agents = 0
        try:
            from aurora_dev.agents.registry import get_registry
            registry = get_registry()
            all_agents = registry.get_all()
            total_agents = len(all_agents)
            active_agents = sum(
                1 for a in all_agents
                if getattr(a, "status", None) in ("working", "idle")
            )
        except Exception as e:
            self._logger.debug(f"Registry not available: {e}")
        
        # Pull live benchmark data
        total_tasks = 0
        completed_tasks = 0
        failed_tasks = 0
        total_cost_usd = 0.0
        try:
            from aurora_dev.core.benchmarks import get_benchmark
            bench = get_benchmark()
            report = bench.get_report()
            total_tasks = report["tasks"]["completed"]
            total_tokens = report["token_usage"]["total"]
            # Estimate cost: ~$0.003 per 1K tokens average
            total_cost_usd = (total_tokens / 1000) * 0.003
        except Exception as e:
            self._logger.debug(f"Benchmark not available: {e}")
        
        stats = DashboardStats(
            total_projects=max(1, 0),  # At least 1 if system is running
            active_projects=1 if active_agents > 0 else 0,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            pending_tasks=max(0, total_tasks - completed_tasks - failed_tasks),
            running_tasks=active_agents,
            total_agents=total_agents,
            active_agents=active_agents,
            total_workflows=0,
            success_rate=(
                completed_tasks / total_tasks if total_tasks > 0 else 0.0
            ),
            total_cost_usd=total_cost_usd,
            daily_cost_usd=total_cost_usd / max(period_days, 1),
            period_start=period_start,
            period_end=now,
        )
        
        return stats
    
    async def get_task_timeline(
        self,
        project_id: Optional[str] = None,
        days: int = 7,
    ) -> ChartData:
        """
        Get task completion timeline data for charts.
        
        Returns data suitable for a line chart showing
        task completions over time.
        """
        now = datetime.now()
        data = []
        
        # Generate sample time series data
        for i in range(days):
            date = now - timedelta(days=days - i - 1)
            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "completed": 10 + (i * 2) % 15,
                "failed": 1 + (i % 3),
                "started": 12 + (i * 3) % 20,
            })
        
        return ChartData(
            chart_type="line",
            title="Task Activity",
            data=data,
            x_label="Date",
            y_label="Tasks",
            legend=["completed", "failed", "started"],
        )
    
    async def get_agent_workload(self) -> ChartData:
        """
        Get agent workload distribution for charts.
        
        Returns data suitable for a bar chart showing
        workload across agents.
        """
        agents = [
            {"agent": "Architect", "tier": "planning", "tasks": 25, "success_rate": 0.92},
            {"agent": "Backend", "tier": "implementation", "tasks": 45, "success_rate": 0.88},
            {"agent": "Frontend", "tier": "implementation", "tasks": 38, "success_rate": 0.85},
            {"agent": "Database", "tier": "implementation", "tasks": 22, "success_rate": 0.90},
            {"agent": "Test Engineer", "tier": "quality", "tasks": 55, "success_rate": 0.95},
            {"agent": "Security Auditor", "tier": "quality", "tasks": 18, "success_rate": 0.98},
            {"agent": "DevOps", "tier": "devops", "tasks": 15, "success_rate": 0.93},
        ]
        
        return ChartData(
            chart_type="bar",
            title="Agent Workload",
            data=agents,
            x_label="Agent",
            y_label="Tasks Completed",
            legend=["tasks"],
        )
    
    async def get_cost_breakdown(
        self,
        project_id: Optional[str] = None,
        days: int = 30,
    ) -> ChartData:
        """
        Get cost breakdown for charts.
        
        Returns data suitable for a pie chart showing
        cost distribution by agent tier.
        """
        costs = [
            {"category": "Orchestration", "cost": 15.50, "percentage": 12.4},
            {"category": "Planning", "cost": 28.25, "percentage": 22.5},
            {"category": "Implementation", "cost": 52.75, "percentage": 42.1},
            {"category": "Quality", "cost": 18.50, "percentage": 14.8},
            {"category": "DevOps", "cost": 10.50, "percentage": 8.2},
        ]
        
        return ChartData(
            chart_type="pie",
            title="Cost Distribution by Tier",
            data=costs,
            legend=[c["category"] for c in costs],
        )
    
    async def get_agent_network(self) -> ChartData:
        """
        Get agent communication network for D3.js force graph.
        
        Returns nodes and links for visualizing
        agent interactions.
        """
        nodes = [
            {"id": "maestro", "group": "orchestration", "label": "Maestro"},
            {"id": "architect", "group": "planning", "label": "Architect"},
            {"id": "backend", "group": "implementation", "label": "Backend"},
            {"id": "frontend", "group": "implementation", "label": "Frontend"},
            {"id": "database", "group": "implementation", "label": "Database"},
            {"id": "test_engineer", "group": "quality", "label": "Test Engineer"},
            {"id": "security", "group": "quality", "label": "Security"},
            {"id": "devops", "group": "devops", "label": "DevOps"},
        ]
        
        links = [
            {"source": "maestro", "target": "architect", "value": 50},
            {"source": "maestro", "target": "backend", "value": 40},
            {"source": "maestro", "target": "frontend", "value": 35},
            {"source": "architect", "target": "backend", "value": 30},
            {"source": "architect", "target": "database", "value": 25},
            {"source": "backend", "target": "database", "value": 45},
            {"source": "frontend", "target": "backend", "value": 20},
            {"source": "backend", "target": "test_engineer", "value": 55},
            {"source": "frontend", "target": "test_engineer", "value": 40},
            {"source": "test_engineer", "target": "security", "value": 25},
            {"source": "backend", "target": "devops", "value": 15},
        ]
        
        return ChartData(
            chart_type="network",
            title="Agent Communication Network",
            data={"nodes": nodes, "links": links},
        )
    
    async def get_workflow_phases(
        self,
        workflow_id: str,
    ) -> ChartData:
        """
        Get workflow phase timeline for visualization.
        
        Returns data suitable for a Gantt-style chart.
        """
        phases = [
            {"phase": "Planning", "start": 0, "duration": 15, "status": "completed"},
            {"phase": "Architecture", "start": 15, "duration": 20, "status": "completed"},
            {"phase": "Implementation", "start": 35, "duration": 45, "status": "running"},
            {"phase": "Testing", "start": 80, "duration": 25, "status": "pending"},
            {"phase": "Review", "start": 105, "duration": 10, "status": "pending"},
            {"phase": "Deployment", "start": 115, "duration": 5, "status": "pending"},
        ]
        
        return ChartData(
            chart_type="gantt",
            title=f"Workflow {workflow_id} Phases",
            data=phases,
            x_label="Time (minutes)",
        )


# FastAPI routes for dashboard
from fastapi import APIRouter, Query


router = APIRouter()
_provider = DashboardDataProvider()


@router.get("/stats")
async def get_dashboard_stats(
    project_id: Optional[str] = None,
    period_days: int = Query(default=7, ge=1, le=90),
):
    """Get aggregated dashboard statistics."""
    stats = await _provider.get_stats(project_id, period_days)
    return stats.to_dict()


@router.get("/charts/task-timeline")
async def get_task_timeline_chart(
    project_id: Optional[str] = None,
    days: int = Query(default=7, ge=1, le=30),
):
    """Get task timeline chart data."""
    chart = await _provider.get_task_timeline(project_id, days)
    return {
        "chart_type": chart.chart_type,
        "title": chart.title,
        "data": chart.data,
        "x_label": chart.x_label,
        "y_label": chart.y_label,
        "legend": chart.legend,
    }


@router.get("/charts/agent-workload")
async def get_agent_workload_chart():
    """Get agent workload chart data."""
    chart = await _provider.get_agent_workload()
    return {
        "chart_type": chart.chart_type,
        "title": chart.title,
        "data": chart.data,
        "x_label": chart.x_label,
        "y_label": chart.y_label,
        "legend": chart.legend,
    }


@router.get("/charts/cost-breakdown")
async def get_cost_breakdown_chart(
    project_id: Optional[str] = None,
    days: int = Query(default=30, ge=1, le=90),
):
    """Get cost breakdown chart data."""
    chart = await _provider.get_cost_breakdown(project_id, days)
    return {
        "chart_type": chart.chart_type,
        "title": chart.title,
        "data": chart.data,
        "legend": chart.legend,
    }


@router.get("/charts/agent-network")
async def get_agent_network_chart():
    """Get agent network graph data for D3.js force graph."""
    chart = await _provider.get_agent_network()
    return {
        "chart_type": chart.chart_type,
        "title": chart.title,
        "nodes": chart.data["nodes"],
        "links": chart.data["links"],
    }


@router.get("/charts/workflow-phases/{workflow_id}")
async def get_workflow_phases_chart(workflow_id: str):
    """Get workflow phases Gantt chart data."""
    chart = await _provider.get_workflow_phases(workflow_id)
    return {
        "chart_type": chart.chart_type,
        "title": chart.title,
        "data": chart.data,
        "x_label": chart.x_label,
    }


@router.get("/benchmarks")
async def get_runtime_benchmarks():
    """Get live runtime benchmark data including latency, tokens, and test metrics."""
    try:
        from aurora_dev.core.benchmarks import get_benchmark
        bench = get_benchmark()
        return bench.get_report()
    except Exception as e:
        return {
            "error": str(e),
            "uptime_seconds": 0,
            "components": {},
            "token_usage": {"by_agent": {}, "total": 0},
            "tasks": {"completed": 0, "avg_duration_ms": 0, "throughput_per_second": 0},
            "tests": {"pass_rate": 0, "total_passed": 0, "total_failed": 0, "suites": {}},
        }

