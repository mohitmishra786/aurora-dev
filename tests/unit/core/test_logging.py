"""Unit tests for logging infrastructure."""
import json
import logging
from unittest.mock import patch

import pytest


class TestJSONFormatter:
    """Tests for JSON log formatter."""

    def test_format_returns_json(self):
        """Test that format returns valid JSON."""
        from aurora_dev.core.logging import JSONFormatter
        
        formatter = JSONFormatter(include_timestamp=False)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert parsed["level"] == "INFO"
        assert parsed["message"] == "Test message"
        assert parsed["logger"] == "test"

    def test_format_includes_timestamp(self):
        """Test that timestamp is included when enabled."""
        from aurora_dev.core.logging import JSONFormatter
        
        formatter = JSONFormatter(include_timestamp=True)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert "timestamp" in parsed

    def test_format_includes_extra_fields(self):
        """Test that extra fields are included."""
        from aurora_dev.core.logging import JSONFormatter
        
        formatter = JSONFormatter(include_timestamp=False)
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None,
        )
        record.agent_id = "agent-123"
        record.task_id = "task-456"
        
        result = formatter.format(record)
        parsed = json.loads(result)
        
        assert parsed["agent_id"] == "agent-123"
        assert parsed["task_id"] == "task-456"


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_returns_adapter(self):
        """Test that get_logger returns a LoggerAdapter."""
        from aurora_dev.core.logging import get_logger
        
        logger = get_logger("test_module")
        
        assert isinstance(logger, logging.LoggerAdapter)

    def test_get_logger_with_context(self):
        """Test that get_logger includes context."""
        from aurora_dev.core.logging import get_logger
        
        logger = get_logger(
            "test_module",
            agent_id="agent-123",
            task_id="task-456",
        )
        
        assert logger.extra["agent_id"] == "agent-123"
        assert logger.extra["task_id"] == "task-456"


class TestGetAgentLogger:
    """Tests for get_agent_logger function."""

    def test_get_agent_logger_returns_adapter(self):
        """Test that get_agent_logger returns a LoggerAdapter."""
        from aurora_dev.core.logging import get_agent_logger
        
        logger = get_agent_logger(
            agent_name="maestro",
            agent_id="maestro-123",
        )
        
        assert isinstance(logger, logging.LoggerAdapter)
        assert logger.extra["agent_id"] == "maestro-123"


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_configures_root_logger(self, mock_settings):
        """Test that setup_logging configures the root logger."""
        from aurora_dev.core.logging import setup_logging
        
        setup_logging(level="DEBUG", log_format="text")
        
        logger = logging.getLogger("aurora_dev")
        assert logger.level == logging.DEBUG
        assert len(logger.handlers) > 0
