"""
Developer Agents for AURORA-DEV.

This module contains the implementation tier agents:
- BackendAgent: API and business logic
- FrontendAgent: UI components and state management
- DatabaseAgent: Schema design and query optimization
- IntegrationAgent: Third-party service integration

Features:
- Polyglot support for multiple languages/frameworks
- Robust error handling with reflexion triggers
- Configurable temperature per task type
- Comprehensive docstrings and type hints

Example usage:
    >>> agent = BackendAgent(project_id="my-project")
    >>> result = agent.implement_endpoint(
    ...     endpoint="/api/users",
    ...     method="POST",
    ...     description="Create a new user",
    ...     language="python",
    ...     framework="fastapi"
    ... )
"""
import json
import time
from typing import Any, Optional

from aurora_dev.agents.base_agent import (
    AgentResponse,
    AgentRole,
    AgentStatus,
    BaseAgent,
    TokenUsage,
)


# Language-specific guidelines for polyglot support
LANGUAGE_GUIDELINES: dict[str, dict[str, str]] = {
    "python": {
        "backend": "\nUse FastAPI with Pydantic validation, async handlers, and type hints.",
        "database": "\nUse SQLAlchemy 2.0 with async sessions, Alembic for migrations.",
        "default": "\nFollow PEP 8, use type hints, prefer f-strings.",
    },
    "nodejs": {
        "backend": "\nUse Express/NestJS with TypeScript, Prisma ORM, Zod validation.",
        "frontend": "\nUse React/Next.js with TypeScript, Tailwind CSS.",
        "database": "\nUse Prisma or TypeORM with migrations.",
        "default": "\nUse TypeScript, ESLint, Prettier.",
    },
    "go": {
        "backend": "\nUse Gin/Fiber, struct tags for validation, goroutines for concurrency.",
        "database": "\nUse GORM or sqlx, goose for migrations.",
        "default": "\nFollow Go idioms, use context, handle errors explicitly.",
    },
    "rust": {
        "backend": "\nUse Axum/Actix, Tokio async runtime, serde for serialization.",
        "database": "\nUse SQLx or Diesel, emphasize ownership and safety.",
        "default": "\nEmphasize memory safety, use Result types, avoid unwrap.",
    },
    "java": {
        "backend": "\nUse Spring Boot, Bean Validation, JPA/Hibernate.",
        "database": "\nUse JPA/Hibernate, Flyway/Liquibase for migrations.",
        "default": "\nFollow Java conventions, use Optional, streams API.",
    },
}

# Frontend framework guidelines
FRONTEND_FRAMEWORKS: dict[str, str] = {
    "react": "\nUse functional components, React hooks, React Query for data fetching.",
    "vue": "\nUse Composition API, Pinia for state, Vue Router.",
    "svelte": "\nUse Svelte components, SvelteKit for routing, stores for state.",
    "angular": "\nUse standalone components, signals, RxJS for async.",
}

# Database-specific guidelines
DATABASE_GUIDELINES: dict[str, str] = {
    "postgresql": "\nUse UUID PKs, JSONB for flexible data, CTEs for complex queries.",
    "mysql": "\nUse InnoDB engine, proper indexes, prepared statements.",
    "mongodb": "\nDesign for query patterns, use aggregation pipelines, proper indexes.",
    "redis": "\nUse appropriate data structures, TTLs, pipelining for performance.",
}


def get_language_guidelines(
    language: str,
    agent_type: str = "default",
) -> str:
    """
    Get language-specific guidelines for prompt enhancement.
    
    Args:
        language: Programming language (python, nodejs, go, rust, java).
        agent_type: Type of agent (backend, frontend, database, default).
        
    Returns:
        Language-specific guidelines string to append to prompts.
    """
    lang = language.lower()
    if lang not in LANGUAGE_GUIDELINES:
        return ""
    
    lang_config = LANGUAGE_GUIDELINES[lang]
    return lang_config.get(agent_type, lang_config.get("default", ""))


BACKEND_SYSTEM_PROMPT = """You are the Backend Developer Agent of AURORA-DEV.

Your responsibilities:
1. Implement server-side business logic
2. Create RESTful/GraphQL APIs  
3. Set up database models and migrations
4. Implement authentication and authorization
5. Add caching and optimization layers
6. Write service classes and repositories
7. Set up background jobs and queues
8. Implement rate limiting and security

Code Standards:
- Follow repository pattern
- Dependency injection for testability
- Single responsibility principle
- Keep functions under 50 lines
- Maximum file size 500 lines
- Use parameterized queries
- Never log sensitive data

For each implementation task, output:
1. File path
2. Complete code
3. Unit tests
4. Integration tests (curl commands)
"""


FRONTEND_SYSTEM_PROMPT = """You are the Frontend Developer Agent of AURORA-DEV.

Your responsibilities:
1. Implement UI components based on design specs
2. Connect components to backend APIs
3. Handle state management (local and global)
4. Implement routing and navigation
5. Add responsive design
6. Optimize performance (code splitting, lazy loading)
7. Ensure accessibility (WCAG 2.1 AA)
8. Implement error boundaries and loading states

Component Development:
- Atomic Design: atoms → molecules → organisms → templates → pages
- Add stories for visual testing
- Test with appropriate testing library

For each component, include:
1. Component code with proper types
2. Styles
3. Tests
4. Documentation
"""


DATABASE_SYSTEM_PROMPT = """You are the Database Agent of AURORA-DEV.

Your responsibilities:
1. Design optimal database schemas
2. Write efficient queries
3. Create indexes for performance
4. Set up migrations
5. Implement data validation
6. Plan for scalability and partitioning
7. Add full-text search capabilities
8. Implement backup and recovery

Design Guidelines:
- Apply 3NF as baseline, denormalize for performance
- Timestamps on all tables
- Check constraints for business rules
- Foreign keys for referential integrity
- Indexes for common query patterns

For schema designs, output:
1. CREATE TABLE/schema statements
2. INDEX definitions
3. Migration files (up/down)
4. Query examples with EXPLAIN
"""


INTEGRATION_SYSTEM_PROMPT = """You are the Integration Agent of AURORA-DEV.

Your responsibilities:
1. Connect frontend to backend APIs
2. Integrate third-party services (Stripe, SendGrid, AWS)
3. Handle authentication flows (OAuth, SSO)
4. Implement error handling across boundaries
5. Set up webhooks and event handlers
6. Manage API rate limiting and retry logic
7. Add request/response logging and tracing
8. Implement circuit breakers for resilience

Integration Patterns:
- API client with retry and exponential backoff
- Circuit breaker (closed → open → half-open)
- Token bucket rate limiting
- Webhook signature verification

For integrations, provide:
1. API client class
2. Error handling strategy
3. Retry configuration
4. Webhook handlers
"""


class BackendAgent(BaseAgent):
    """
    Backend Developer Agent for API and business logic implementation.
    
    Supports multiple languages and frameworks with dynamic prompt
    enhancement based on the target stack.
    
    Attributes:
        _generated_files: Cache of generated file contents.
        
    Example:
        >>> agent = BackendAgent(project_id="my-project")
        >>> result = agent.implement_endpoint(
        ...     endpoint="/api/users",
        ...     method="POST",
        ...     description="Create user",
        ...     language="python",
        ...     framework="fastapi"
        ... )
    """
    
    # Default temperature for backend tasks (precision-focused)
    DEFAULT_TEMPERATURE = 0.3
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        """
        Initialize the Backend Agent.
        
        Args:
            project_id: Associated project identifier.
            session_id: Session identifier for tracking.
            name: Human-readable agent name.
        """
        super().__init__(
            name=name or "BackendDeveloper",
            project_id=project_id,
            session_id=session_id,
        )
        self._generated_files: dict[str, str] = {}
    
    @property
    def role(self) -> AgentRole:
        """Return the agent's role."""
        return AgentRole.BACKEND
    
    @property
    def system_prompt(self) -> str:
        """Return the base system prompt."""
        return BACKEND_SYSTEM_PROMPT
    
    def _get_enhanced_prompt(
        self,
        language: str = "python",
        framework: Optional[str] = None,
    ) -> str:
        """
        Get system prompt enhanced with language-specific guidelines.
        
        Args:
            language: Target programming language.
            framework: Optional framework override.
            
        Returns:
            Enhanced system prompt string.
        """
        base = self.system_prompt
        lang_guide = get_language_guidelines(language, "backend")
        
        if framework:
            base += f"\n\nFramework: {framework}"
        
        return base + lang_guide
    
    def _execute_with_retry(
        self,
        prompt: str,
        language: str = "python",
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """
        Execute API call with retry and error handling.
        
        Args:
            prompt: The prompt to send.
            language: Target language for guidelines.
            max_retries: Maximum retry attempts.
            
        Returns:
            Result dict with content, success, and optional error info.
        """
        last_error: Optional[str] = None
        
        for attempt in range(max_retries):
            response = self._call_api(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096,
                temperature=self.DEFAULT_TEMPERATURE,
            )
            
            if response.success:
                return {
                    "content": response.content,
                    "success": True,
                    "attempts": attempt + 1,
                }
            
            last_error = response.error
            self._logger.warning(
                f"API call failed (attempt {attempt + 1}/{max_retries}): {last_error}"
            )
            
            # Exponential backoff
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
        
        return {
            "content": "",
            "success": False,
            "error": last_error,
            "needs_reflexion": True,
            "attempts": max_retries,
        }
    
    def implement_endpoint(
        self,
        endpoint: str,
        method: str,
        description: str,
        request_schema: Optional[dict] = None,
        response_schema: Optional[dict] = None,
        language: str = "python",
        framework: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Implement an API endpoint with full code generation.
        
        Args:
            endpoint: API endpoint path (e.g., "/api/users").
            method: HTTP method (GET, POST, PUT, DELETE, etc.).
            description: Detailed description of endpoint behavior.
            request_schema: Optional request body schema.
            response_schema: Optional response schema.
            language: Target programming language.
            framework: Optional framework (e.g., "fastapi", "express").
            
        Returns:
            Dict with endpoint, method, implementation, and success status.
        """
        self._set_status(AgentStatus.WORKING)
        
        fw_info = framework or self._get_default_framework(language)
        lang_guide = get_language_guidelines(language, "backend")
        
        prompt = f"""Implement the following API endpoint:

LANGUAGE: {language}
FRAMEWORK: {fw_info}
ENDPOINT: {method} {endpoint}
DESCRIPTION: {description}

REQUEST SCHEMA:
{json.dumps(request_schema or {}, indent=2)}

RESPONSE SCHEMA:
{json.dumps(response_schema or {}, indent=2)}

{lang_guide}

Provide:
1. Route handler code
2. Service class with business logic
3. Repository class for database access
4. Unit tests for all components
5. Curl command for testing

Use these patterns:
- Dependency injection
- Error handling with custom exceptions
- Input validation
- Logging with context
"""
        
        result = self._execute_with_retry(prompt, language)
        
        self._set_status(AgentStatus.IDLE)
        
        return {
            "endpoint": endpoint,
            "method": method,
            "language": language,
            "framework": fw_info,
            "implementation": result.get("content", ""),
            "success": result["success"],
            "error": result.get("error"),
            "needs_reflexion": result.get("needs_reflexion", False),
        }
    
    def _get_default_framework(self, language: str) -> str:
        """Get default framework for a language."""
        defaults = {
            "python": "FastAPI",
            "nodejs": "Express with TypeScript",
            "go": "Gin",
            "rust": "Axum",
            "java": "Spring Boot",
        }
        return defaults.get(language.lower(), "native")
    
    def implement_service(
        self,
        service_name: str,
        methods: list[str],
        dependencies: Optional[list[str]] = None,
        language: str = "python",
    ) -> dict[str, Any]:
        """
        Implement a service class with business logic.
        
        Args:
            service_name: Name of the service (e.g., "User", "Order").
            methods: List of method names to implement.
            dependencies: Optional list of service dependencies.
            language: Target programming language.
            
        Returns:
            Dict with service name, implementation, and success status.
        """
        self._set_status(AgentStatus.WORKING)
        
        lang_guide = get_language_guidelines(language, "backend")
        
        prompt = f"""Implement a service class:

LANGUAGE: {language}
SERVICE: {service_name}Service
METHODS: {', '.join(methods)}
DEPENDENCIES: {', '.join(dependencies or [])}

{lang_guide}

Provide:
1. Service class with all methods
2. Interface/protocol for dependency injection
3. Unit tests with mocks
4. Error handling

Follow SOLID principles and keep methods focused.
"""
        
        result = self._execute_with_retry(prompt, language)
        
        self._set_status(AgentStatus.IDLE)
        
        return {
            "service": service_name,
            "language": language,
            "implementation": result.get("content", ""),
            "success": result["success"],
            "error": result.get("error"),
            "needs_reflexion": result.get("needs_reflexion", False),
        }
    
    def execute(self, task: dict[str, Any]) -> AgentResponse:
        """
        Execute a backend development task.
        
        Args:
            task: Task definition containing:
                - operation: "endpoint" or "service"
                - language: Target language (default: python)
                - framework: Optional framework override
                - Additional operation-specific parameters
                
        Returns:
            AgentResponse with execution results.
        """
        start_time = time.time()
        operation = task.get("operation", "endpoint")
        language = task.get("language", "python")
        
        try:
            if operation == "endpoint":
                result = self.implement_endpoint(
                    task.get("endpoint", "/api/resource"),
                    task.get("method", "GET"),
                    task.get("description", ""),
                    task.get("request_schema"),
                    task.get("response_schema"),
                    language=language,
                    framework=task.get("framework"),
                )
            elif operation == "service":
                result = self.implement_service(
                    task.get("service_name", "Resource"),
                    task.get("methods", []),
                    task.get("dependencies"),
                    language=language,
                )
            else:
                result = {
                    "error": f"Unknown operation: {operation}",
                    "success": False,
                }
            
            execution_time = (time.time() - start_time) * 1000
            
            return AgentResponse(
                content=json.dumps(result, indent=2),
                token_usage=self._total_usage,
                model=self._model,
                stop_reason="end_turn",
                execution_time_ms=execution_time,
                error=result.get("error") if not result.get("success") else None,
            )
            
        except Exception as e:
            self._logger.error(f"Execute failed: {e}")
            return AgentResponse(
                content=json.dumps({
                    "error": str(e),
                    "needs_reflexion": True,
                    "operation": operation,
                }),
                token_usage=self._total_usage,
                model=self._model,
                stop_reason="error",
                execution_time_ms=(time.time() - start_time) * 1000,
                error=str(e),
            )


class FrontendAgent(BaseAgent):
    """
    Frontend Developer Agent for UI component implementation.
    
    Supports multiple frontend frameworks (React, Vue, Svelte, Angular)
    with dynamic prompt enhancement.
    
    Attributes:
        _components: Cache of generated component content.
    """
    
    DEFAULT_TEMPERATURE = 0.3
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        """Initialize the Frontend Agent."""
        super().__init__(
            name=name or "FrontendDeveloper",
            project_id=project_id,
            session_id=session_id,
        )
        self._components: dict[str, str] = {}
    
    @property
    def role(self) -> AgentRole:
        """Return the agent's role."""
        return AgentRole.FRONTEND
    
    @property
    def system_prompt(self) -> str:
        """Return the base system prompt."""
        return FRONTEND_SYSTEM_PROMPT
    
    def _get_framework_guidelines(self, framework: str = "react") -> str:
        """Get framework-specific guidelines."""
        return FRONTEND_FRAMEWORKS.get(framework.lower(), FRONTEND_FRAMEWORKS["react"])
    
    def _execute_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """Execute API call with retry and error handling."""
        last_error: Optional[str] = None
        
        for attempt in range(max_retries):
            response = self._call_api(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096,
                temperature=self.DEFAULT_TEMPERATURE,
            )
            
            if response.success:
                return {"content": response.content, "success": True}
            
            last_error = response.error
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
        
        return {
            "content": "",
            "success": False,
            "error": last_error,
            "needs_reflexion": True,
        }
    
    def implement_component(
        self,
        component_name: str,
        props: dict[str, str],
        description: str,
        design_tokens: Optional[dict] = None,
        framework: str = "react",
        language: str = "typescript",
    ) -> dict[str, Any]:
        """
        Implement a UI component.
        
        Args:
            component_name: Name of the component.
            props: Component props with types.
            description: Component description.
            design_tokens: Optional design system tokens.
            framework: Frontend framework (react, vue, svelte).
            language: typescript or javascript.
            
        Returns:
            Dict with component implementation and metadata.
        """
        self._set_status(AgentStatus.WORKING)
        
        fw_guide = self._get_framework_guidelines(framework)
        
        prompt = f"""Implement a {framework.title()} component:

COMPONENT: {component_name}
DESCRIPTION: {description}
LANGUAGE: {language}

PROPS:
{json.dumps(props, indent=2)}

DESIGN TOKENS:
{json.dumps(design_tokens or {}, indent=2)}

{fw_guide}

Provide:
1. Component code with proper types
2. Styles (CSS modules or Tailwind)
3. Unit tests
4. Accessibility attributes (ARIA)

Follow atomic design principles.
"""
        
        result = self._execute_with_retry(prompt)
        
        self._set_status(AgentStatus.IDLE)
        
        return {
            "component": component_name,
            "framework": framework,
            "implementation": result.get("content", ""),
            "success": result["success"],
            "error": result.get("error"),
        }
    
    def implement_page(
        self,
        page_name: str,
        route: str,
        components: list[str],
        data_requirements: Optional[dict] = None,
        framework: str = "react",
    ) -> dict[str, Any]:
        """
        Implement a page component.
        
        Args:
            page_name: Name of the page.
            route: Route path.
            components: List of child components.
            data_requirements: Data fetching requirements.
            framework: Frontend framework.
            
        Returns:
            Dict with page implementation and metadata.
        """
        self._set_status(AgentStatus.WORKING)
        
        fw_guide = self._get_framework_guidelines(framework)
        
        prompt = f"""Implement a {framework.title()} page:

PAGE: {page_name}
ROUTE: {route}
COMPONENTS: {', '.join(components)}

DATA REQUIREMENTS:
{json.dumps(data_requirements or {}, indent=2)}

{fw_guide}

Provide:
1. Page component with data fetching
2. Loading and error states
3. SEO metadata
4. E2E test
5. Responsive layout
"""
        
        result = self._execute_with_retry(prompt)
        
        self._set_status(AgentStatus.IDLE)
        
        return {
            "page": page_name,
            "route": route,
            "framework": framework,
            "implementation": result.get("content", ""),
            "success": result["success"],
            "error": result.get("error"),
        }
    
    def execute(self, task: dict[str, Any]) -> AgentResponse:
        """Execute a frontend task."""
        start_time = time.time()
        operation = task.get("operation", "component")
        framework = task.get("framework", "react")
        
        try:
            if operation == "component":
                result = self.implement_component(
                    task.get("component_name", "Component"),
                    task.get("props", {}),
                    task.get("description", ""),
                    task.get("design_tokens"),
                    framework=framework,
                    language=task.get("language", "typescript"),
                )
            elif operation == "page":
                result = self.implement_page(
                    task.get("page_name", "Page"),
                    task.get("route", "/"),
                    task.get("components", []),
                    task.get("data_requirements"),
                    framework=framework,
                )
            else:
                result = {"error": f"Unknown operation: {operation}", "success": False}
            
            return AgentResponse(
                content=json.dumps(result, indent=2),
                token_usage=self._total_usage,
                model=self._model,
                stop_reason="end_turn",
                execution_time_ms=(time.time() - start_time) * 1000,
            )
            
        except Exception as e:
            return AgentResponse(
                content=json.dumps({"error": str(e), "needs_reflexion": True}),
                token_usage=self._total_usage,
                model=self._model,
                stop_reason="error",
                execution_time_ms=(time.time() - start_time) * 1000,
                error=str(e),
            )


class DatabaseAgent(BaseAgent):
    """
    Database Agent for schema design and query optimization.
    
    Supports multiple database systems with optimized prompts.
    Uses lower temperature (0.2) for precision.
    """
    
    # Lower temperature for database precision
    DEFAULT_TEMPERATURE = 0.2
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        """Initialize the Database Agent."""
        super().__init__(
            name=name or "DatabaseSpecialist",
            project_id=project_id,
            session_id=session_id,
        )
    
    @property
    def role(self) -> AgentRole:
        """Return the agent's role."""
        return AgentRole.DATABASE
    
    @property
    def system_prompt(self) -> str:
        """Return the base system prompt."""
        return DATABASE_SYSTEM_PROMPT
    
    def _get_db_guidelines(self, database: str) -> str:
        """Get database-specific guidelines."""
        return DATABASE_GUIDELINES.get(database.lower(), DATABASE_GUIDELINES["postgresql"])
    
    def _execute_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """Execute API call with retry and error handling."""
        last_error: Optional[str] = None
        
        for attempt in range(max_retries):
            response = self._call_api(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096,
                temperature=self.DEFAULT_TEMPERATURE,
            )
            
            if response.success:
                return {"content": response.content, "success": True}
            
            last_error = response.error
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
        
        return {
            "content": "",
            "success": False,
            "error": last_error,
            "needs_reflexion": True,
        }
    
    def design_schema(
        self,
        entities: list[dict[str, Any]],
        relationships: list[dict[str, str]],
        database: str = "postgresql",
        language: str = "python",
    ) -> dict[str, Any]:
        """
        Design database schema with ORM models.
        
        Args:
            entities: List of entity definitions.
            relationships: List of relationships between entities.
            database: Target database system.
            language: Programming language for ORM models.
            
        Returns:
            Dict with schema definition and success status.
        """
        self._set_status(AgentStatus.WORKING)
        
        db_guide = self._get_db_guidelines(database)
        lang_guide = get_language_guidelines(language, "database")
        
        prompt = f"""Design a {database} schema:

LANGUAGE: {language}
ENTITIES:
{json.dumps(entities, indent=2)}

RELATIONSHIPS:
{json.dumps(relationships, indent=2)}

{db_guide}
{lang_guide}

Provide:
1. CREATE TABLE statements (or equivalent)
2. INDEX definitions
3. Constraints (FK, CHECK, UNIQUE)
4. Migration file (up/down)
5. ORM models in {language}
6. Sample queries with EXPLAIN
"""
        
        result = self._execute_with_retry(prompt)
        
        self._set_status(AgentStatus.IDLE)
        
        return {
            "database": database,
            "language": language,
            "schema": result.get("content", ""),
            "success": result["success"],
            "error": result.get("error"),
        }
    
    def optimize_query(
        self,
        query: str,
        table_stats: Optional[dict] = None,
        database: str = "postgresql",
    ) -> dict[str, Any]:
        """
        Optimize a database query.
        
        Args:
            query: SQL query to optimize.
            table_stats: Optional table statistics.
            database: Database system.
            
        Returns:
            Dict with optimization analysis and suggestions.
        """
        self._set_status(AgentStatus.WORKING)
        
        db_guide = self._get_db_guidelines(database)
        
        prompt = f"""Optimize this {database} query:

QUERY:
{query}

TABLE STATS:
{json.dumps(table_stats or {}, indent=2)}

{db_guide}

Provide:
1. Analysis of current query
2. Optimized query
3. Required indexes
4. Expected improvement
5. EXPLAIN ANALYZE comparison
"""
        
        result = self._execute_with_retry(prompt)
        
        self._set_status(AgentStatus.IDLE)
        
        return {
            "original_query": query,
            "database": database,
            "optimization": result.get("content", ""),
            "success": result["success"],
            "error": result.get("error"),
        }
    
    def execute(self, task: dict[str, Any]) -> AgentResponse:
        """Execute a database task."""
        start_time = time.time()
        operation = task.get("operation", "schema")
        database = task.get("database", "postgresql")
        
        try:
            if operation == "schema":
                result = self.design_schema(
                    task.get("entities", []),
                    task.get("relationships", []),
                    database=database,
                    language=task.get("language", "python"),
                )
            elif operation == "optimize":
                result = self.optimize_query(
                    task.get("query", ""),
                    task.get("table_stats"),
                    database=database,
                )
            else:
                result = {"error": f"Unknown operation: {operation}", "success": False}
            
            return AgentResponse(
                content=json.dumps(result, indent=2),
                token_usage=self._total_usage,
                model=self._model,
                stop_reason="end_turn",
                execution_time_ms=(time.time() - start_time) * 1000,
            )
            
        except Exception as e:
            return AgentResponse(
                content=json.dumps({"error": str(e), "needs_reflexion": True}),
                token_usage=self._total_usage,
                model=self._model,
                stop_reason="error",
                execution_time_ms=(time.time() - start_time) * 1000,
                error=str(e),
            )


class IntegrationAgent(BaseAgent):
    """
    Integration Agent for third-party service integration.
    
    Handles API clients, authentication flows, webhooks,
    and resilience patterns (circuit breaker, retry).
    """
    
    DEFAULT_TEMPERATURE = 0.3
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        """Initialize the Integration Agent."""
        super().__init__(
            name=name or "IntegrationSpecialist",
            project_id=project_id,
            session_id=session_id,
        )
    
    @property
    def role(self) -> AgentRole:
        """Return the agent's role."""
        return AgentRole.INTEGRATION
    
    @property
    def system_prompt(self) -> str:
        """Return the base system prompt."""
        return INTEGRATION_SYSTEM_PROMPT
    
    def _execute_with_retry(
        self,
        prompt: str,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """Execute API call with retry and error handling."""
        last_error: Optional[str] = None
        
        for attempt in range(max_retries):
            response = self._call_api(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096,
                temperature=self.DEFAULT_TEMPERATURE,
            )
            
            if response.success:
                return {"content": response.content, "success": True}
            
            last_error = response.error
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
        
        return {
            "content": "",
            "success": False,
            "error": last_error,
            "needs_reflexion": True,
        }
    
    def integrate_service(
        self,
        service: str,
        operations: list[str],
        auth_type: str = "api_key",
        language: str = "python",
    ) -> dict[str, Any]:
        """
        Create integration for a third-party service.
        
        Args:
            service: Service name (e.g., "Stripe", "SendGrid").
            operations: List of operations to implement.
            auth_type: Authentication type (api_key, oauth2, jwt).
            language: Target programming language.
            
        Returns:
            Dict with integration code and success status.
        """
        self._set_status(AgentStatus.WORKING)
        
        lang_guide = get_language_guidelines(language, "backend")
        
        prompt = f"""Create integration for {service}:

LANGUAGE: {language}
OPERATIONS: {', '.join(operations)}
AUTH TYPE: {auth_type}

{lang_guide}

Provide:
1. API client class with retry logic
2. Error handling for each error type
3. Rate limiting implementation
4. Webhook handler (if applicable)
5. Unit tests with mocks
6. Circuit breaker pattern

Use exponential backoff for retries.
"""
        
        result = self._execute_with_retry(prompt)
        
        self._set_status(AgentStatus.IDLE)
        
        return {
            "service": service,
            "language": language,
            "integration": result.get("content", ""),
            "success": result["success"],
            "error": result.get("error"),
        }
    
    def execute(self, task: dict[str, Any]) -> AgentResponse:
        """Execute an integration task."""
        start_time = time.time()
        
        try:
            result = self.integrate_service(
                task.get("service", ""),
                task.get("operations", []),
                task.get("auth_type", "api_key"),
                language=task.get("language", "python"),
            )
            
            return AgentResponse(
                content=json.dumps(result, indent=2),
                token_usage=self._total_usage,
                model=self._model,
                stop_reason="end_turn",
                execution_time_ms=(time.time() - start_time) * 1000,
            )
            
        except Exception as e:
            return AgentResponse(
                content=json.dumps({"error": str(e), "needs_reflexion": True}),
                token_usage=self._total_usage,
                model=self._model,
                stop_reason="error",
                execution_time_ms=(time.time() - start_time) * 1000,
                error=str(e),
            )
