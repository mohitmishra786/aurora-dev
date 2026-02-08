"""
Unit tests for Reflexion Engine.

Tests reflection generation, pattern library, and retry context.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock

from aurora_dev.core.reflexion import (
    ReflexionEngine,
    Reflection,
    ReflexionPattern,
    PatternLibrary,
)


class TestReflection:
    """Tests for Reflection dataclass."""
    
    def test_initialization(self) -> None:
        """Test reflection initialization."""
        reflection = Reflection(
            task_id="task-1",
            agent_role="backend",
            original_output="original code",
            analysis="The code has a bug",
            improvements=["Fix null check", "Add error handling"],
            confidence_score=0.85,
        )
        
        assert reflection.task_id == "task-1"
        assert reflection.agent_role == "backend"
        assert reflection.confidence_score == 0.85
        assert len(reflection.improvements) == 2
    
    def test_is_high_confidence(self) -> None:
        """Test high confidence check."""
        high = Reflection(
            task_id="t1",
            agent_role="backend",
            original_output="",
            analysis="",
            improvements=[],
            confidence_score=0.9,
        )
        
        low = Reflection(
            task_id="t2",
            agent_role="backend",
            original_output="",
            analysis="",
            improvements=[],
            confidence_score=0.5,
        )
        
        assert high.is_high_confidence(threshold=0.8) is True
        assert low.is_high_confidence(threshold=0.8) is False


class TestReflexionPattern:
    """Tests for ReflexionPattern."""
    
    def test_initialization(self) -> None:
        """Test pattern initialization."""
        pattern = ReflexionPattern(
            name="null_check",
            description="Missing null/undefined checks",
            detection_keywords=["null", "undefined", "NoneType"],
            suggested_fix="Add null checks before accessing properties",
            severity="high",
        )
        
        assert pattern.name == "null_check"
        assert pattern.severity == "high"
        assert "null" in pattern.detection_keywords
    
    def test_matches_content(self) -> None:
        """Test pattern matching against content."""
        pattern = ReflexionPattern(
            name="sql_injection",
            description="Potential SQL injection",
            detection_keywords=["f-string", "format(", "% s"],
            suggested_fix="Use parameterized queries",
            severity="critical",
        )
        
        vulnerable_code = "query = f\"SELECT * FROM users WHERE id = {user_id}\""
        safe_code = "query = 'SELECT * FROM users WHERE id = ?'"
        
        assert pattern.matches(vulnerable_code) is True
        assert pattern.matches(safe_code) is False


class TestPatternLibrary:
    """Tests for PatternLibrary."""
    
    def test_add_pattern(self) -> None:
        """Test adding patterns to library."""
        library = PatternLibrary()
        
        pattern = ReflexionPattern(
            name="error_handling",
            description="Missing error handling",
            detection_keywords=["try:", "except", "catch"],
            suggested_fix="Add try-except blocks",
            severity="medium",
        )
        
        library.add_pattern(pattern)
        
        assert library.get_pattern("error_handling") is not None
    
    def test_find_matches(self) -> None:
        """Test finding matching patterns."""
        library = PatternLibrary()
        
        library.add_pattern(ReflexionPattern(
            name="hardcoded_secret",
            description="Hardcoded secrets",
            detection_keywords=["password =", "api_key =", "secret ="],
            suggested_fix="Use environment variables",
            severity="critical",
        ))
        
        code = 'password = "mysecretpassword"'
        matches = library.find_matches(code)
        
        assert len(matches) >= 1
        assert any(m.name == "hardcoded_secret" for m in matches)
    
    def test_get_by_severity(self) -> None:
        """Test filtering patterns by severity."""
        library = PatternLibrary()
        
        library.add_pattern(ReflexionPattern(
            name="p1", description="", detection_keywords=[], 
            suggested_fix="", severity="critical"
        ))
        library.add_pattern(ReflexionPattern(
            name="p2", description="", detection_keywords=[], 
            suggested_fix="", severity="low"
        ))
        
        critical = library.get_by_severity("critical")
        
        assert len(critical) == 1
        assert critical[0].name == "p1"


class TestReflexionEngine:
    """Tests for ReflexionEngine."""
    
    @patch("aurora_dev.core.reflexion.Anthropic")
    def test_initialization(self, mock_anthropic: Mock) -> None:
        """Test engine initialization."""
        engine = ReflexionEngine()
        
        assert engine is not None
        assert engine._pattern_library is not None
    
    @patch("aurora_dev.core.reflexion.Anthropic")
    def test_should_reflect_on_error(self, mock_anthropic: Mock) -> None:
        """Test that errors trigger reflection."""
        engine = ReflexionEngine()
        
        result = {
            "success": False,
            "error": "TypeError: Cannot read property",
            "output": None,
        }
        
        assert engine.should_reflect(result) is True
    
    @patch("aurora_dev.core.reflexion.Anthropic")
    def test_should_not_reflect_on_success(self, mock_anthropic: Mock) -> None:
        """Test that success doesn't always trigger reflection."""
        engine = ReflexionEngine()
        
        result = {
            "success": True,
            "error": None,
            "output": "Valid output",
            "quality_score": 0.95,
        }
        
        # High quality success shouldn't need reflection
        assert engine.should_reflect(result, quality_threshold=0.9) is False
    
    @patch("aurora_dev.core.reflexion.Anthropic")
    def test_extract_context(self, mock_anthropic: Mock) -> None:
        """Test context extraction for retry."""
        engine = ReflexionEngine()
        
        reflection = Reflection(
            task_id="task-1",
            agent_role="backend",
            original_output="buggy code",
            analysis="Missing error handling",
            improvements=["Add try-except", "Validate input"],
            confidence_score=0.9,
        )
        
        context = engine.extract_retry_context(reflection)
        
        assert "improvements" in context
        assert len(context["improvements"]) == 2
        assert context["previous_analysis"] == "Missing error handling"
    
    @patch("aurora_dev.core.reflexion.Anthropic")
    def test_pattern_detection(self, mock_anthropic: Mock) -> None:
        """Test automatic pattern detection in output."""
        engine = ReflexionEngine()
        
        # Add a test pattern
        engine._pattern_library.add_pattern(ReflexionPattern(
            name="print_debug",
            description="Debug print statements",
            detection_keywords=["print(", "console.log"],
            suggested_fix="Use proper logging",
            severity="low",
        ))
        
        output = """
def process():
    print("Debug: processing started")
    return result
"""
        
        patterns = engine.detect_patterns(output)
        
        assert len(patterns) >= 1
