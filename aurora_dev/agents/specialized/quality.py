import json
import asyncio
import subprocess
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from aurora_dev.agents.base_agent import (
    AgentResponse,
    AgentRole,
    AgentStatus,
    BaseAgent,
)


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# DAST Scanner (Gap B1)
# ---------------------------------------------------------------------------

@dataclass
class DASTFinding:
    """A finding from dynamic security testing."""
    
    alert: str
    risk: str  # High, Medium, Low, Informational
    confidence: str  # High, Medium, Low
    url: str = ""
    description: str = ""
    solution: str = ""
    cwe_id: int = 0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "alert": self.alert,
            "risk": self.risk,
            "confidence": self.confidence,
            "url": self.url,
            "description": self.description,
            "solution": self.solution,
            "cwe_id": self.cwe_id,
        }


class DynamicSecurityScanner:
    """DAST scanner using OWASP ZAP for runtime vulnerability detection.
    
    Runs ZAP in Docker to perform active and passive scanning
    against a target URL, then parses the results.
    
    Example:
        >>> scanner = DynamicSecurityScanner()
        >>> findings = await scanner.run_baseline_scan("http://localhost:8000")
    """
    
    ZAP_DOCKER_IMAGE = "ghcr.io/zaproxy/zaproxy:stable"
    
    def __init__(self, zap_api_key: Optional[str] = None) -> None:
        self._api_key = zap_api_key or "aurora-dev-zap-key"
    
    async def run_baseline_scan(
        self,
        target_url: str,
        timeout_minutes: int = 10,
    ) -> list[DASTFinding]:
        """Run ZAP baseline scan against a target.
        
        Args:
            target_url: URL to scan.
            timeout_minutes: Max scan duration.
            
        Returns:
            List of security findings.
        """
        findings: list[DASTFinding] = []
        
        try:
            cmd = [
                "docker", "run", "--rm",
                "-t", self.ZAP_DOCKER_IMAGE,
                "zap-baseline.py",
                "-t", target_url,
                "-J", "/dev/stdout",  # JSON output to stdout
                "-I",  # Don't return error on findings
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout_minutes * 60,
            )
            
            if stdout:
                try:
                    report = json.loads(stdout.decode())
                    for site in report.get("site", []):
                        for alert in site.get("alerts", []):
                            findings.append(DASTFinding(
                                alert=alert.get("name", "Unknown"),
                                risk=alert.get("riskdesc", "Unknown").split(" ")[0],
                                confidence=alert.get("confidence", "Low"),
                                url=target_url,
                                description=alert.get("desc", ""),
                                solution=alert.get("solution", ""),
                                cwe_id=int(alert.get("cweid", 0)),
                            ))
                except json.JSONDecodeError:
                    logger.warning("Failed to parse ZAP output as JSON")
            
        except asyncio.TimeoutError:
            logger.error(f"ZAP scan timed out after {timeout_minutes} minutes")
        except FileNotFoundError:
            logger.warning("Docker not available for DAST scanning")
        except Exception as e:
            logger.error(f"DAST scan failed: {e}")
        
        return findings
    
    async def run_api_scan(
        self,
        openapi_url: str,
        target_url: str,
    ) -> list[DASTFinding]:
        """Run ZAP API scan using OpenAPI spec.
        
        Args:
            openapi_url: URL or path to OpenAPI spec.
            target_url: Target API base URL.
            
        Returns:
            List of security findings.
        """
        findings: list[DASTFinding] = []
        
        try:
            cmd = [
                "docker", "run", "--rm",
                "-t", self.ZAP_DOCKER_IMAGE,
                "zap-api-scan.py",
                "-t", openapi_url,
                "-f", "openapi",
                "-J", "/dev/stdout",
                "-I",
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, _ = await process.communicate()
            
            if stdout:
                try:
                    report = json.loads(stdout.decode())
                    for site in report.get("site", []):
                        for alert in site.get("alerts", []):
                            findings.append(DASTFinding(
                                alert=alert.get("name", "Unknown"),
                                risk=alert.get("riskdesc", "Unknown").split(" ")[0],
                                confidence=alert.get("confidence", "Low"),
                                url=target_url,
                                description=alert.get("desc", ""),
                                solution=alert.get("solution", ""),
                                cwe_id=int(alert.get("cweid", 0)),
                            ))
                except json.JSONDecodeError:
                    pass
                    
        except Exception as e:
            logger.error(f"API scan failed: {e}")
        
        return findings


# ---------------------------------------------------------------------------
# Self-healing Test Runner (Gap B3)
# ---------------------------------------------------------------------------

@dataclass
class SelectorRepair:
    """A repaired test selector."""
    original_selector: str
    repaired_selector: str
    confidence: float
    repair_method: str  # "accessibility", "data-testid", "css-fallback"


class SelfHealingTestRunner:
    """Self-healing Playwright test runner.
    
    When tests fail due to selector changes, this runner:
    1. Parses the failure to identify the broken selector
    2. Queries the accessibility tree for alternative selectors
    3. Uses LLM to suggest repaired selectors
    4. Re-runs the test with the repaired selector
    
    Example:
        >>> runner = SelfHealingTestRunner()
        >>> result = await runner.run_with_healing("tests/e2e/login.spec.ts")
    """
    
    MAX_REPAIR_ATTEMPTS = 3
    
    def __init__(self, llm_agent: Optional[BaseAgent] = None) -> None:
        self._agent = llm_agent
        self._repair_history: list[SelectorRepair] = []
    
    async def run_with_healing(
        self,
        test_file: str,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """Run a Playwright test with self-healing selectors.
        
        Args:
            test_file: Path to the test file.
            max_retries: Max repair attempts.
            
        Returns:
            Test result with any repairs applied.
        """
        attempt = 0
        repairs: list[dict[str, Any]] = []
        
        while attempt < max_retries:
            result = await self._run_playwright(test_file)
            
            if result["exit_code"] == 0:
                return {
                    "success": True,
                    "attempts": attempt + 1,
                    "repairs": repairs,
                    "output": result["stdout"],
                }
            
            # Parse selector failure
            broken_selector = self._parse_selector_error(result["stderr"])
            if not broken_selector:
                break
            
            # Attempt repair
            repair = await self._repair_selector(
                broken_selector,
                result.get("accessibility_tree", ""),
            )
            
            if repair:
                repairs.append(repair.original_selector)
                self._repair_history.append(repair)
                await self._apply_repair(test_file, repair)
                attempt += 1
            else:
                break
        
        return {
            "success": False,
            "attempts": attempt + 1,
            "repairs": repairs,
            "error": "Could not self-heal test failures",
        }
    
    async def _run_playwright(self, test_file: str) -> dict[str, Any]:
        """Execute a Playwright test and capture output."""
        try:
            process = await asyncio.create_subprocess_exec(
                "npx", "playwright", "test", test_file,
                "--reporter=json",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            
            return {
                "exit_code": process.returncode,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
            }
        except Exception as e:
            return {"exit_code": 1, "stdout": "", "stderr": str(e)}
    
    def _parse_selector_error(self, stderr: str) -> Optional[str]:
        """Extract the broken selector from Playwright error output."""
        import re
        
        patterns = [
            r'locator\.(?:click|fill|check)\("([^"]+)"\)',
            r'page\.locator\("([^"]+)"\)',
            r'getByRole\("([^"]+)"',
            r'getByTestId\("([^"]+)"',
            r'Locator: (.+?)(?:\n|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, stderr)
            if match:
                return match.group(1)
        
        return None
    
    async def _repair_selector(
        self,
        broken_selector: str,
        accessibility_tree: str,
    ) -> Optional[SelectorRepair]:
        """Use LLM to suggest a repaired selector."""
        if not self._agent:
            return self._fallback_repair(broken_selector)
        
        prompt = f"""A Playwright test failed because this selector no longer matches:
Broken selector: {broken_selector}

Accessibility tree of the page:
{accessibility_tree[:3000]}

Suggest a repaired selector that targets the same element. Prefer:
1. getByRole with accessible name
2. data-testid attributes
3. CSS selectors as last resort

Respond with ONLY the new selector string, nothing else."""
        
        response = self._agent._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.1,
        )
        
        if response.success and response.content.strip():
            return SelectorRepair(
                original_selector=broken_selector,
                repaired_selector=response.content.strip().strip('"\''),
                confidence=0.8,
                repair_method="accessibility",
            )
        
        return None
    
    def _fallback_repair(self, broken_selector: str) -> Optional[SelectorRepair]:
        """Simple heuristic repair without LLM."""
        # Try converting class-based selector to data-testid
        if broken_selector.startswith("."):
            class_name = broken_selector.lstrip(".")
            return SelectorRepair(
                original_selector=broken_selector,
                repaired_selector=f'[data-testid="{class_name}"]',
                confidence=0.4,
                repair_method="data-testid",
            )
        return None
    
    async def _apply_repair(
        self,
        test_file: str,
        repair: SelectorRepair,
    ) -> None:
        """Apply a selector repair to the test file."""
        try:
            with open(test_file, "r") as f:
                content = f.read()
            
            content = content.replace(
                repair.original_selector,
                repair.repaired_selector,
            )
            
            with open(test_file, "w") as f:
                f.write(content)
                
            logger.info(
                f"Applied selector repair: "
                f"'{repair.original_selector}' -> '{repair.repaired_selector}'"
            )
        except Exception as e:
            logger.error(f"Failed to apply repair: {e}")
    
    def get_repair_history(self) -> list[dict[str, Any]]:
        """Get history of all selector repairs."""
        return [
            {
                "original": r.original_selector,
                "repaired": r.repaired_selector,
                "confidence": r.confidence,
                "method": r.repair_method,
            }
            for r in self._repair_history
        ]


# ---------------------------------------------------------------------------
# Agent Prompts
# ---------------------------------------------------------------------------

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
9. Dynamic Application Security Testing (DAST) via OWASP ZAP

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
        self._self_healing_runner = SelfHealingTestRunner(llm_agent=self)
    
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
    
    async def run_self_healing_tests(
        self,
        test_file: str,
        max_retries: int = 3,
    ) -> dict[str, Any]:
        """Run E2E tests with self-healing selector repair.
        
        When a Playwright test fails due to a changed selector,
        the runner will attempt to repair it using accessibility
        tree context and LLM suggestions.
        
        Args:
            test_file: Path to the Playwright test file.
            max_retries: Maximum repair attempts.
            
        Returns:
            Test result including any repairs made.
        """
        return await self._self_healing_runner.run_with_healing(
            test_file, max_retries=max_retries,
        )
    
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
        elif operation == "self_healing":
            import asyncio
            result = asyncio.get_event_loop().run_until_complete(
                self.run_self_healing_tests(
                    task.get("test_file", ""),
                    task.get("max_retries", 3),
                )
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
    """Security Auditor Agent for vulnerability assessment.
    
    Provides both static (SAST) and dynamic (DAST) security testing.
    """
    
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
        self._dast_scanner = DynamicSecurityScanner()
    
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
        """Audit code for security vulnerabilities (SAST)."""
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
    
    async def run_dast(
        self,
        target_url: str,
        scan_type: str = "baseline",
        openapi_url: Optional[str] = None,
    ) -> dict[str, Any]:
        """Run Dynamic Application Security Testing (DAST).
        
        Uses OWASP ZAP to perform runtime security testing against
        a live application endpoint.
        
        Args:
            target_url: URL of the application to scan.
            scan_type: Type of scan - "baseline" or "api".
            openapi_url: OpenAPI spec URL (required for api scan).
            
        Returns:
            DAST findings with severity and remediation guidance.
        """
        self._set_status(AgentStatus.WORKING)
        
        if scan_type == "api" and openapi_url:
            findings = await self._dast_scanner.run_api_scan(
                openapi_url=openapi_url,
                target_url=target_url,
            )
        else:
            findings = await self._dast_scanner.run_baseline_scan(target_url)
        
        self._set_status(AgentStatus.IDLE)
        
        return {
            "scan_type": scan_type,
            "target": target_url,
            "findings": [f.to_dict() for f in findings],
            "findings_count": len(findings),
            "critical_count": sum(1 for f in findings if f.risk == "High"),
            "success": True,
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
        elif operation == "dast":
            import asyncio
            result = asyncio.get_event_loop().run_until_complete(
                self.run_dast(
                    task.get("target_url", "http://localhost:8000"),
                    task.get("scan_type", "baseline"),
                    task.get("openapi_url"),
                )
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

