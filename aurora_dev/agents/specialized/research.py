"""
Research Agent for AURORA-DEV.

The Research Agent is responsible for:
- Technology research and evaluation
- Best practices discovery
- Security vulnerability scanning
- Documentation gathering
- Competitive analysis
- API/library compatibility checking
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


RESEARCH_SYSTEM_PROMPT = """You are the Research Agent of AURORA-DEV.

Your responsibilities:
1. **Technology Research**: Evaluate technologies, frameworks, and libraries
2. **Best Practices**: Discover and document industry best practices
3. **Security Research**: Identify vulnerabilities and security patterns
4. **Documentation**: Gather and synthesize technical documentation
5. **Competitive Analysis**: Analyze similar solutions and their approaches

Research Framework:
- Always cite sources when available
- Provide quantitative data when possible
- List pros and cons for each technology
- Consider team expertise and learning curve
- Evaluate community support and maintenance status

Output all findings in structured JSON format with clear hierarchies.
Always include confidence scores (0-100) for recommendations.
"""


class ResearchAgent(BaseAgent):
    """
    Research Agent for technology evaluation and best practices.
    
    Performs:
    - Technology stack research
    - Security vulnerability analysis
    - Best practices documentation
    - Competitive analysis
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        """Initialize the Research Agent."""
        super().__init__(
            name=name or "Research",
            project_id=project_id,
            session_id=session_id,
        )
        
        self._research_cache: dict[str, dict[str, Any]] = {}
        self._findings: list[dict[str, Any]] = []
        
        # Initialize external research tool clients
        try:
            from aurora_dev.tools.research_tools import (
                GitHubSearchClient,
                PackageRegistryClient,
                WebSearchClient,
            )
            self._github_client = GitHubSearchClient()
            self._package_client = PackageRegistryClient()
            self._web_client = WebSearchClient()
            self._logger.info("External research tools initialized")
        except Exception as e:
            self._github_client = None
            self._package_client = None
            self._web_client = None
            self._logger.warning(f"Research tools unavailable: {e}")
        
        self._logger.info("Research Agent initialized")
    
    @property
    def role(self) -> AgentRole:
        """Return the agent's role."""
        return AgentRole.RESEARCH
    
    @property
    def system_prompt(self) -> str:
        """Return the system prompt."""
        return RESEARCH_SYSTEM_PROMPT
    
    def research_technology(
        self,
        technology: str,
        use_case: str,
        requirements: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Research a specific technology.
        
        Args:
            technology: Technology to research.
            use_case: Intended use case.
            requirements: Specific requirements.
            
        Returns:
            Research findings.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Research the following technology:

TECHNOLOGY: {technology}
USE CASE: {use_case}
REQUIREMENTS: {json.dumps(requirements or [], indent=2)}

Provide your findings in this JSON format:
{{
    "technology": "{technology}",
    "summary": "Brief overview",
    "pros": ["advantage1", "advantage2"],
    "cons": ["disadvantage1", "disadvantage2"],
    "use_cases": ["use_case1", "use_case2"],
    "alternatives": [
        {{"name": "alt_name", "comparison": "how it compares"}}
    ],
    "maturity": "early|growing|mature|declining",
    "community_size": "small|medium|large",
    "learning_curve": "easy|moderate|steep",
    "documentation_quality": "poor|fair|good|excellent",
    "maintenance_status": "active|slow|unmaintained",
    "confidence_score": 85,
    "recommendation": "recommended|conditional|not_recommended",
    "recommendation_rationale": "Why this recommendation"
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
                finding = json.loads(response.content[start:end])
                self._findings.append(finding)
                self._research_cache[technology] = finding
                return finding
        except json.JSONDecodeError:
            pass
        
        return {"raw_response": response.content}
    
    def analyze_security(
        self,
        technology: str,
        version: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Analyze security aspects of a technology.
        
        Args:
            technology: Technology to analyze.
            version: Specific version.
            
        Returns:
            Security analysis.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Analyze security aspects of:

TECHNOLOGY: {technology}
VERSION: {version or "latest"}

Provide security analysis in this JSON format:
{{
    "technology": "{technology}",
    "version": "{version or 'latest'}",
    "known_vulnerabilities": [
        {{"cve": "CVE-XXXX-XXXX", "severity": "critical|high|medium|low", "description": "desc"}}
    ],
    "security_best_practices": [
        "practice1",
        "practice2"
    ],
    "common_misconfigurations": [
        {{"issue": "desc", "mitigation": "how to fix"}}
    ],
    "security_score": 75,
    "recommendations": ["action1", "action2"]
}}
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
            temperature=0.2,
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
    
    def discover_best_practices(
        self,
        domain: str,
        context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Discover best practices for a domain.
        
        Args:
            domain: Domain area (e.g., "REST API design").
            context: Additional context.
            
        Returns:
            Best practices.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Discover best practices for:

DOMAIN: {domain}
CONTEXT: {json.dumps(context or {}, indent=2)}

Provide best practices in this JSON format:
{{
    "domain": "{domain}",
    "best_practices": [
        {{
            "title": "Practice title",
            "description": "Detailed description",
            "rationale": "Why this is important",
            "examples": ["example1", "example2"],
            "anti_patterns": ["what to avoid"]
        }}
    ],
    "references": ["ref1", "ref2"],
    "implementation_priority": [
        {{"practice": "practice_title", "priority": "high|medium|low"}}
    ]
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
    
    def compare_technologies(
        self,
        technologies: list[str],
        criteria: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Compare multiple technologies.
        
        Args:
            technologies: Technologies to compare.
            criteria: Comparison criteria.
            
        Returns:
            Comparison results.
        """
        self._set_status(AgentStatus.WORKING)
        
        default_criteria = [
            "performance",
            "ease_of_use",
            "community_support",
            "documentation",
            "scalability",
            "cost",
        ]
        
        prompt = f"""Compare these technologies:

TECHNOLOGIES: {', '.join(technologies)}
CRITERIA: {', '.join(criteria or default_criteria)}

Provide comparison in this JSON format:
{{
    "comparison": {{
        "criteria_name": {{
            "tech1": {{"score": 8, "notes": "explanation"}},
            "tech2": {{"score": 7, "notes": "explanation"}}
        }}
    }},
    "overall_scores": {{
        "tech1": 7.5,
        "tech2": 8.2
    }},
    "winner": "tech_name",
    "recommendation": "Detailed recommendation",
    "use_case_fit": {{
        "tech1": ["best for X", "good for Y"],
        "tech2": ["best for A", "good for B"]
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
                return json.loads(response.content[start:end])
        except json.JSONDecodeError:
            pass
        
        return {"raw_response": response.content}
    
    def execute(self, task: dict[str, Any]) -> AgentResponse:
        """Execute a research task."""
        self._set_status(AgentStatus.WORKING)
        
        operation = task.get("operation", "research")
        
        if operation == "research":
            result = self.research_technology(
                task.get("technology", ""),
                task.get("use_case", ""),
                task.get("requirements"),
            )
        elif operation == "security":
            result = self.analyze_security(
                task.get("technology", ""),
                task.get("version"),
            )
        elif operation == "best_practices":
            result = self.discover_best_practices(
                task.get("domain", ""),
                task.get("context"),
            )
        elif operation == "compare":
            result = self.compare_technologies(
                task.get("technologies", []),
                task.get("criteria"),
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
