"""
Monitoring Agent for AURORA-DEV.

The Monitoring Agent is responsible for:
- System health monitoring
- Performance metrics collection
- Alert configuration
- Log analysis
- Incident response recommendations
- SLO/SLA tracking
"""
import json
from typing import Any, Optional

from aurora_dev.agents.base_agent import (
    AgentResponse,
    AgentRole,
    AgentStatus,
    BaseAgent,
)
from aurora_dev.core.logging import get_agent_logger


MONITORING_SYSTEM_PROMPT = """You are the Monitoring Agent of AURORA-DEV.

Your responsibilities:
1. **Health Monitoring**: Design health check strategies
2. **Metrics Collection**: Define key performance indicators
3. **Alerting**: Configure alert rules and thresholds
4. **Log Analysis**: Analyze logs for patterns and issues
5. **Incident Response**: Recommend remediation actions
6. **SLO/SLA**: Track service level objectives

Monitoring Principles:
- Focus on the four golden signals: latency, traffic, errors, saturation
- Alert on symptoms, not causes
- Avoid alert fatigue with proper thresholds
- Provide runbooks for common issues
- Enable observability: metrics, logs, traces

Key Metrics Framework:
- RED: Rate, Errors, Duration (for services)
- USE: Utilization, Saturation, Errors (for resources)
- SLI/SLO/SLA: Service level indicators and objectives
"""


class MonitoringAgent(BaseAgent):
    """
    Monitoring Agent for observability and alerting.
    
    Designs:
    - Health check strategies
    - Metrics and dashboards
    - Alert configurations
    - Log analysis patterns
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        """Initialize the Monitoring Agent."""
        super().__init__(
            name=name or "Monitoring",
            project_id=project_id,
            session_id=session_id,
        )
        
        self._monitoring_configs: dict[str, dict[str, Any]] = {}
        
        self._logger.info("Monitoring Agent initialized")
    
    @property
    def role(self) -> AgentRole:
        """Return the agent's role."""
        return AgentRole.MONITORING
    
    @property
    def system_prompt(self) -> str:
        """Return the system prompt."""
        return MONITORING_SYSTEM_PROMPT
    
    def design_health_checks(
        self,
        services: list[str],
        infrastructure: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Design health check strategy.
        
        Args:
            services: Services to monitor.
            infrastructure: Infrastructure components.
            
        Returns:
            Health check configuration.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Design a health check strategy for:

SERVICES: {', '.join(services)}
INFRASTRUCTURE: {', '.join(infrastructure or [])}

Provide health check configuration in this JSON format:
{{
    "health_checks": [
        {{
            "service": "service_name",
            "endpoint": "/health",
            "type": "http|tcp|grpc|custom",
            "interval_seconds": 30,
            "timeout_seconds": 5,
            "healthy_threshold": 2,
            "unhealthy_threshold": 3,
            "checks": [
                {{"name": "database", "type": "dependency", "critical": true}},
                {{"name": "cache", "type": "dependency", "critical": false}}
            ]
        }}
    ],
    "readiness_vs_liveness": {{
        "liveness": "What to check for liveness",
        "readiness": "What to check for readiness"
    }},
    "cascade_handling": {{
        "strategy": "circuit_breaker|graceful_degradation",
        "dependencies": ["dep1", "dep2"]
    }},
    "implementation": {{
        "framework": "kubernetes|consul|custom",
        "code_example": "health check implementation snippet"
    }}
}}
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=3072,
            temperature=0.3,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        if not response.success:
            return {"error": response.error}
        
        try:
            start = response.content.find("{")
            end = response.content.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(response.content[start:end])
                self._monitoring_configs["health_checks"] = result
                return result
        except json.JSONDecodeError:
            pass
        
        return {"raw_response": response.content}
    
    def define_metrics(
        self,
        service_type: str,
        business_metrics: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Define metrics to collect.
        
        Args:
            service_type: Type of service (api, worker, database).
            business_metrics: Business-specific metrics.
            
        Returns:
            Metrics configuration.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Define metrics for a {service_type} service:

BUSINESS METRICS: {', '.join(business_metrics or [])}

Provide metrics configuration in this JSON format:
{{
    "metrics": [
        {{
            "name": "metric_name",
            "type": "counter|gauge|histogram|summary",
            "description": "What it measures",
            "labels": ["label1", "label2"],
            "unit": "seconds|bytes|count",
            "slo_target": "p99 < 100ms"
        }}
    ],
    "golden_signals": {{
        "latency": [
            {{"metric": "request_duration_seconds", "percentiles": [0.5, 0.95, 0.99]}}
        ],
        "traffic": [
            {{"metric": "requests_total", "by": ["method", "endpoint"]}}
        ],
        "errors": [
            {{"metric": "errors_total", "by": ["type", "endpoint"]}}
        ],
        "saturation": [
            {{"metric": "active_connections", "threshold": 100}}
        ]
    }},
    "business_metrics": [
        {{"name": "metric_name", "description": "description", "calculation": "formula"}}
    ],
    "dashboards": [
        {{
            "name": "Service Overview",
            "panels": ["Request Rate", "Error Rate", "Latency Histogram"]
        }}
    ],
    "prometheus_config": "# Prometheus scrape config snippet"
}}
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=3072,
            temperature=0.3,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        if not response.success:
            return {"error": response.error}
        
        try:
            start = response.content.find("{")
            end = response.content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response.content[start:end])
        except json.JSONDecodeError:
            pass
        
        return {"raw_response": response.content}
    
    def configure_alerts(
        self,
        service: str,
        slo_targets: Optional[dict[str, str]] = None,
    ) -> dict[str, Any]:
        """
        Configure alerting rules.
        
        Args:
            service: Service to alert on.
            slo_targets: SLO targets.
            
        Returns:
            Alert configuration.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Configure alerts for:

SERVICE: {service}
SLO TARGETS: {json.dumps(slo_targets or {}, indent=2)}

Provide alert configuration in this JSON format:
{{
    "alerts": [
        {{
            "name": "HighErrorRate",
            "severity": "critical|warning|info",
            "condition": "error_rate > 0.01 for 5m",
            "description": "Error rate exceeds 1%",
            "runbook_url": "/runbooks/high-error-rate",
            "labels": {{"team": "platform"}},
            "annotations": {{"summary": "High error rate detected"}}
        }}
    ],
    "alert_groups": [
        {{
            "name": "ServiceHealth",
            "alerts": ["HighErrorRate", "HighLatency"],
            "interval": "30s"
        }}
    ],
    "routing": {{
        "critical": ["pagerduty", "slack-oncall"],
        "warning": ["slack-alerts"],
        "info": ["slack-alerts"]
    }},
    "silencing_rules": [
        {{"condition": "during_deployment", "duration": "10m"}}
    ],
    "escalation": {{
        "initial_wait": "5m",
        "repeat_interval": "1h",
        "escalation_path": ["on-call", "secondary", "manager"]
    }},
    "prometheus_rules": "# Prometheus alerting rules snippet"
}}
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=3072,
            temperature=0.3,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        if not response.success:
            return {"error": response.error}
        
        try:
            start = response.content.find("{")
            end = response.content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response.content[start:end])
        except json.JSONDecodeError:
            pass
        
        return {"raw_response": response.content}
    
    def analyze_logs(
        self,
        log_samples: list[str],
        context: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Analyze log samples for patterns.
        
        Args:
            log_samples: Sample log entries.
            context: Additional context.
            
        Returns:
            Log analysis results.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Analyze these log samples:

LOG SAMPLES:
{chr(10).join(log_samples[:20])}

CONTEXT: {context or "General log analysis"}

Provide analysis in this JSON format:
{{
    "patterns_found": [
        {{
            "pattern": "pattern description",
            "frequency": "high|medium|low",
            "severity": "error|warning|info",
            "example": "log line example"
        }}
    ],
    "issues_detected": [
        {{
            "issue": "issue description",
            "evidence": ["log line 1", "log line 2"],
            "recommended_action": "what to do"
        }}
    ],
    "anomalies": [
        {{"description": "anomaly description", "log_lines": ["line"]}}
    ],
    "recommendations": [
        "recommendation1",
        "recommendation2"
    ],
    "log_improvements": [
        "Add request_id to all logs",
        "Include more context in error logs"
    ]
}}
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
            temperature=0.3,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        if not response.success:
            return {"error": response.error}
        
        try:
            start = response.content.find("{")
            end = response.content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response.content[start:end])
        except json.JSONDecodeError:
            pass
        
        return {"raw_response": response.content}
    
    def recommend_incident_response(
        self,
        incident_type: str,
        symptoms: list[str],
    ) -> dict[str, Any]:
        """
        Recommend incident response actions.
        
        Args:
            incident_type: Type of incident.
            symptoms: Observed symptoms.
            
        Returns:
            Incident response recommendations.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Recommend incident response for:

INCIDENT TYPE: {incident_type}
SYMPTOMS: {', '.join(symptoms)}

Provide response recommendations in this JSON format:
{{
    "immediate_actions": [
        {{"action": "action description", "priority": 1, "owner": "role"}}
    ],
    "investigation_steps": [
        {{"step": "step description", "tools": ["tool1", "tool2"]}}
    ],
    "potential_causes": [
        {{"cause": "cause description", "probability": "high|medium|low", "check": "how to verify"}}
    ],
    "mitigation_options": [
        {{"option": "option description", "impact": "impact description", "rollback": "how to rollback"}}
    ],
    "communication_template": {{
        "internal": "Internal status update template",
        "external": "Customer-facing status update template"
    }},
    "post_incident": [
        "Schedule post-mortem",
        "Document timeline",
        "Identify preventive measures"
    ]
}}
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
            temperature=0.4,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        if not response.success:
            return {"error": response.error}
        
        try:
            start = response.content.find("{")
            end = response.content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response.content[start:end])
        except json.JSONDecodeError:
            pass
        
        return {"raw_response": response.content}
    
    def execute(self, task: dict[str, Any]) -> AgentResponse:
        """Execute a monitoring task."""
        self._set_status(AgentStatus.WORKING)
        
        operation = task.get("operation", "health")
        
        if operation == "health":
            result = self.design_health_checks(
                task.get("services", []),
                task.get("infrastructure"),
            )
        elif operation == "metrics":
            result = self.define_metrics(
                task.get("service_type", "api"),
                task.get("business_metrics"),
            )
        elif operation == "alerts":
            result = self.configure_alerts(
                task.get("service", ""),
                task.get("slo_targets"),
            )
        elif operation == "logs":
            result = self.analyze_logs(
                task.get("log_samples", []),
                task.get("context"),
            )
        elif operation == "incident":
            result = self.recommend_incident_response(
                task.get("incident_type", ""),
                task.get("symptoms", []),
            )
        else:
            result = {"error": f"Unknown operation: {operation}"}
        
        self._set_status(AgentStatus.IDLE)
        
        return AgentResponse(
            content=json.dumps(result, indent=2) if isinstance(result, dict) else result,
            token_usage=self._total_usage,
            model=self._model,
            stop_reason="end_turn",
            execution_time_ms=0,
        )
