"""
Validator Agent for AURORA-DEV.

The Validator Agent is responsible for:
- Code validation and verification
- Schema validation
- Configuration validation
- Contract testing
- Data integrity checks
- Compliance verification
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


VALIDATOR_SYSTEM_PROMPT = """You are the Validator Agent of AURORA-DEV.

Your responsibilities:
1. **Code Validation**: Verify code meets quality standards
2. **Schema Validation**: Validate data structures against schemas
3. **Configuration Validation**: Check configuration files for errors
4. **Contract Testing**: Verify API contracts and interfaces
5. **Compliance**: Check regulatory and security compliance

Validation Principles:
- Fail fast with clear error messages
- Provide actionable remediation steps
- Validate both structure and semantics
- Consider edge cases and boundary conditions
- Report all issues, not just the first one

Always output validation results in structured JSON format.
Include severity levels (error, warning, info) for each issue.
"""


class ValidatorAgent(BaseAgent):
    """
    Validator Agent for code and data validation.
    
    Performs:
    - Code quality validation
    - Schema validation
    - Configuration checks
    - Contract verification
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        """Initialize the Validator Agent."""
        super().__init__(
            name=name or "Validator",
            project_id=project_id,
            session_id=session_id,
        )
        
        self._validation_results: list[dict[str, Any]] = []
        
        self._logger.info("Validator Agent initialized")
    
    @property
    def role(self) -> AgentRole:
        """Return the agent's role."""
        return AgentRole.VALIDATOR
    
    @property
    def system_prompt(self) -> str:
        """Return the system prompt."""
        return VALIDATOR_SYSTEM_PROMPT
    
    def validate_code(
        self,
        code: str,
        language: str,
        rules: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Validate code against quality rules.
        
        Args:
            code: Code to validate.
            language: Programming language.
            rules: Specific rules to check.
            
        Returns:
            Validation results.
        """
        self._set_status(AgentStatus.WORKING)
        
        default_rules = [
            "no_hardcoded_secrets",
            "proper_error_handling",
            "input_validation",
            "sql_injection_prevention",
            "xss_prevention",
            "proper_logging",
            "type_safety",
            "code_complexity",
        ]
        
        prompt = f"""Validate the following {language} code:

CODE:
```{language}
{code}
```

RULES TO CHECK:
{json.dumps(rules or default_rules, indent=2)}

Provide validation results in this JSON format:
{{
    "valid": true|false,
    "issues": [
        {{
            "severity": "error|warning|info",
            "rule": "rule_name",
            "line": 10,
            "column": 5,
            "message": "Issue description",
            "suggestion": "How to fix",
            "code_snippet": "affected code"
        }}
    ],
    "summary": {{
        "errors": 0,
        "warnings": 0,
        "info": 0
    }},
    "recommendations": ["recommendation1", "recommendation2"],
    "quality_score": 85
}}
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=3072,
            temperature=0.2,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        if not response.success:
            return {"error": response.error}
        
        try:
            start = response.content.find("{")
            end = response.content.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(response.content[start:end])
                self._validation_results.append(result)
                return result
        except json.JSONDecodeError:
            pass
        
        return {"raw_response": response.content}
    
    def validate_schema(
        self,
        data: dict[str, Any],
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Validate data against a schema.
        
        Args:
            data: Data to validate.
            schema: JSON Schema or similar.
            
        Returns:
            Validation results.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Validate this data against the schema:

DATA:
{json.dumps(data, indent=2)}

SCHEMA:
{json.dumps(schema, indent=2)}

Provide validation results in this JSON format:
{{
    "valid": true|false,
    "errors": [
        {{
            "path": "$.field.subfield",
            "expected": "expected type or value",
            "actual": "actual type or value",
            "message": "Error description"
        }}
    ],
    "warnings": [
        {{
            "path": "$.field",
            "message": "Warning description"
        }}
    ],
    "missing_required_fields": ["field1", "field2"],
    "extra_fields": ["field3"],
    "type_mismatches": [
        {{"path": "$.field", "expected": "string", "actual": "number"}}
    ]
}}
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2048,
            temperature=0.1,
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
    
    def validate_configuration(
        self,
        config: dict[str, Any],
        config_type: str = "application",
    ) -> dict[str, Any]:
        """
        Validate configuration file.
        
        Args:
            config: Configuration to validate.
            config_type: Type of configuration.
            
        Returns:
            Validation results.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Validate this {config_type} configuration:

CONFIGURATION:
{json.dumps(config, indent=2)}

Check for:
- Missing required fields
- Invalid values
- Security issues (hardcoded secrets, weak configs)
- Performance issues (suboptimal settings)
- Deprecated options
- Conflicting settings

Provide validation results in this JSON format:
{{
    "valid": true|false,
    "issues": [
        {{
            "severity": "error|warning|info",
            "field": "field.path",
            "issue": "Issue description",
            "current_value": "value",
            "recommended_value": "better_value"
        }}
    ],
    "security_issues": [
        {{"field": "field", "issue": "description", "risk_level": "high|medium|low"}}
    ],
    "deprecated_settings": ["setting1"],
    "recommendations": ["recommendation1"]
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
    
    def validate_api_contract(
        self,
        spec: dict[str, Any],
        implementation: str,
    ) -> dict[str, Any]:
        """
        Validate API implementation against spec.
        
        Args:
            spec: API specification (OpenAPI).
            implementation: Implementation code.
            
        Returns:
            Contract validation results.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Validate API implementation against specification:

SPECIFICATION:
{json.dumps(spec, indent=2)}

IMPLEMENTATION:
{implementation}

Check for:
- Missing endpoints
- Wrong HTTP methods
- Response schema mismatches
- Missing error handlers
- Missing authentication

Provide validation results in this JSON format:
{{
    "compliant": true|false,
    "endpoint_coverage": {{
        "total": 10,
        "implemented": 8,
        "missing": ["GET /api/missing"]
    }},
    "issues": [
        {{
            "endpoint": "GET /api/resource",
            "issue_type": "missing|schema_mismatch|wrong_method",
            "description": "Issue description",
            "severity": "error|warning"
        }}
    ],
    "schema_issues": [
        {{
            "endpoint": "GET /api/resource",
            "field": "response.field",
            "expected": "string",
            "actual": "number"
        }}
    ],
    "recommendations": ["recommendation1"]
}}
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=3072,
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
    
    def execute(self, task: dict[str, Any]) -> AgentResponse:
        """Execute a validation task."""
        self._set_status(AgentStatus.WORKING)
        
        operation = task.get("operation", "code")
        
        if operation == "code":
            result = self.validate_code(
                task.get("code", ""),
                task.get("language", "python"),
                task.get("rules"),
            )
        elif operation == "schema":
            result = self.validate_schema(
                task.get("data", {}),
                task.get("schema", {}),
            )
        elif operation == "configuration":
            result = self.validate_configuration(
                task.get("config", {}),
                task.get("config_type", "application"),
            )
        elif operation == "contract":
            result = self.validate_api_contract(
                task.get("spec", {}),
                task.get("implementation", ""),
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
