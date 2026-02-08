"""
Product Analyst Agent for AURORA-DEV.

The Product Analyst Agent is responsible for:
- Requirements analysis and refinement
- User story generation
- Acceptance criteria definition
- Feature prioritization
- Product specification documentation
- Stakeholder communication
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


PRODUCT_ANALYST_SYSTEM_PROMPT = """You are the Product Analyst Agent of AURORA-DEV.

Your responsibilities:
1. **Requirements Analysis**: Transform vague requirements into clear specifications
2. **User Stories**: Generate well-structured user stories with acceptance criteria
3. **Feature Prioritization**: Apply MoSCoW or weighted scoring methods
4. **Documentation**: Create detailed product specification documents
5. **Gap Analysis**: Identify missing requirements and edge cases

User Story Format:
- As a [persona]
- I want [feature]
- So that [benefit]

Acceptance Criteria Format (Gherkin):
- Given [context]
- When [action]
- Then [expected result]

Always consider:
- Edge cases and error scenarios
- Non-functional requirements (performance, security, accessibility)
- Dependencies between features
- MVP vs full-feature scope
"""


class ProductAnalystAgent(BaseAgent):
    """
    Product Analyst Agent for requirements and specifications.
    
    Generates:
    - User stories with acceptance criteria
    - Product specifications
    - Feature prioritization matrices
    - Requirements gap analysis
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        """Initialize the Product Analyst Agent."""
        super().__init__(
            name=name or "ProductAnalyst",
            project_id=project_id,
            session_id=session_id,
        )
        
        self._user_stories: list[dict[str, Any]] = []
        self._requirements: list[dict[str, Any]] = []
        
        self._logger.info("Product Analyst Agent initialized")
    
    @property
    def role(self) -> AgentRole:
        """Return the agent's role."""
        return AgentRole.PRODUCT_ANALYST
    
    @property
    def system_prompt(self) -> str:
        """Return the system prompt."""
        return PRODUCT_ANALYST_SYSTEM_PROMPT
    
    def analyze_requirements(
        self,
        raw_requirements: str,
        context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Analyze and structure raw requirements.
        
        Args:
            raw_requirements: Unstructured requirements text.
            context: Additional context.
            
        Returns:
            Structured requirements.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Analyze and structure the following requirements:

RAW REQUIREMENTS:
{raw_requirements}

CONTEXT:
{json.dumps(context or {}, indent=2)}

Provide structured analysis in this JSON format:
{{
    "functional_requirements": [
        {{
            "id": "FR001",
            "title": "Requirement title",
            "description": "Detailed description",
            "priority": "must_have|should_have|could_have|wont_have",
            "complexity": "low|medium|high",
            "dependencies": ["FR002"],
            "acceptance_criteria": ["criterion1", "criterion2"]
        }}
    ],
    "non_functional_requirements": [
        {{
            "id": "NFR001",
            "category": "performance|security|usability|reliability|scalability",
            "description": "Description",
            "metric": "Measurable target"
        }}
    ],
    "assumptions": ["assumption1", "assumption2"],
    "constraints": ["constraint1", "constraint2"],
    "out_of_scope": ["item1", "item2"],
    "questions_for_clarification": ["question1", "question2"],
    "risks": [
        {{"risk": "description", "mitigation": "strategy"}}
    ]
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
                analysis = json.loads(response.content[start:end])
                self._requirements.extend(analysis.get("functional_requirements", []))
                return analysis
        except json.JSONDecodeError:
            pass
        
        return {"raw_response": response.content}
    
    def generate_user_stories(
        self,
        feature: str,
        personas: Optional[list[str]] = None,
    ) -> list[dict[str, Any]]:
        """
        Generate user stories for a feature.
        
        Args:
            feature: Feature description.
            personas: User personas.
            
        Returns:
            List of user stories.
        """
        self._set_status(AgentStatus.WORKING)
        
        default_personas = ["end_user", "admin", "system"]
        
        prompt = f"""Generate user stories for:

FEATURE: {feature}
PERSONAS: {', '.join(personas or default_personas)}

Provide user stories in this JSON format:
{{
    "stories": [
        {{
            "id": "US001",
            "persona": "persona_name",
            "title": "Short title",
            "story": "As a [persona], I want [feature] so that [benefit]",
            "acceptance_criteria": [
                {{
                    "given": "context",
                    "when": "action",
                    "then": "expected result"
                }}
            ],
            "priority": "must_have|should_have|could_have",
            "story_points": 3,
            "dependencies": [],
            "notes": "Additional notes"
        }}
    ],
    "epic": {{
        "title": "Epic title",
        "description": "Epic description",
        "stories": ["US001", "US002"]
    }}
}}
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=3072,
            temperature=0.4,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        if not response.success:
            return [{"error": response.error}]
        
        try:
            start = response.content.find("{")
            end = response.content.rfind("}") + 1
            if start >= 0 and end > start:
                result = json.loads(response.content[start:end])
                stories = result.get("stories", [])
                self._user_stories.extend(stories)
                return stories
        except json.JSONDecodeError:
            pass
        
        return [{"raw_response": response.content}]
    
    def prioritize_features(
        self,
        features: list[str],
        method: str = "moscow",
    ) -> dict[str, Any]:
        """
        Prioritize features using specified method.
        
        Args:
            features: Features to prioritize.
            method: Prioritization method (moscow, weighted, kano).
            
        Returns:
            Prioritization results.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Prioritize these features using {method.upper()} method:

FEATURES:
{chr(10).join(f'- {f}' for f in features)}

Provide prioritization in this JSON format:
{{
    "method": "{method}",
    "prioritization": {{
        "must_have": ["feature1"],
        "should_have": ["feature2"],
        "could_have": ["feature3"],
        "wont_have": ["feature4"]
    }},
    "scoring": [
        {{
            "feature": "feature_name",
            "business_value": 8,
            "complexity": 5,
            "risk": 3,
            "weighted_score": 7.2,
            "rationale": "reasoning"
        }}
    ],
    "recommended_mvp": ["feature1", "feature2"],
    "phase_recommendations": [
        {{"phase": 1, "features": ["f1", "f2"]}},
        {{"phase": 2, "features": ["f3", "f4"]}}
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
    
    def create_specification(
        self,
        product_name: str,
        features: list[str],
        context: Optional[dict[str, Any]] = None,
    ) -> str:
        """
        Create a product specification document.
        
        Args:
            product_name: Product name.
            features: Core features.
            context: Additional context.
            
        Returns:
            Specification document in markdown.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Create a product specification document for:

PRODUCT: {product_name}
FEATURES: {', '.join(features)}
CONTEXT: {json.dumps(context or {}, indent=2)}

Generate a comprehensive specification document in markdown format including:
1. Executive Summary
2. Product Overview
3. Target Users & Personas
4. Feature Specifications (detailed)
5. Non-Functional Requirements
6. User Flows
7. Data Requirements
8. Integration Points
9. Success Metrics
10. Timeline Recommendations
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.4,
        )
        
        self._set_status(AgentStatus.IDLE)
        
        return response.content if response.success else f"Error: {response.error}"
    
    def execute(self, task: dict[str, Any]) -> AgentResponse:
        """Execute a product analysis task."""
        self._set_status(AgentStatus.WORKING)
        
        operation = task.get("operation", "analyze")
        
        if operation == "analyze":
            result = self.analyze_requirements(
                task.get("requirements", ""),
                task.get("context"),
            )
            content = json.dumps(result, indent=2) if isinstance(result, dict) else result
        elif operation == "user_stories":
            result = self.generate_user_stories(
                task.get("feature", ""),
                task.get("personas"),
            )
            content = json.dumps(result, indent=2)
        elif operation == "prioritize":
            result = self.prioritize_features(
                task.get("features", []),
                task.get("method", "moscow"),
            )
            content = json.dumps(result, indent=2) if isinstance(result, dict) else result
        elif operation == "specification":
            content = self.create_specification(
                task.get("product_name", "Product"),
                task.get("features", []),
                task.get("context"),
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
