"""
Unit tests for Reflexion Engine.

Tests ReflexionEngine, Reflection dataclass, and pattern management.
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

from aurora_dev.core.reflexion import (
    ReflexionEngine,
    Reflection,
    RootCause,
    IncorrectAssumption,
    ImprovedStrategy,
    LessonLearned,
    ReflexionTrigger,
    TaskContext,
    AttemptResult,
    RetryContext,
)


class TestReflection:
    """Tests for Reflection dataclass."""
    
    def test_initialization(self) -> None:
        """Test reflection initialization."""
        reflection = Reflection(
            reflection_id="ref-1",
            task_id="task-1",
            agent_id="agent-1",
            attempt_number=1,
            trigger=ReflexionTrigger.TEST_FAILURE,
            timestamp=datetime.now(),
            root_cause=RootCause(
                technical="Null pointer exception",
                reasoning="Missing null check",
            ),
            incorrect_assumptions=[
                IncorrectAssumption(
                    assumption="Input was always valid",
                    why_wrong="External data can be null",
                    correct_approach="Add null checks",
                )
            ],
            improved_strategy=ImprovedStrategy(
                approach="Add validation",
                implementation_steps=["Add null check", "Add tests"],
                validation_plan="Run unit tests",
            ),
            lessons_learned=[
                LessonLearned(
                    lesson="Always validate inputs",
                    applicability="All input handlers",
                    pattern_name="input_validation",
                )
            ],
            task_description="Implement user endpoint",
            approach_taken="Direct implementation",
            code_produced=None,
            test_results=None,
            errors=None,
            performance_metrics=None,
        )
        
        assert reflection.task_id == "task-1"
        assert reflection.agent_id == "agent-1"
        assert reflection.attempt_number == 1
        assert reflection.trigger == ReflexionTrigger.TEST_FAILURE
    
    def test_to_dict(self) -> None:
        """Test conversion to dictionary."""
        reflection = Reflection(
            reflection_id="ref-1",
            task_id="task-1",
            agent_id="agent-1",
            attempt_number=1,
            trigger=ReflexionTrigger.API_ERROR,
            timestamp=datetime.now(),
            root_cause=RootCause(technical="Error", reasoning="Reason"),
            incorrect_assumptions=[],
            improved_strategy=ImprovedStrategy(
                approach="Retry", implementation_steps=[], validation_plan=""
            ),
            lessons_learned=[],
            task_description="",
            approach_taken="",
            code_produced=None,
            test_results=None,
            errors=None,
            performance_metrics=None,
        )
        
        result = reflection.to_dict()
        
        assert result["task_id"] == "task-1"
        assert result["trigger"] == "api_error"
        assert "root_cause" in result
    
    def test_from_dict(self) -> None:
        """Test creation from dictionary."""
        data = {
            "reflection_id": "ref-1",
            "task_id": "task-1",
            "agent_id": "agent-1",
            "attempt_number": 2,
            "trigger": "test_failure",
            "timestamp": datetime.now().isoformat(),
            "root_cause": {"technical": "Bug", "reasoning": "Logic error"},
            "incorrect_assumptions": [],
            "improved_strategy": {
                "approach": "Fix it",
                "implementation_steps": ["Step 1"],
                "validation_plan": "Test it",
            },
            "lessons_learned": [],
        }
        
        reflection = Reflection.from_dict(data)
        
        assert reflection.task_id == "task-1"
        assert reflection.attempt_number == 2


class TestReflexionTrigger:
    """Tests for ReflexionTrigger enum."""
    
    def test_trigger_values(self) -> None:
        """Test trigger enum values."""
        assert ReflexionTrigger.TEST_FAILURE.value == "test_failure"
        assert ReflexionTrigger.SECURITY_VULNERABILITY.value == "security_vulnerability"
        assert ReflexionTrigger.API_ERROR.value == "api_error"


class TestTaskContext:
    """Tests for TaskContext dataclass."""
    
    def test_initialization(self) -> None:
        """Test task context initialization."""
        context = TaskContext(
            task_id="task-1",
            description="Implement feature X",
            requirements=["Req 1", "Req 2"],
            acceptance_criteria=["AC 1", "AC 2"],
        )
        
        assert context.task_id == "task-1"
        assert len(context.requirements) == 2
        assert len(context.acceptance_criteria) == 2


class TestRetryContext:
    """Tests for RetryContext dataclass."""
    
    def test_to_prompt_context(self) -> None:
        """Test formatting for LLM prompt."""
        task = TaskContext(task_id="t1", description="Test task")
        
        context = RetryContext(
            original_task=task,
            previous_attempts_summary="Attempt 1 failed",
            reflections=[],
            relevant_patterns=[],
            similar_successful_tasks=[],
        )
        
        result = context.to_prompt_context()
        
        assert "Test task" in result
        assert "Attempt 1 failed" in result


class TestReflexionEngine:
    """Tests for ReflexionEngine."""
    
    def test_initialization(self) -> None:
        """Test engine initialization."""
        engine = ReflexionEngine(project_id="test-project")
        
        assert engine.project_id == "test-project"
        assert engine.max_attempts == 5
    
    def test_should_continue_retrying_under_max(self) -> None:
        """Test retry decision under max attempts."""
        engine = ReflexionEngine(max_attempts=5)
        
        assert engine.should_continue_retrying(1, []) is True
        assert engine.should_continue_retrying(4, []) is True
    
    def test_should_not_continue_retrying_at_max(self) -> None:
        """Test retry decision at max attempts."""
        engine = ReflexionEngine(max_attempts=5)
        
        assert engine.should_continue_retrying(5, []) is False
        assert engine.should_continue_retrying(6, []) is False
    
    def test_get_retry_context(self) -> None:
        """Test building retry context."""
        engine = ReflexionEngine()
        task = TaskContext(task_id="t1", description="Test")
        
        context = engine.get_retry_context(task, [])
        
        assert context.original_task == task
        assert isinstance(context, RetryContext)
    
    def test_pattern_library_management(self) -> None:
        """Test adding and retrieving patterns."""
        engine = ReflexionEngine()
        
        pattern = {
            "name": "test_pattern",
            "description": "A test pattern",
            "applicability": "testing scenarios",
        }
        
        engine.add_pattern(pattern)
        patterns = engine.get_pattern_library()
        
        assert len(patterns) >= 1
        assert any(p["name"] == "test_pattern" for p in patterns)
    
    @pytest.mark.asyncio
    async def test_store_reflection(self) -> None:
        """Test storing a reflection."""
        engine = ReflexionEngine()
        
        reflection = Reflection(
            reflection_id="ref-1",
            task_id="task-1",
            agent_id="agent-1",
            attempt_number=1,
            trigger=ReflexionTrigger.TEST_FAILURE,
            timestamp=datetime.now(),
            root_cause=RootCause(technical="Error", reasoning="Reason"),
            incorrect_assumptions=[],
            improved_strategy=ImprovedStrategy(
                approach="Fix", implementation_steps=[], validation_plan=""
            ),
            lessons_learned=[],
            task_description="",
            approach_taken="",
            code_produced=None,
            test_results=None,
            errors=None,
            performance_metrics=None,
        )
        
        await engine.store_reflection(reflection)
        
        reflections = await engine.get_reflections("task-1")
        assert len(reflections) == 1
        assert reflections[0].reflection_id == "ref-1"
