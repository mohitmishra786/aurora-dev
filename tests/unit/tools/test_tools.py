"""
Unit tests for the Tool integration module.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from aurora_dev.tools.tools import (
    BaseTool,
    ToolResult,
    ToolStatus,
    ToolRegistry,
)


class MockTool(BaseTool):
    """Mock tool for testing."""
    
    @property
    def name(self) -> str:
        return "mock_tool"
    
    @property
    def description(self) -> str:
        return "A mock tool for testing"
    
    async def run(self, config):
        if config.get("fail"):
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILED,
                output=None,
                error="Mock failure",
            )
        return ToolResult(
            tool_name=self.name,
            status=ToolStatus.SUCCESS,
            output={"result": "success"},
            duration_ms=100,
        )


class TestToolResult:
    """Test ToolResult dataclass."""
    
    def test_success_property(self):
        """Test success property."""
        success_result = ToolResult(
            tool_name="test",
            status=ToolStatus.SUCCESS,
            output="data",
        )
        assert success_result.success is True
        
        failed_result = ToolResult(
            tool_name="test",
            status=ToolStatus.FAILED,
            output=None,
            error="Error",
        )
        assert failed_result.success is False
    
    def test_to_dict(self):
        """Test to_dict conversion."""
        result = ToolResult(
            tool_name="test",
            status=ToolStatus.SUCCESS,
            output={"key": "value"},
            duration_ms=50,
            metrics={"count": 1},
        )
        
        d = result.to_dict()
        
        assert d["tool_name"] == "test"
        assert d["status"] == "success"
        assert d["output"]["key"] == "value"
        assert d["duration_ms"] == 50


class TestToolRegistry:
    """Test ToolRegistry functionality."""
    
    @pytest.fixture
    def registry(self):
        """Create registry with mock tool."""
        reg = ToolRegistry()
        reg.register(MockTool())
        return reg
    
    def test_register_tool(self, registry):
        """Test tool registration."""
        tools = registry.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "mock_tool"
    
    def test_get_tool(self, registry):
        """Test getting registered tool."""
        tool = registry.get("mock_tool")
        assert tool is not None
        assert tool.name == "mock_tool"
        
        missing = registry.get("nonexistent")
        assert missing is None
    
    def test_unregister_tool(self, registry):
        """Test tool unregistration."""
        registry.unregister("mock_tool")
        assert registry.get("mock_tool") is None
    
    @pytest.mark.asyncio
    async def test_run_success(self, registry):
        """Test running tool successfully."""
        result = await registry.run("mock_tool", {"data": "test"})
        
        assert result.success is True
        assert result.output["result"] == "success"
    
    @pytest.mark.asyncio
    async def test_run_failure(self, registry):
        """Test running tool with failure."""
        result = await registry.run("mock_tool", {"fail": True})
        
        assert result.success is False
        assert result.error == "Mock failure"
    
    @pytest.mark.asyncio
    async def test_run_nonexistent_tool(self, registry):
        """Test running nonexistent tool."""
        result = await registry.run("nonexistent", {})
        
        assert result.success is False
        assert "not found" in result.error.lower()
    
    @pytest.mark.asyncio
    async def test_run_parallel(self, registry):
        """Test parallel tool execution."""
        results = await registry.run_parallel([
            ("mock_tool", {"data": "1"}),
            ("mock_tool", {"data": "2"}),
            ("mock_tool", {"fail": True}),
        ])
        
        assert len(results) == 3
        assert results[0].success is True
        assert results[1].success is True
        assert results[2].success is False


class TestBaseTool:
    """Test BaseTool abstract class."""
    
    def test_validate_config_default(self):
        """Test default config validation."""
        tool = MockTool()
        is_valid, error = tool.validate_config({})
        assert is_valid is True
        assert error is None
    
    @pytest.mark.asyncio
    async def test_run_with_timeout(self):
        """Test timeout handling."""
        import asyncio
        
        class SlowTool(BaseTool):
            @property
            def name(self):
                return "slow"
            
            @property
            def description(self):
                return "Slow tool"
            
            @property
            def timeout_seconds(self):
                return 1
            
            async def run(self, config):
                await asyncio.sleep(10)  # Simulate slow operation
                return ToolResult(
                    tool_name=self.name,
                    status=ToolStatus.SUCCESS,
                    output="done",
                )
        
        tool = SlowTool()
        result = await tool.run_with_timeout({}, timeout=1)
        
        assert result.status == ToolStatus.TIMEOUT
        assert "timed out" in result.error.lower()
