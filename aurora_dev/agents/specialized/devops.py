"""
DevOps and Documentation Agents for AURORA-DEV.

This module contains:
- DevOpsAgent: CI/CD, Docker, Kubernetes, infrastructure
- DocumentationAgent: API docs, architecture docs, runbooks
- ResearchAgent: Technical research and best practices
"""
import json
from typing import Any, Optional

from aurora_dev.agents.base_agent import (
    AgentResponse,
    AgentRole,
    AgentStatus,
    BaseAgent,
)


DEVOPS_SYSTEM_PROMPT = """You are the DevOps Agent of AURORA-DEV.

Your responsibilities:
1. Create CI/CD pipelines (GitHub Actions, GitLab CI)
2. Write Dockerfiles and docker-compose
3. Create Kubernetes manifests
4. Set up infrastructure as code (Terraform)
5. Configure monitoring and alerting
6. Implement deployment strategies
7. Manage secrets and configuration
8. Set up development environments

Best Practices:
- Multi-stage Docker builds
- Non-root container users
- Health checks on all services
- Proper secrets management
- Rolling updates with rollback
- Resource limits and requests
- Liveness and readiness probes

For each infrastructure component, provide:
1. Configuration files
2. Documentation
3. Troubleshooting guide
"""


DOCUMENTATION_SYSTEM_PROMPT = """You are the Documentation Agent of AURORA-DEV.

Your responsibilities:
1. Generate API documentation (OpenAPI/Swagger)
2. Write architecture documentation
3. Create developer guides
4. Build runbooks for operations
5. Document troubleshooting procedures
6. Create onboarding guides
7. Write README files
8. Generate changelog entries

Documentation Standards:
- Clear and concise language
- Code examples for all endpoints
- Diagrams for architecture
- Step-by-step guides
- Versioned documentation
- Searchable format

For each document, include:
1. Purpose and audience
2. Prerequisites
3. Step-by-step content
4. Examples
5. Troubleshooting section
"""


RESEARCH_SYSTEM_PROMPT = """You are the Research Agent of AURORA-DEV.

Your responsibilities:
1. Search for latest frameworks and tools
2. Find security best practices
3. Research similar reference implementations
4. Identify technical risks and solutions
5. Gather performance benchmarks
6. Monitor CVEs and security advisories
7. Evaluate licensing compatibility
8. Compare technology options

Research Workflow:
1. Query formulation with variations
2. Parallel search across sources
3. Cross-reference and validate
4. Score by confidence
5. Generate comparative analysis

Output Format:
- Executive summary
- Detailed findings
- Recommendations with rationale
- Decision matrix
- References
"""


class DevOpsAgent(BaseAgent):
    """DevOps Agent for CI/CD and infrastructure."""
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(
            name=name or "DevOps",
            project_id=project_id,
            session_id=session_id,
        )
    
    @property
    def role(self) -> AgentRole:
        return AgentRole.DEVOPS
    
    @property
    def system_prompt(self) -> str:
        return DEVOPS_SYSTEM_PROMPT
    
    def create_dockerfile(
        self,
        language: str,
        framework: str,
        port: int = 8000,
    ) -> dict[str, Any]:
        """Create optimized Dockerfile."""
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Create an optimized Dockerfile:

LANGUAGE: {language}
FRAMEWORK: {framework}
PORT: {port}

Include:
1. Multi-stage build
2. Non-root user
3. Security hardening
4. Health check
5. Proper labels
6. .dockerignore

Output the complete Dockerfile.
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
            temperature=0.2,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        return {
            "dockerfile": response.content if response.success else response.error,
            "success": response.success,
        }
    
    def create_ci_pipeline(
        self,
        platform: str = "github",
        stages: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Create CI/CD pipeline configuration."""
        self._set_status(AgentStatus.WORKING)
        
        stages = stages or ["lint", "test", "build", "deploy"]
        
        prompt = f"""Create a CI/CD pipeline for {platform}:

STAGES: {', '.join(stages)}

Include:
1. Caching for dependencies
2. Parallel test execution
3. Test coverage reporting
4. Security scanning
5. Docker image building
6. Deployment to staging/production
7. Slack notifications

Output the complete workflow file.
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.2,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        return {
            "pipeline": response.content if response.success else response.error,
            "platform": platform,
            "success": response.success,
        }
    
    def create_k8s_manifests(
        self,
        service_name: str,
        replicas: int = 3,
        resources: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Create Kubernetes manifests."""
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Create Kubernetes manifests:

SERVICE: {service_name}
REPLICAS: {replicas}
RESOURCES: {json.dumps(resources or {"cpu": "100m", "memory": "256Mi"})}

Include:
1. Deployment with rolling update
2. Service (ClusterIP)
3. Ingress
4. ConfigMap
5. Secret template
6. HPA for autoscaling
7. PodDisruptionBudget
8. Readiness/Liveness probes

Output complete YAML manifests.
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.2,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        return {
            "manifests": response.content if response.success else response.error,
            "service": service_name,
            "success": response.success,
        }
    
    def execute(self, task: dict[str, Any]) -> AgentResponse:
        """Execute a DevOps task."""
        operation = task.get("operation", "dockerfile")
        
        if operation == "dockerfile":
            result = self.create_dockerfile(
                task.get("language", "python"),
                task.get("framework", "fastapi"),
                task.get("port", 8000),
            )
        elif operation == "ci":
            result = self.create_ci_pipeline(
                task.get("platform", "github"),
                task.get("stages"),
            )
        elif operation == "k8s":
            result = self.create_k8s_manifests(
                task.get("service_name", "app"),
                task.get("replicas", 3),
                task.get("resources"),
            )
        else:
            result = {"error": f"Unknown operation: {operation}"}
        
        return AgentResponse(
            content=json.dumps(result, indent=2),
            token_usage=self._total_usage,
            model=self._model,
            stop_reason="end_turn",
            execution_time_ms=0,
        )


class DocumentationAgent(BaseAgent):
    """Documentation Agent for technical writing."""
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(
            name=name or "Documentation",
            project_id=project_id,
            session_id=session_id,
        )
    
    @property
    def role(self) -> AgentRole:
        return AgentRole.DOCUMENTATION
    
    @property
    def system_prompt(self) -> str:
        return DOCUMENTATION_SYSTEM_PROMPT
    
    def generate_api_docs(
        self,
        endpoints: list[dict[str, Any]],
        title: str = "API Documentation",
    ) -> dict[str, Any]:
        """Generate API documentation."""
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Generate API documentation:

TITLE: {title}
ENDPOINTS:
{json.dumps(endpoints, indent=2)}

Include for each endpoint:
1. Description
2. Request parameters
3. Request body schema
4. Response schema
5. Example requests (curl)
6. Error responses
7. Authentication requirements

Output in Markdown format.
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.3,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        return {
            "documentation": response.content if response.success else response.error,
            "success": response.success,
        }
    
    def generate_readme(
        self,
        project_name: str,
        description: str,
        features: list[str],
        tech_stack: list[str],
    ) -> dict[str, Any]:
        """Generate README documentation."""
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Generate a comprehensive README:

PROJECT: {project_name}
DESCRIPTION: {description}
FEATURES: {', '.join(features)}
TECH STACK: {', '.join(tech_stack)}

Include:
1. Project title and badges
2. Description
3. Features list
4. Tech stack
5. Prerequisites
6. Installation steps
7. Configuration
8. Usage examples
9. API documentation link
10. Contributing guide
11. License

Output in Markdown format.
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.3,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        return {
            "readme": response.content if response.success else response.error,
            "success": response.success,
        }
    
    def generate_runbook(
        self,
        service_name: str,
        scenarios: list[str],
    ) -> dict[str, Any]:
        """Generate operational runbook."""
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Generate an operational runbook:

SERVICE: {service_name}
SCENARIOS: {', '.join(scenarios)}

For each scenario, include:
1. Alert/symptom description
2. Impact assessment
3. Quick diagnosis steps
4. Resolution steps
5. Escalation path
6. Prevention measures

Output in Markdown format.
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.3,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        return {
            "runbook": response.content if response.success else response.error,
            "success": response.success,
        }
    
    def execute(self, task: dict[str, Any]) -> AgentResponse:
        """Execute a documentation task."""
        operation = task.get("operation", "api")
        
        if operation == "api":
            result = self.generate_api_docs(
                task.get("endpoints", []),
                task.get("title", "API Documentation"),
            )
        elif operation == "readme":
            result = self.generate_readme(
                task.get("project_name", "Project"),
                task.get("description", ""),
                task.get("features", []),
                task.get("tech_stack", []),
            )
        elif operation == "runbook":
            result = self.generate_runbook(
                task.get("service_name", "Service"),
                task.get("scenarios", []),
            )
        else:
            result = {"error": f"Unknown operation: {operation}"}
        
        return AgentResponse(
            content=json.dumps(result, indent=2),
            token_usage=self._total_usage,
            model=self._model,
            stop_reason="end_turn",
            execution_time_ms=0,
        )


class ResearchAgent(BaseAgent):
    """Research Agent for technical research and analysis."""
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(
            name=name or "Research",
            project_id=project_id,
            session_id=session_id,
        )
    
    @property
    def role(self) -> AgentRole:
        return AgentRole.RESEARCH
    
    @property
    def system_prompt(self) -> str:
        return RESEARCH_SYSTEM_PROMPT
    
    def research_technology(
        self,
        topic: str,
        requirements: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Research a technology topic."""
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Research the following topic:

TOPIC: {topic}
REQUIREMENTS: {', '.join(requirements or [])}

Provide:
1. Executive summary
2. Top 3-5 options with pros/cons
3. Comparison table
4. Recommendation with rationale
5. Security considerations
6. Performance benchmarks (if available)
7. Community/maintenance status
8. References

Be objective and data-driven.
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.4,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        return {
            "research": response.content if response.success else response.error,
            "topic": topic,
            "success": response.success,
        }
    
    def compare_solutions(
        self,
        category: str,
        options: list[str],
        criteria: list[str],
    ) -> dict[str, Any]:
        """Compare multiple solutions."""
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Compare these solutions:

CATEGORY: {category}
OPTIONS: {', '.join(options)}
CRITERIA: {', '.join(criteria)}

For each option:
1. Score on each criterion (1-10)
2. Pros and cons
3. Best use cases
4. Pricing/licensing
5. Community size

Output:
1. Comparison matrix
2. Weighted scores
3. Recommendation
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.3,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        return {
            "comparison": response.content if response.success else response.error,
            "success": response.success,
        }
    
    def execute(self, task: dict[str, Any]) -> AgentResponse:
        """Execute a research task."""
        operation = task.get("operation", "research")
        
        if operation == "research":
            result = self.research_technology(
                task.get("topic", ""),
                task.get("requirements"),
            )
        elif operation == "compare":
            result = self.compare_solutions(
                task.get("category", ""),
                task.get("options", []),
                task.get("criteria", []),
            )
        else:
            result = {"error": f"Unknown operation: {operation}"}
        
        return AgentResponse(
            content=json.dumps(result, indent=2),
            token_usage=self._total_usage,
            model=self._model,
            stop_reason="end_turn",
            execution_time_ms=0,
        )
