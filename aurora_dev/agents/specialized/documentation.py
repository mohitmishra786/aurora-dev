"""
Documentation Agent for AURORA-DEV.

The Documentation Agent is responsible for:
- API documentation generation
- Code documentation
- User guides and tutorials
- README files
- Architecture documentation
- Changelog generation
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


DOCUMENTATION_SYSTEM_PROMPT = """You are the Documentation Agent of AURORA-DEV.

Your responsibilities:
1. **API Documentation**: Generate OpenAPI specs and API guides
2. **Code Documentation**: Create docstrings, comments, and inline docs
3. **User Guides**: Write tutorials and how-to guides
4. **README Files**: Create comprehensive project READMEs
5. **Architecture Docs**: Document system design and decisions

Documentation Principles:
- Write for the reader, not the writer
- Include examples for every concept
- Keep it up to date with code changes
- Use consistent formatting and style
- Provide both quick-start and detailed reference

Documentation Standards:
- READMEs should include: overview, installation, usage, contributing, license
- API docs should include: endpoints, parameters, responses, examples
- Code docs should follow language-specific conventions (docstrings, JSDoc, etc.)
"""


class DocumentationAgent(BaseAgent):
    """
    Documentation Agent for generating documentation.
    
    Generates:
    - API documentation
    - Code documentation
    - User guides
    - README files
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        """Initialize the Documentation Agent."""
        super().__init__(
            name=name or "Documentation",
            project_id=project_id,
            session_id=session_id,
        )
        
        self._generated_docs: dict[str, str] = {}
        
        self._logger.info("Documentation Agent initialized")
    
    @property
    def role(self) -> AgentRole:
        """Return the agent's role."""
        return AgentRole.DOCUMENTATION
    
    @property
    def system_prompt(self) -> str:
        """Return the system prompt."""
        return DOCUMENTATION_SYSTEM_PROMPT
    
    def generate_readme(
        self,
        project_name: str,
        description: str,
        features: list[str],
        tech_stack: Optional[list[str]] = None,
    ) -> str:
        """
        Generate a comprehensive README file.
        
        Args:
            project_name: Project name.
            description: Project description.
            features: Key features.
            tech_stack: Technology stack.
            
        Returns:
            README content in markdown.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Generate a comprehensive README.md for:

PROJECT: {project_name}
DESCRIPTION: {description}
FEATURES: {', '.join(features)}
TECH STACK: {', '.join(tech_stack or [])}

Include sections:
1. Project title with badges (build status, license, version)
2. Short description
3. Features list
4. Quick Start / Installation
5. Usage Examples
6. Configuration
7. API Reference (if applicable)
8. Contributing guidelines
9. License
10. Contact / Support

Use proper markdown formatting with code blocks for examples.
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.4,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        content = response.content if response.success else f"Error: {response.error}"
        self._generated_docs["README.md"] = content
        
        return content
    
    def generate_api_docs(
        self,
        endpoints: list[dict[str, Any]],
        title: str = "API Documentation",
    ) -> str:
        """
        Generate API documentation.
        
        Args:
            endpoints: List of endpoint definitions.
            title: Documentation title.
            
        Returns:
            API documentation in markdown.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Generate API documentation for:

TITLE: {title}
ENDPOINTS:
{json.dumps(endpoints, indent=2)}

Generate comprehensive API documentation including:
1. Overview
2. Authentication section
3. Base URL information
4. For each endpoint:
   - HTTP method and path
   - Description
   - Request parameters (path, query, body)
   - Request example (curl and language examples)
   - Response schema and example
   - Error responses
   - Rate limiting info
5. Error codes reference
6. Pagination documentation

Use markdown with code blocks for examples.
Include both curl commands and Python/JavaScript examples.
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.3,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        content = response.content if response.success else f"Error: {response.error}"
        self._generated_docs[f"{title}.md"] = content
        
        return content
    
    def generate_code_docs(
        self,
        code: str,
        language: str,
        style: str = "google",
    ) -> str:
        """
        Generate code documentation.
        
        Args:
            code: Code to document.
            language: Programming language.
            style: Documentation style (google, numpy, sphinx).
            
        Returns:
            Documented code.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Add comprehensive documentation to this {language} code using {style} style:

CODE:
```{language}
{code}
```

Add:
1. Module-level docstring
2. Class docstrings with attributes
3. Method/function docstrings with:
   - Description
   - Args
   - Returns
   - Raises
   - Examples (where helpful)
4. Inline comments for complex logic
5. Type hints (if not present)

Return the fully documented code.
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.2,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        return response.content if response.success else f"Error: {response.error}"
    
    def generate_tutorial(
        self,
        topic: str,
        target_audience: str = "intermediate",
        format_type: str = "step_by_step",
    ) -> str:
        """
        Generate a tutorial or guide.
        
        Args:
            topic: Tutorial topic.
            target_audience: beginner, intermediate, advanced.
            format_type: step_by_step, conceptual, reference.
            
        Returns:
            Tutorial content in markdown.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Generate a {format_type} tutorial for:

TOPIC: {topic}
AUDIENCE: {target_audience}

Include:
1. Introduction and learning objectives
2. Prerequisites
3. Main content with clear steps
4. Code examples with explanations
5. Common pitfalls and troubleshooting
6. Summary and next steps
7. Additional resources

Use clear language appropriate for {target_audience} developers.
Include diagrams descriptions where helpful.
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.5,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        return response.content if response.success else f"Error: {response.error}"
    
    def generate_changelog(
        self,
        changes: list[dict[str, Any]],
        version: str,
    ) -> str:
        """
        Generate a changelog entry.
        
        Args:
            changes: List of changes with type and description.
            version: Version number.
            
        Returns:
            Changelog entry in markdown.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Generate a changelog entry for version {version}:

CHANGES:
{json.dumps(changes, indent=2)}

Follow Keep a Changelog format:
- Group by: Added, Changed, Deprecated, Removed, Fixed, Security
- Include date
- Link to issues/PRs where applicable
- Write concise, meaningful descriptions

Example format:
## [version] - date
### Added
- New feature description
### Fixed
- Bug fix description
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
            temperature=0.3,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        return response.content if response.success else f"Error: {response.error}"
    
    def generate_architecture_doc(
        self,
        components: list[str],
        relationships: Optional[list[dict[str, str]]] = None,
        decisions: Optional[list[dict[str, str]]] = None,
    ) -> str:
        """
        Generate architecture documentation.
        
        Args:
            components: System components.
            relationships: Component relationships.
            decisions: Architecture decisions.
            
        Returns:
            Architecture documentation.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Generate architecture documentation for:

COMPONENTS: {', '.join(components)}
RELATIONSHIPS:
{json.dumps(relationships or [], indent=2)}
DECISIONS:
{json.dumps(decisions or [], indent=2)}

Include:
1. System Overview
2. Component Descriptions
3. Communication Patterns
4. Data Flow
5. Architecture Decisions (ADRs)
6. Deployment Architecture
7. Security Considerations
8. Scalability Approach

Include Mermaid diagrams for:
- System context (C4 Level 1)
- Container diagram (C4 Level 2)
- Data flow diagram
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.4,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        return response.content if response.success else f"Error: {response.error}"
    
    def execute(self, task: dict[str, Any]) -> AgentResponse:
        """Execute a documentation task."""
        self._set_status(AgentStatus.WORKING)
        
        operation = task.get("operation", "readme")
        
        if operation == "readme":
            content = self.generate_readme(
                task.get("project_name", "Project"),
                task.get("description", ""),
                task.get("features", []),
                task.get("tech_stack"),
            )
        elif operation == "api":
            content = self.generate_api_docs(
                task.get("endpoints", []),
                task.get("title", "API Documentation"),
            )
        elif operation == "code":
            content = self.generate_code_docs(
                task.get("code", ""),
                task.get("language", "python"),
                task.get("style", "google"),
            )
        elif operation == "tutorial":
            content = self.generate_tutorial(
                task.get("topic", ""),
                task.get("target_audience", "intermediate"),
                task.get("format_type", "step_by_step"),
            )
        elif operation == "changelog":
            content = self.generate_changelog(
                task.get("changes", []),
                task.get("version", "1.0.0"),
            )
        elif operation == "architecture":
            content = self.generate_architecture_doc(
                task.get("components", []),
                task.get("relationships"),
                task.get("decisions"),
            )
        else:
            content = json.dumps({"error": f"Unknown operation: {operation}"})
        
        self._set_status(AgentStatus.IDLE)
        
        return AgentResponse(
            content=content,
            token_usage=self._total_usage,
            model=self._model,
            stop_reason="end_turn",
            execution_time_ms=0,
        )
