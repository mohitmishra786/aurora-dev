"""
Unit tests for the Reflexion engine.
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from aurora_dev.core.reflexion import (
    ReflexionEngine,
    Reflection,
    ReflexionTrigger,
    TaskContext,
    AttemptResult,
    RetryContext,
    RootCause,
    IncorrectAssumption,
    ImprovedStrategy,
    LessonLearned,
)


class TestReflexionDataclasses:
    """Test dataclass serialization."""
    
    def test_reflection_to_dict(self):
        """Test Reflection.to_dict()."""
        reflection = Reflection(
            reflection_id="ref-123",
            task_id="task-456",
            agent_id="backend",
            attempt_number=1,
            trigger=ReflexionTrigger.TEST_FAILURE,
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            root_cause=RootCause(
                technical="Missing null check",
                reasoning="Assumed input would always be valid",
            ),
            incorrect_assumptions=[
                IncorrectAssumption(
                    assumption="Input is always valid",
                    why_wrong="User can submit empty form",
                    correct_approach="Add input validation",
                )
            ],
            improved_strategy=ImprovedStrategy(
                approach="Add comprehensive validation",
                implementation_steps=["Add null checks", "Add type validation"],
                validation_plan="Run unit tests and manual testing",
            ),
            lessons_learned=[
                LessonLearned(
                    lesson="Always validate inputs",
                    applicability="All user-facing endpoints",
                    pattern_name="input_validation",
                )
            ],
            task_description="Implement user login",
            approach_taken="Direct database query",
            code_produced="def login(): ...",
            test_results="1 failed",
            errors="NullPointerError",
            performance_metrics={"latency_ms": 100},
        )
        
        result = reflection.to_dict()
        
        assert result["reflection_id"] == "ref-123"
        assert result["task_id"] == "task-456"
        assert result["trigger"] == "test_failure"
        assert result["root_cause"]["technical"] == "Missing null check"
        assert len(result["incorrect_assumptions"]) == 1
        assert result["improved_strategy"]["approach"] == "Add comprehensive validation"
        assert len(result["lessons_learned"]) == 1
    
    def test_retry_context_to_prompt(self):
        """Test RetryContext.to_prompt_context()."""
        reflection = Reflection(
            reflection_id="ref-1",
            task_id="task-1",
            agent_id="backend",
            attempt_number=1,
            trigger=ReflexionTrigger.TEST_FAILURE,
            timestamp=datetime.now(),
            root_cause=RootCause(technical="Bug X", reasoning="Reason Y"),
            incorrect_assumptions=[],
            improved_strategy=ImprovedStrategy(
                approach="New approach",
                implementation_steps=[],
                validation_plan="Test it",
            ),
            lessons_learned=[],
            task_description="",
            approach_taken="",
            code_produced=None,
            test_results=None,
            errors=None,
            performance_metrics=None,
        )
        
        context = RetryContext(
            original_task=TaskContext(
                task_id="task-1",
                description="Build feature X",
            ),
            previous_attempts_summary="Attempt 1 failed due to bug",
            reflections=[reflection],
            relevant_patterns=[{"name": "pattern_a"}],
            similar_successful_tasks=[],
        )
        
        prompt = context.to_prompt_context()
        
        assert "ORIGINAL TASK:" in prompt
        assert "Build feature X" in prompt
        assert "PREVIOUS ATTEMPTS" in prompt
        assert "LATEST REFLECTION" in prompt
        assert "Bug X" in prompt


class TestReflexionEngine:
    """Test ReflexionEngine functionality."""
    
    @pytest.fixture
    def engine(self):
        """Create engine instance."""
        return ReflexionEngine(project_id="test-project", max_attempts=5)
    
    def test_init(self, engine):
        """Test engine initialization."""
        assert engine.project_id == "test-project"
        assert engine.max_attempts == 5
    
    def test_should_continue_retrying_under_limit(self, engine):
        """Test retry continues under max attempts."""
        assert engine.should_continue_retrying(1, []) is True
        assert engine.should_continue_retrying(4, []) is True
    
    def test_should_stop_retrying_at_limit(self, engine):
        """Test retry stops at max attempts."""
        assert engine.should_continue_retrying(5, []) is False
        assert engine.should_continue_retrying(6, []) is False
    
    @pytest.mark.asyncio
    async def test_generate_reflection_without_llm(self, engine):
        """Test fallback reflection generation."""
        task = TaskContext(
            task_id="task-123",
            description="Implement user auth",
        )
        
        attempt = AttemptResult(
            success=False,
            output=None,
            error="Authentication failed",
            approach_taken="Basic auth",
        )
        
        reflection = await engine.generate_reflection(
            task=task,
            attempt=attempt,
            agent_id="backend",
            attempt_number=1,
            trigger=ReflexionTrigger.TEST_FAILURE,
            llm_client=None,  # No LLM, use fallback
        )
        
        assert reflection.task_id == "task-123"
        assert reflection.agent_id == "backend"
        assert reflection.attempt_number == 1
        assert reflection.trigger == ReflexionTrigger.TEST_FAILURE
        assert "Authentication failed" in reflection.root_cause.technical
    
    @pytest.mark.asyncio
    async def test_store_and_get_reflections(self, engine):
        """Test reflection storage."""
        task = TaskContext(task_id="task-1", description="Test task")
        attempt = AttemptResult(success=False, output=None, error="Error")
        
        reflection = await engine.generate_reflection(
            task=task,
            attempt=attempt,
            agent_id="test",
            attempt_number=1,
            trigger=ReflexionTrigger.VALIDATION_ERROR,
        )
        
        stored = await engine.get_reflections("task-1")
        
        assert len(stored) == 1
        assert stored[0].reflection_id == reflection.reflection_id
    
    def test_get_retry_context(self, engine):
        """Test building retry context."""
        task = TaskContext(task_id="task-1", description="Test task")
        
        reflection = Reflection(
            reflection_id="ref-1",
            task_id="task-1",
            agent_id="test",
            attempt_number=1,
            trigger=ReflexionTrigger.TEST_FAILURE,
            timestamp=datetime.now(),
            root_cause=RootCause(technical="Bug", reasoning="Reason"),
            incorrect_assumptions=[],
            improved_strategy=ImprovedStrategy(
                approach="Fix it",
                implementation_steps=["Step 1"],
                validation_plan="Test",
            ),
            lessons_learned=[],
            task_description="",
            approach_taken="",
            code_produced=None,
            test_results=None,
            errors=None,
            performance_metrics=None,
        )
        
        context = engine.get_retry_context(task, [reflection])
        
        assert context.original_task == task
        assert len(context.reflections) == 1
        assert "Fix it" in context.previous_attempts_summary
    
    def test_pattern_library(self, engine):
        """Test pattern library management."""
        pattern = {
            "name": "test_pattern",
            "description": "A test pattern",
            "applicability": "Testing",
        }
        
        engine.add_pattern(pattern)
        patterns = engine.get_pattern_library()
        
        assert len(patterns) == 1
        assert patterns[0]["name"] == "test_pattern"
