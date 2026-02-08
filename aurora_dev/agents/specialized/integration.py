"""
Integration Agent for AURORA-DEV.

The Integration Agent is responsible for:
- Third-party API integration
- Service orchestration
- Data transformation and mapping
- Webhook management
- Event-driven architecture implementation
- Integration testing coordination
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


INTEGRATION_SYSTEM_PROMPT = """You are the Integration Agent of AURORA-DEV.

Your responsibilities:
1. **API Integration**: Design and implement third-party API integrations
2. **Data Mapping**: Transform data between different systems and formats
3. **Webhook Management**: Configure and handle webhook endpoints
4. **Event Architecture**: Design event-driven communication patterns
5. **Error Handling**: Implement robust error handling and retry logic

Integration Patterns:
- Point-to-point: Direct API calls
- Pub/Sub: Event-driven messaging
- Request/Reply: Synchronous patterns
- Saga: Distributed transaction management

Always consider:
- Rate limiting and throttling
- Authentication and authorization
- Data validation and sanitization
- Idempotency for retries
- Circuit breaker patterns
- Logging and monitoring
"""


class IntegrationAgent(BaseAgent):
    """
    Integration Agent for third-party integrations.
    
    Handles:
    - API integration code generation
    - Data transformation mappings
    - Webhook endpoint design
    - Integration testing strategies
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        """Initialize the Integration Agent."""
        super().__init__(
            name=name or "Integration",
            project_id=project_id,
            session_id=session_id,
        )
        
        self._integrations: dict[str, dict[str, Any]] = {}
        self._mappings: dict[str, dict[str, str]] = {}
        
        self._logger.info("Integration Agent initialized")
    
    @property
    def role(self) -> AgentRole:
        """Return the agent's role."""
        return AgentRole.INTEGRATION
    
    @property
    def system_prompt(self) -> str:
        """Return the system prompt."""
        return INTEGRATION_SYSTEM_PROMPT
    
    def design_integration(
        self,
        service_name: str,
        api_docs: str,
        requirements: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """
        Design an integration with a third-party service.
        
        Args:
            service_name: Name of the service.
            api_docs: API documentation or overview.
            requirements: Integration requirements.
            
        Returns:
            Integration design.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Design an integration with:

SERVICE: {service_name}
API DOCUMENTATION:
{api_docs}

REQUIREMENTS:
{json.dumps(requirements or [], indent=2)}

Provide integration design in this JSON format:
{{
    "service": "{service_name}",
    "integration_type": "rest|graphql|websocket|grpc",
    "authentication": {{
        "type": "api_key|oauth2|basic|jwt",
        "configuration": {{}},
        "token_refresh": "auto|manual|none"
    }},
    "endpoints": [
        {{
            "name": "endpoint_name",
            "method": "GET|POST|PUT|DELETE",
            "path": "/api/resource",
            "purpose": "what it does",
            "request_schema": {{}},
            "response_schema": {{}},
            "rate_limit": "100/minute"
        }}
    ],
    "error_handling": {{
        "retry_strategy": "exponential_backoff|linear|none",
        "max_retries": 3,
        "circuit_breaker": {{
            "threshold": 5,
            "timeout_seconds": 30
        }},
        "fallback": "cache|default_value|error"
    }},
    "data_mapping": {{
        "external_field": "internal_field"
    }},
    "webhooks": [
        {{
            "event": "event_name",
            "endpoint": "/webhooks/service",
            "signature_verification": true
        }}
    ],
    "testing_strategy": {{
        "unit_tests": ["test descriptions"],
        "integration_tests": ["test descriptions"],
        "mock_strategy": "record_playback|fixtures"
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
        
        try:
            start = response.content.find("{")
            end = response.content.rfind("}") + 1
            if start >= 0 and end > start:
                design = json.loads(response.content[start:end])
                self._integrations[service_name] = design
                return design
        except json.JSONDecodeError:
            pass
        
        return {"raw_response": response.content}
    
    def generate_client_code(
        self,
        service_name: str,
        language: str = "python",
        framework: Optional[str] = None,
    ) -> str:
        """
        Generate integration client code.
        
        Args:
            service_name: Service to integrate.
            language: Programming language.
            framework: Optional framework.
            
        Returns:
            Generated client code.
        """
        self._set_status(AgentStatus.WORKING)
        
        integration = self._integrations.get(service_name, {})
        
        prompt = f"""Generate integration client code for:

SERVICE: {service_name}
LANGUAGE: {language}
FRAMEWORK: {framework or "none"}
INTEGRATION DETAILS:
{json.dumps(integration, indent=2) if integration else "No cached details - generate a basic client"}

Generate production-ready client code with:
- Type hints (if applicable)
- Error handling with custom exceptions
- Rate limiting awareness
- Retry logic with exponential backoff
- Logging
- Configuration from environment variables
- Connection pooling (if applicable)
- Async support (if applicable)

Include docstrings and usage examples.
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.3,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        return response.content if response.success else f"Error: {response.error}"
    
    def create_data_mapping(
        self,
        source_schema: dict[str, Any],
        target_schema: dict[str, Any],
        context: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Create data mapping between schemas.
        
        Args:
            source_schema: Source data schema.
            target_schema: Target data schema.
            context: Additional context.
            
        Returns:
            Data mapping configuration.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Create a data mapping between:

SOURCE SCHEMA:
{json.dumps(source_schema, indent=2)}

TARGET SCHEMA:
{json.dumps(target_schema, indent=2)}

CONTEXT: {context or "General data transformation"}

Provide mapping in this JSON format:
{{
    "mappings": [
        {{
            "source": "source.field.path",
            "target": "target.field.path",
            "transform": "none|string_to_date|date_to_string|uppercase|lowercase|custom",
            "custom_transform": "transformation expression if custom",
            "default_value": null,
            "required": true
        }}
    ],
    "unmapped_source_fields": ["field1", "field2"],
    "required_target_fields_missing": ["field1"],
    "validation_rules": [
        {{"field": "target_field", "rule": "validation expression"}}
    ],
    "transformation_code": "// Code snippet for complex transformations"
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
    
    def design_webhook_handler(
        self,
        events: list[str],
        service: str,
    ) -> dict[str, Any]:
        """
        Design webhook handler implementation.
        
        Args:
            events: Events to handle.
            service: Service name.
            
        Returns:
            Webhook handler design.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Design webhook handlers for:

SERVICE: {service}
EVENTS: {', '.join(events)}

Provide webhook design in this JSON format:
{{
    "endpoint": "/webhooks/{service.lower()}",
    "handlers": [
        {{
            "event": "event_name",
            "handler_function": "handle_event_name",
            "processing": "sync|async",
            "idempotency_key": "field to use for idempotency",
            "actions": ["action1", "action2"],
            "error_handling": "retry|dlq|ignore"
        }}
    ],
    "security": {{
        "signature_header": "X-Signature-256",
        "signature_algorithm": "HMAC-SHA256",
        "replay_prevention": true,
        "timestamp_tolerance_seconds": 300
    }},
    "infrastructure": {{
        "queue": "webhook_queue_name",
        "dead_letter_queue": "webhook_dlq",
        "retention_days": 7
    }},
    "monitoring": {{
        "metrics": ["webhook_received", "webhook_processed", "webhook_failed"],
        "alerts": ["high_failure_rate", "processing_delay"]
    }}
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
    
    def execute(self, task: dict[str, Any]) -> AgentResponse:
        """Execute an integration task."""
        self._set_status(AgentStatus.WORKING)
        
        operation = task.get("operation", "design")
        
        if operation == "design":
            result = self.design_integration(
                task.get("service_name", ""),
                task.get("api_docs", ""),
                task.get("requirements"),
            )
            content = json.dumps(result, indent=2) if isinstance(result, dict) else result
        elif operation == "generate_client":
            content = self.generate_client_code(
                task.get("service_name", ""),
                task.get("language", "python"),
                task.get("framework"),
            )
        elif operation == "mapping":
            result = self.create_data_mapping(
                task.get("source_schema", {}),
                task.get("target_schema", {}),
                task.get("context"),
            )
            content = json.dumps(result, indent=2) if isinstance(result, dict) else result
        elif operation == "webhook":
            result = self.design_webhook_handler(
                task.get("events", []),
                task.get("service", ""),
            )
            content = json.dumps(result, indent=2) if isinstance(result, dict) else result
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
