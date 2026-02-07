"""
Architect Agent for AURORA-DEV.

The Architect Agent is the technical lead responsible for:
- System architecture design (microservices, monolith, serverless)
- Technology stack selection
- Database schema design
- API contract definitions
- Architecture Decision Records (ADRs)
- Diagram generation (C4, sequence, ERD)
"""
import json
from datetime import datetime, timezone
from typing import Any, Optional

from aurora_dev.agents.base_agent import (
    AgentResponse,
    AgentRole,
    AgentStatus,
    BaseAgent,
)
from aurora_dev.core.logging import get_agent_logger


ARCHITECT_SYSTEM_PROMPT = """You are the Architect Agent, the technical lead of AURORA-DEV.

Your responsibilities:
1. **System Design**: Choose architecture style (microservices, monolith, serverless, hybrid)
2. **Technology Stack**: Select optimal frameworks, databases, and tools
3. **Database Design**: Create schemas, define relationships, plan migrations
4. **API Contracts**: Define REST/GraphQL/gRPC specifications
5. **Documentation**: Generate ADRs, C4 diagrams, and technical specs

Decision Framework:
- For team_size > 10 or multiple bounded contexts → microservices
- For variable traffic and stateless operations → serverless
- For simpler projects → modular monolith

Technology Selection Weights:
- Performance: 0.25
- Developer familiarity: 0.20
- Ecosystem maturity: 0.20
- Hiring availability: 0.15
- Long-term viability: 0.10
- Community support: 0.10

Always output structured decisions in JSON format when designing systems.
Include rationale for each decision and list alternatives considered.
"""


class ArchitectAgent(BaseAgent):
    """
    Architect Agent for system design and technical leadership.
    
    Generates:
    - Architecture Decision Records (ADRs)
    - System diagrams (Mermaid format)
    - Database schemas
    - API specifications (OpenAPI)
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        """Initialize the Architect Agent."""
        super().__init__(
            name=name or "Architect",
            project_id=project_id,
            session_id=session_id,
        )
        
        # Store generated decisions
        self._decisions: list[dict[str, Any]] = []
        self._schemas: dict[str, str] = {}
        self._diagrams: dict[str, str] = {}
        
        self._logger.info("Architect Agent initialized")
    
    @property
    def role(self) -> AgentRole:
        """Return the agent's role."""
        return AgentRole.ARCHITECT
    
    @property
    def system_prompt(self) -> str:
        """Return the system prompt."""
        return ARCHITECT_SYSTEM_PROMPT
    
    def design_architecture(
        self,
        requirements: str,
        constraints: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Design system architecture based on requirements.
        
        Args:
            requirements: Natural language requirements.
            constraints: Optional constraints (budget, timeline, team size).
            
        Returns:
            Architecture design with decisions.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Design a system architecture for the following requirements:

REQUIREMENTS:
{requirements}

CONSTRAINTS:
{json.dumps(constraints or {}, indent=2)}

Provide your design in the following JSON format:
{{
    "architecture_style": "microservices|monolith|serverless|hybrid",
    "rationale": "Why this architecture style",
    "services": [
        {{
            "name": "service_name",
            "responsibility": "what it does",
            "technology": "framework/language",
            "database": "database choice",
            "api_type": "REST|GraphQL|gRPC"
        }}
    ],
    "communication": {{
        "synchronous": "how services communicate sync",
        "asynchronous": "how services communicate async"  
    }},
    "data_storage": {{
        "primary": "main database choice",
        "cache": "caching strategy",
        "search": "search solution if needed"
    }},
    "security": {{
        "authentication": "auth strategy",
        "authorization": "authz strategy"
    }},
    "scalability": {{
        "horizontal": "how to scale out",
        "vertical": "how to scale up"
    }},
    "adr": {{
        "id": "ADR-001",
        "title": "Architecture Decision Title",
        "context": "Background",
        "decision": "What was decided",
        "consequences": {{
            "positive": ["list"],
            "negative": ["list"]
        }}
    }}
}}
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.3,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        if not response.success:
            return {"error": response.error}
        
        # Parse JSON from response
        try:
            start = response.content.find("{")
            end = response.content.rfind("}") + 1
            if start >= 0 and end > start:
                design = json.loads(response.content[start:end])
                self._decisions.append(design.get("adr", {}))
                return design
        except json.JSONDecodeError:
            pass
        
        return {"raw_response": response.content}
    
    def generate_database_schema(
        self,
        entities: list[str],
        relationships: Optional[list[dict[str, str]]] = None,
        database_type: str = "postgresql",
    ) -> str:
        """
        Generate database schema.
        
        Args:
            entities: List of entity names.
            relationships: Optional list of relationships.
            database_type: Target database.
            
        Returns:
            SQL schema or DBML.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Generate a {database_type} database schema for these entities:

ENTITIES: {', '.join(entities)}

RELATIONSHIPS:
{json.dumps(relationships or [], indent=2)}

Generate SQL CREATE TABLE statements with:
- Appropriate data types
- Primary keys (UUID preferred)
- Foreign key constraints
- Indexes for common queries
- Created_at and updated_at timestamps
- Check constraints where appropriate

Output valid SQL only.
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.2,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        if response.success:
            schema = response.content
            self._schemas[f"schema_{len(self._schemas)}"] = schema
            return schema
        
        return f"-- Error: {response.error}"
    
    def generate_api_spec(
        self,
        resources: list[str],
        api_type: str = "REST",
    ) -> str:
        """
        Generate API specification.
        
        Args:
            resources: List of API resources.
            api_type: REST or GraphQL.
            
        Returns:
            OpenAPI spec or GraphQL schema.
        """
        self._set_status(AgentStatus.WORKING)
        
        if api_type == "REST":
            prompt = f"""Generate an OpenAPI 3.1 specification for these resources:

RESOURCES: {', '.join(resources)}

For each resource, include:
- GET /resources (list with pagination)
- GET /resources/{{id}} (single item)
- POST /resources (create)
- PUT /resources/{{id}} (update)
- DELETE /resources/{{id}} (delete)

Include:
- Request/response schemas
- Error responses (400, 401, 403, 404, 500)
- Authentication (Bearer token)
- Example values

Output valid OpenAPI 3.1 YAML.
"""
        else:
            prompt = f"""Generate a GraphQL schema for these resources:

RESOURCES: {', '.join(resources)}

Include:
- Type definitions
- Query types (list, single)
- Mutation types (create, update, delete)
- Input types
- Connection types for pagination

Output valid GraphQL SDL.
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.2,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        return response.content if response.success else f"Error: {response.error}"
    
    def generate_diagram(
        self,
        diagram_type: str,
        components: list[str],
        relationships: Optional[list[dict[str, str]]] = None,
    ) -> str:
        """
        Generate architecture diagram in Mermaid format.
        
        Args:
            diagram_type: c4_context, c4_container, sequence, erd
            components: List of component names.
            relationships: Optional relationships.
            
        Returns:
            Mermaid diagram code.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Generate a {diagram_type} diagram in Mermaid format:

COMPONENTS: {', '.join(components)}

RELATIONSHIPS:
{json.dumps(relationships or [], indent=2)}

Output valid Mermaid syntax that can be rendered.
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
            temperature=0.2,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        if response.success:
            diagram = response.content
            self._diagrams[f"{diagram_type}_{len(self._diagrams)}"] = diagram
            return diagram
        
        return f"Error: {response.error}"
    
    def execute(self, task: dict[str, Any]) -> AgentResponse:
        """Execute an architecture task."""
        self._set_status(AgentStatus.WORKING)
        
        operation = task.get("operation", "design")
        
        if operation == "design":
            result = self.design_architecture(
                task.get("requirements", ""),
                task.get("constraints"),
            )
        elif operation == "schema":
            result = {"schema": self.generate_database_schema(
                task.get("entities", []),
                task.get("relationships"),
                task.get("database_type", "postgresql"),
            )}
        elif operation == "api":
            result = {"spec": self.generate_api_spec(
                task.get("resources", []),
                task.get("api_type", "REST"),
            )}
        elif operation == "diagram":
            result = {"diagram": self.generate_diagram(
                task.get("diagram_type", "c4_context"),
                task.get("components", []),
                task.get("relationships"),
            )}
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
