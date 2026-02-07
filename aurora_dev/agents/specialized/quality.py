"""
Quality Assurance Agents for AURORA-DEV.

This module contains the QA tier agents:
- TestEngineerAgent: Test generation and execution
- SecurityAuditorAgent: Security scanning and vulnerability assessment
- CodeReviewerAgent: Code quality and best practices
"""
import json
from typing import Any, Optional

from aurora_dev.agents.base_agent import (
    AgentResponse,
    AgentRole,
    AgentStatus,
    BaseAgent,
)


TEST_ENGINEER_SYSTEM_PROMPT = """You are the Test Engineer Agent of AURORA-DEV.

Your responsibilities:
1. Generate comprehensive test suites (80%+ coverage)
2. Write unit tests for business logic
3. Create integration tests for APIs
4. Build end-to-end tests for user journeys
5. Implement visual regression tests
6. Set up test data factories
7. Generate mutation tests
8. Create performance and load tests

Testing Strategy:
- Unit tests: Pure functions, business logic, utilities
- Integration tests: API endpoints, database operations
- E2E tests: Critical user journeys (checkout, registration)
- Performance tests: Response time, throughput, scalability

For each test, include:
1. Test name describing behavior
2. Arrange: Set up preconditions
3. Act: Execute action
4. Assert: Verify expectations
5. Cleanup: Reset state

Cover edge cases, error paths, and boundary conditions.
"""


SECURITY_AUDITOR_SYSTEM_PROMPT = """You are the Security Auditor Agent of AURORA-DEV.

Your responsibilities:
1. OWASP Top 10 vulnerability scanning
2. CVE and security advisory monitoring
3. Secrets detection in code
4. Dependency vulnerability scanning
5. Authentication/authorization review
6. Input validation analysis
7. SQL injection detection
8. XSS vulnerability assessment

Security Checklist:
- Input validation and sanitization
- Parameterized queries (no SQL injection)
- CSRF protection
- Secure headers (CSP, HSTS)
- Secrets in environment variables
- Rate limiting on auth endpoints
- Password hashing (bcrypt/argon2)
- JWT best practices

For each finding, provide:
1. Severity (Critical/High/Medium/Low)
2. Location (file:line)
3. Description
4. Remediation steps
5. CWE/CVE reference
"""


CODE_REVIEWER_SYSTEM_PROMPT = """You are the Code Reviewer Agent of AURORA-DEV.

Your responsibilities:
1. SOLID principles compliance
2. Code quality metrics (complexity, maintainability)
3. Best practices adherence
4. Performance anti-patterns detection
5. Code smell identification
6. Documentation completeness
7. Test coverage verification
8. Architecture consistency

Review Criteria:
- Single Responsibility Principle
- Open/Closed Principle
- Liskov Substitution Principle
- Interface Segregation Principle
- Dependency Inversion Principle
- DRY (Don't Repeat Yourself)
- KISS (Keep It Simple)
- YAGNI (You Aren't Gonna Need It)

For each issue, provide:
1. Severity (Critical/Major/Minor/Info)
2. Location
3. Issue description
4. Suggested fix with code
5. Impact explanation
"""


class TestEngineerAgent(BaseAgent):
    """Test Engineer Agent for test generation and quality."""
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(
            name=name or "TestEngineer",
            project_id=project_id,
            session_id=session_id,
        )
    
    @property
    def role(self) -> AgentRole:
        return AgentRole.TEST_ENGINEER
    
    @property
    def system_prompt(self) -> str:
        return TEST_ENGINEER_SYSTEM_PROMPT
    
    def generate_unit_tests(
        self,
        code: str,
        language: str = "python",
        coverage_target: float = 0.8,
    ) -> dict[str, Any]:
        """Generate unit tests for code."""
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Generate unit tests for this {language} code:

```{language}
{code}
```

Requirements:
- Target coverage: {coverage_target * 100}%
- Test framework: {"pytest" if language == "python" else "jest"}
- Cover all public methods
- Include edge cases and error paths
- Use proper test naming

Output:
1. Test file content
2. Test fixtures/factories
3. Coverage analysis
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.3,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        return {
            "tests": response.content if response.success else response.error,
            "coverage_target": coverage_target,
            "success": response.success,
        }
    
    def generate_integration_tests(
        self,
        api_spec: dict[str, Any],
        base_url: str = "http://localhost:8000",
    ) -> dict[str, Any]:
        """Generate integration tests for API endpoints."""
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Generate integration tests for this API:

API SPECIFICATION:
{json.dumps(api_spec, indent=2)}

BASE URL: {base_url}

Test each endpoint with:
- Success cases (2xx)
- Validation errors (400)
- Auth errors (401, 403)
- Not found (404)
- Server errors (500)

Use pytest with httpx client.
Include setup/teardown for test data.
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.3,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        return {
            "tests": response.content if response.success else response.error,
            "success": response.success,
        }
    
    def generate_e2e_tests(
        self,
        user_journey: str,
        pages: list[str],
    ) -> dict[str, Any]:
        """Generate E2E tests for user journeys."""
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Generate E2E tests for this user journey:

JOURNEY: {user_journey}
PAGES: {', '.join(pages)}

Use Playwright with TypeScript.
Include:
- Page object models
- Test steps with assertions
- Visual regression checks
- Accessibility checks
- Mobile viewport tests
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.3,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        return {
            "tests": response.content if response.success else response.error,
            "journey": user_journey,
            "success": response.success,
        }
    
    def execute(self, task: dict[str, Any]) -> AgentResponse:
        """Execute a testing task."""
        operation = task.get("operation", "unit")
        
        if operation == "unit":
            result = self.generate_unit_tests(
                task.get("code", ""),
                task.get("language", "python"),
                task.get("coverage_target", 0.8),
            )
        elif operation == "integration":
            result = self.generate_integration_tests(
                task.get("api_spec", {}),
                task.get("base_url", "http://localhost:8000"),
            )
        elif operation == "e2e":
            result = self.generate_e2e_tests(
                task.get("user_journey", ""),
                task.get("pages", []),
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


class SecurityAuditorAgent(BaseAgent):
    """Security Auditor Agent for vulnerability assessment."""
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(
            name=name or "SecurityAuditor",
            project_id=project_id,
            session_id=session_id,
        )
    
    @property
    def role(self) -> AgentRole:
        return AgentRole.SECURITY_AUDITOR
    
    @property
    def system_prompt(self) -> str:
        return SECURITY_AUDITOR_SYSTEM_PROMPT
    
    def audit_code(
        self,
        code: str,
        language: str = "python",
        context: Optional[str] = None,
    ) -> dict[str, Any]:
        """Audit code for security vulnerabilities."""
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Perform security audit on this {language} code:

```{language}
{code}
```

CONTEXT: {context or "General application code"}

Check for:
1. OWASP Top 10 vulnerabilities
2. Secrets/credentials in code
3. Input validation issues
4. SQL/NoSQL injection
5. XSS vulnerabilities
6. CSRF vulnerabilities
7. Authentication issues
8. Authorization bypass

For each finding, provide:
- Severity (Critical/High/Medium/Low)
- CWE ID
- Description
- Location
- Remediation
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.2,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        return {
            "audit": response.content if response.success else response.error,
            "success": response.success,
        }
    
    def check_dependencies(
        self,
        requirements: str,
        package_manager: str = "pip",
    ) -> dict[str, Any]:
        """Check dependencies for known vulnerabilities."""
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Analyze these dependencies for security vulnerabilities:

PACKAGE MANAGER: {package_manager}

DEPENDENCIES:
{requirements}

Check each package for:
1. Known CVEs
2. Outdated versions
3. Unmaintained packages
4. License issues
5. Supply chain risks

Provide:
- Risk level for each package
- CVE details if any
- Recommended version updates
- Alternative packages if needed
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.2,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        return {
            "analysis": response.content if response.success else response.error,
            "success": response.success,
        }
    
    def execute(self, task: dict[str, Any]) -> AgentResponse:
        """Execute a security task."""
        operation = task.get("operation", "audit")
        
        if operation == "audit":
            result = self.audit_code(
                task.get("code", ""),
                task.get("language", "python"),
                task.get("context"),
            )
        elif operation == "dependencies":
            result = self.check_dependencies(
                task.get("requirements", ""),
                task.get("package_manager", "pip"),
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


class CodeReviewerAgent(BaseAgent):
    """Code Reviewer Agent for quality and best practices."""
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(
            name=name or "CodeReviewer",
            project_id=project_id,
            session_id=session_id,
        )
    
    @property
    def role(self) -> AgentRole:
        return AgentRole.CODE_REVIEWER
    
    @property
    def system_prompt(self) -> str:
        return CODE_REVIEWER_SYSTEM_PROMPT
    
    def review_code(
        self,
        code: str,
        language: str = "python",
        context: Optional[str] = None,
    ) -> dict[str, Any]:
        """Review code for quality and best practices."""
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Review this {language} code:

```{language}
{code}
```

CONTEXT: {context or "Application code"}

Evaluate:
1. SOLID principles compliance
2. Code complexity (cyclomatic)
3. Naming conventions
4. Error handling
5. Documentation
6. Test coverage
7. Performance concerns
8. Maintainability

For each issue:
- Severity (Critical/Major/Minor/Info)
- Location
- Description
- Suggested fix
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.3,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        return {
            "review": response.content if response.success else response.error,
            "success": response.success,
        }
    
    def review_pr(
        self,
        diff: str,
        description: str,
    ) -> dict[str, Any]:
        """Review a pull request."""
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Review this pull request:

DESCRIPTION: {description}

DIFF:
{diff}

Provide:
1. Overall assessment (Approve/Request Changes/Comment)
2. Specific line comments
3. Suggestions for improvement
4. Questions for the author
5. Test coverage concerns
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.3,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        return {
            "review": response.content if response.success else response.error,
            "success": response.success,
        }
    
    def execute(self, task: dict[str, Any]) -> AgentResponse:
        """Execute a review task."""
        operation = task.get("operation", "code")
        
        if operation == "code":
            result = self.review_code(
                task.get("code", ""),
                task.get("language", "python"),
                task.get("context"),
            )
        elif operation == "pr":
            result = self.review_pr(
                task.get("diff", ""),
                task.get("description", ""),
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
