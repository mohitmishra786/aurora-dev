"""
Reflexion engine for AURORA-DEV self-improvement.

This module implements the Reflexion pattern (Shinn et al.) for
agents to learn from failures without model fine-tuning.

The process:
1. Capture failure context
2. Generate structured reflection
3. Store in episodic memory
4. Retry with enhanced context

Example usage:
    >>> engine = ReflexionEngine(project_id="my-project")
    >>> reflection = await engine.generate_reflection(
    ...     task=task_context,
    ...     attempt=attempt_result,
    ...     previous_reflections=[],
    ... )
"""
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import uuid4

from aurora_dev.core.logging import get_logger


logger = get_logger(__name__)


class ReflexionTrigger(Enum):
    """Triggers that initiate a reflexion loop."""
    
    TEST_FAILURE = "test_failure"
    CODE_REVIEW_REJECTION = "code_review_rejection"
    SECURITY_VULNERABILITY = "security_vulnerability"
    PERFORMANCE_TARGET_MISSED = "performance_target_missed"
    ACCEPTANCE_CRITERIA_NOT_MET = "acceptance_criteria_not_met"
    API_ERROR = "api_error"
    VALIDATION_ERROR = "validation_error"


@dataclass
class RootCause:
    """Root cause analysis from reflection."""
    
    technical: str
    reasoning: str


@dataclass
class IncorrectAssumption:
    """An incorrect assumption identified during reflection."""
    
    assumption: str
    why_wrong: str
    correct_approach: str


@dataclass
class ImprovedStrategy:
    """Improved strategy for retry attempt."""
    
    approach: str
    implementation_steps: list[str]
    validation_plan: str


@dataclass
class LessonLearned:
    """A generalizable lesson from the reflection."""
    
    lesson: str
    applicability: str
    pattern_name: str


@dataclass
class Reflection:
    """
    Structured reflection output from the reflexion engine.
    
    Contains root cause analysis, incorrect assumptions,
    improved strategy, and lessons learned.
    """
    
    reflection_id: str
    task_id: str
    agent_id: str
    attempt_number: int
    trigger: ReflexionTrigger
    timestamp: datetime
    
    root_cause: RootCause
    incorrect_assumptions: list[IncorrectAssumption]
    improved_strategy: ImprovedStrategy
    lessons_learned: list[LessonLearned]
    
    # Original context
    task_description: str
    approach_taken: str
    code_produced: Optional[str]
    test_results: Optional[str]
    errors: Optional[str]
    performance_metrics: Optional[dict]
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "reflection_id": self.reflection_id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "attempt_number": self.attempt_number,
            "trigger": self.trigger.value,
            "timestamp": self.timestamp.isoformat(),
            "root_cause": {
                "technical": self.root_cause.technical,
                "reasoning": self.root_cause.reasoning,
            },
            "incorrect_assumptions": [
                {
                    "assumption": a.assumption,
                    "why_wrong": a.why_wrong,
                    "correct_approach": a.correct_approach,
                }
                for a in self.incorrect_assumptions
            ],
            "improved_strategy": {
                "approach": self.improved_strategy.approach,
                "implementation_steps": self.improved_strategy.implementation_steps,
                "validation_plan": self.improved_strategy.validation_plan,
            },
            "lessons_learned": [
                {
                    "lesson": l.lesson,
                    "applicability": l.applicability,
                    "pattern_name": l.pattern_name,
                }
                for l in self.lessons_learned
            ],
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Reflection":
        """Create from dictionary."""
        return cls(
            reflection_id=data["reflection_id"],
            task_id=data["task_id"],
            agent_id=data["agent_id"],
            attempt_number=data["attempt_number"],
            trigger=ReflexionTrigger(data["trigger"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            root_cause=RootCause(**data["root_cause"]),
            incorrect_assumptions=[
                IncorrectAssumption(**a) for a in data["incorrect_assumptions"]
            ],
            improved_strategy=ImprovedStrategy(**data["improved_strategy"]),
            lessons_learned=[
                LessonLearned(**l) for l in data["lessons_learned"]
            ],
            task_description=data.get("task_description", ""),
            approach_taken=data.get("approach_taken", ""),
            code_produced=data.get("code_produced"),
            test_results=data.get("test_results"),
            errors=data.get("errors"),
            performance_metrics=data.get("performance_metrics"),
        )


@dataclass
class AttemptResult:
    """Result from an agent's attempt at a task."""
    
    success: bool
    output: Any
    error: Optional[str] = None
    test_results: Optional[str] = None
    performance_metrics: Optional[dict] = None
    code_produced: Optional[str] = None
    approach_taken: str = ""


@dataclass
class TaskContext:
    """Context for a task being attempted."""
    
    task_id: str
    description: str
    requirements: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)
    constraints: dict[str, Any] = field(default_factory=dict)


@dataclass
class RetryContext:
    """Enhanced context for retry attempt after reflection."""
    
    original_task: TaskContext
    previous_attempts_summary: str
    reflections: list[Reflection]
    relevant_patterns: list[dict[str, Any]]
    similar_successful_tasks: list[dict[str, Any]]
    
    def to_prompt_context(self) -> str:
        """Format as context for LLM prompt."""
        parts = [
            f"ORIGINAL TASK:\n{self.original_task.description}",
            f"\nPREVIOUS ATTEMPTS ({len(self.reflections)}):\n{self.previous_attempts_summary}",
        ]
        
        if self.reflections:
            latest = self.reflections[-1]
            parts.append(
                f"\nLATEST REFLECTION:\n"
                f"- Root cause: {latest.root_cause.technical}\n"
                f"- Strategy: {latest.improved_strategy.approach}\n"
                f"- Validation: {latest.improved_strategy.validation_plan}"
            )
        
        if self.relevant_patterns:
            patterns = [p.get("name", "unknown") for p in self.relevant_patterns]
            parts.append(f"\nRELEVANT PATTERNS: {', '.join(patterns)}")
        
        return "\n".join(parts)


# The reflection prompt from the spec (lines 3838-3884)
REFLECTION_PROMPT = """You attempted to complete this task:
{task_description}

Your approach was:
{approach_taken}

The code you wrote:
{code}

Test results:
{test_results}

Errors encountered:
{errors}

Performance metrics:
{metrics}

This was attempt #{attempt_number}.
Previous reflections:
{previous_reflections}

Provide a detailed reflection:

1. ROOT CAUSE ANALYSIS
- What exactly went wrong?
- Why did it happen?
- What was the fundamental error in reasoning?

2. INCORRECT ASSUMPTIONS
- What did you assume that was wrong?
- What did you overlook?
- What edge cases did you miss?

3. ALTERNATIVE APPROACHES
- What should you try differently?
- What patterns or techniques would work better?
- What additional validation is needed?

4. GENERALIZABLE LEARNINGS
- What lesson applies to similar tasks?
- What pattern should you remember?
- What should you check for next time?

Be specific and actionable. Focus on what to change, not just
what went wrong.

Respond in JSON format:
{{
  "root_cause": {{
    "technical": "...",
    "reasoning": "..."
  }},
  "incorrect_assumptions": [
    {{"assumption": "...", "why_wrong": "...", "correct_approach": "..."}}
  ],
  "improved_strategy": {{
    "approach": "...",
    "implementation_steps": ["step1", "step2"],
    "validation_plan": "..."
  }},
  "lessons_learned": [
    {{"lesson": "...", "applicability": "...", "pattern_name": "..."}}
  ]
}}"""



class ReflexionEngine:
    """
    Engine for generating and managing reflections.
    
    Implements the Reflexion pattern for self-improvement:
    1. Capture failure context
    2. Generate structured reflection via LLM
    3. Store in episodic memory
    4. Build enhanced retry context
    
    Attributes:
        project_id: Project identifier.
        max_attempts: Maximum retry attempts (default 5).
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        max_attempts: int = 5,
    ):
        """
        Initialize the reflexion engine.
        
        Args:
            project_id: Project identifier.
            max_attempts: Maximum retry attempts.
        """
        self.project_id = project_id
        self.max_attempts = max_attempts
        self._reflections: dict[str, list[Reflection]] = {}
        self._pattern_library: list[dict[str, Any]] = []
        self._logger = get_logger(__name__, project_id=project_id)
    
    async def generate_reflection(
        self,
        task: TaskContext,
        attempt: AttemptResult,
        agent_id: str,
        attempt_number: int,
        trigger: ReflexionTrigger,
        previous_reflections: Optional[list[Reflection]] = None,
        llm_client: Optional[Any] = None,
    ) -> Reflection:
        """
        Generate a structured reflection from a failed attempt.
        
        Args:
            task: The task context.
            attempt: The failed attempt result.
            agent_id: ID of the agent that made the attempt.
            attempt_number: Current attempt number.
            trigger: What triggered the reflexion.
            previous_reflections: Previous reflections for this task.
            llm_client: Optional LLM client for generation.
            
        Returns:
            Structured Reflection object.
        """
        self._logger.info(
            f"Generating reflection for task {task.task_id}, attempt {attempt_number}",
            extra={"trigger": trigger.value},
        )
        
        # Format previous reflections for prompt
        prev_refs_str = ""
        if previous_reflections:
            prev_refs_str = "\n".join([
                f"Attempt {r.attempt_number}: {r.root_cause.technical}"
                for r in previous_reflections
            ])
        
        # Build the prompt
        prompt = REFLECTION_PROMPT.format(
            task_description=task.description,
            approach_taken=attempt.approach_taken,
            code=attempt.code_produced or "(no code)",
            test_results=attempt.test_results or "(no test results)",
            errors=attempt.error or "(no errors)",
            metrics=json.dumps(attempt.performance_metrics or {}),
            attempt_number=attempt_number,
            previous_reflections=prev_refs_str or "(none)",
        )
        
        # Generate reflection via LLM
        if llm_client:
            response = await self._call_llm(llm_client, prompt)
            reflection_data = self._parse_reflection_response(response)
        else:
            # Fallback: structured reflection without LLM
            reflection_data = self._generate_fallback_reflection(
                task, attempt, trigger
            )
        
        # Create Reflection object
        reflection = Reflection(
            reflection_id=str(uuid4()),
            task_id=task.task_id,
            agent_id=agent_id,
            attempt_number=attempt_number,
            trigger=trigger,
            timestamp=datetime.now(),
            root_cause=RootCause(**reflection_data["root_cause"]),
            incorrect_assumptions=[
                IncorrectAssumption(**a) 
                for a in reflection_data["incorrect_assumptions"]
            ],
            improved_strategy=ImprovedStrategy(**reflection_data["improved_strategy"]),
            lessons_learned=[
                LessonLearned(**l) 
                for l in reflection_data["lessons_learned"]
            ],
            task_description=task.description,
            approach_taken=attempt.approach_taken,
            code_produced=attempt.code_produced,
            test_results=attempt.test_results,
            errors=attempt.error,
            performance_metrics=attempt.performance_metrics,
        )
        
        # Store reflection
        await self.store_reflection(reflection)
        
        # Extract patterns if generalizable
        await self._extract_patterns(reflection)
        
        return reflection
    
    async def store_reflection(self, reflection: Reflection) -> None:
        """
        Store reflection in episodic memory.
        
        Args:
            reflection: The reflection to store.
        """
        task_id = reflection.task_id
        
        if task_id not in self._reflections:
            self._reflections[task_id] = []
        
        self._reflections[task_id].append(reflection)
        
        self._logger.info(
            f"Stored reflection {reflection.reflection_id} for task {task_id}",
            extra={"attempt": reflection.attempt_number},
        )
        
        # TODO: Persist to Mem0 / database
    
    async def get_reflections(self, task_id: str) -> list[Reflection]:
        """
        Get all reflections for a task.
        
        Args:
            task_id: The task identifier.
            
        Returns:
            List of reflections for the task.
        """
        return self._reflections.get(task_id, [])
    
    def get_retry_context(
        self,
        task: TaskContext,
        reflections: list[Reflection],
    ) -> RetryContext:
        """
        Build enhanced context for retry attempt.
        
        Args:
            task: Original task context.
            reflections: All reflections for this task.
            
        Returns:
            RetryContext with accumulated learnings.
        """
        # Build summary of previous attempts
        summaries = []
        for r in reflections:
            summaries.append(
                f"Attempt {r.attempt_number}: {r.root_cause.technical} "
                f"→ {r.improved_strategy.approach}"
            )
        
        # Find relevant patterns
        relevant_patterns = self._find_relevant_patterns(task)
        
        # Find similar successful tasks (would query memory)
        similar_tasks: list[dict[str, Any]] = []
        
        return RetryContext(
            original_task=task,
            previous_attempts_summary="\n".join(summaries),
            reflections=reflections,
            relevant_patterns=relevant_patterns,
            similar_successful_tasks=similar_tasks,
        )
    
    def should_continue_retrying(
        self,
        attempt_number: int,
        reflections: list[Reflection],
    ) -> bool:
        """
        Determine if retry should continue.
        
        Args:
            attempt_number: Current attempt number.
            reflections: Accumulated reflections.
            
        Returns:
            True if should retry, False if should give up.
        """
        if attempt_number >= self.max_attempts:
            self._logger.warning(
                f"Max attempts ({self.max_attempts}) reached"
            )
            return False
        
        # Check if reflections show progress
        if len(reflections) >= 2:
            # Could add logic to detect if making progress
            pass
        
        return True
    
    async def _call_llm(self, client: Any, prompt: str) -> str:
        """Call LLM for reflection generation."""
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2048,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        except Exception as e:
            self._logger.error(f"LLM call failed: {e}")
            raise
    
    def _parse_reflection_response(self, response: str) -> dict[str, Any]:
        """Parse LLM response into reflection structure."""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
        
        # Fallback structure
        return self._generate_fallback_reflection(
            TaskContext(task_id="", description=""),
            AttemptResult(success=False, output=None, error=response),
            ReflexionTrigger.API_ERROR,
        )
    
    def _generate_fallback_reflection(
        self,
        task: TaskContext,
        attempt: AttemptResult,
        trigger: ReflexionTrigger,
    ) -> dict[str, Any]:
        """Generate fallback reflection without LLM."""
        return {
            "root_cause": {
                "technical": attempt.error or "Unknown error",
                "reasoning": f"Task failed during {trigger.value}",
            },
            "incorrect_assumptions": [
                {
                    "assumption": "Initial approach would work",
                    "why_wrong": "Did not account for edge cases",
                    "correct_approach": "Add more validation and error handling",
                }
            ],
            "improved_strategy": {
                "approach": "Retry with additional validation",
                "implementation_steps": [
                    "Review error details",
                    "Add error handling",
                    "Add validation",
                    "Test edge cases",
                ],
                "validation_plan": "Run comprehensive tests before submission",
            },
            "lessons_learned": [
                {
                    "lesson": f"Handle {trigger.value} gracefully",
                    "applicability": "Similar tasks with same failure mode",
                    "pattern_name": f"handle_{trigger.value}",
                }
            ],
        }
    
    async def _extract_patterns(self, reflection: Reflection) -> None:
        """Extract generalizable patterns from reflection."""
        for lesson in reflection.lessons_learned:
            if lesson.pattern_name:
                pattern = {
                    "name": lesson.pattern_name,
                    "description": lesson.lesson,
                    "applicability": lesson.applicability,
                    "source_reflection_id": reflection.reflection_id,
                    "created_at": datetime.now().isoformat(),
                }
                
                # Check if pattern already exists
                existing = [
                    p for p in self._pattern_library 
                    if p["name"] == lesson.pattern_name
                ]
                
                if not existing:
                    self._pattern_library.append(pattern)
                    self._logger.info(
                        f"Added pattern to library: {lesson.pattern_name}"
                    )
    
    def _find_relevant_patterns(
        self,
        task: TaskContext,
    ) -> list[dict[str, Any]]:
        """Find patterns relevant to a task."""
        # Simple keyword matching for now
        # TODO: Use semantic search with embeddings
        relevant = []
        task_text = task.description.lower()
        
        for pattern in self._pattern_library:
            applicability = pattern.get("applicability", "").lower()
            if any(word in task_text for word in applicability.split()):
                relevant.append(pattern)
        
        return relevant
    
    def get_pattern_library(self) -> list[dict[str, Any]]:
        """Get all patterns in the library."""
        return list(self._pattern_library)
    
    def add_pattern(self, pattern: dict[str, Any]) -> None:
        """Manually add a pattern to the library."""
        self._pattern_library.append(pattern)
        self._logger.info(f"Added pattern: {pattern.get('name', 'unknown')}")
