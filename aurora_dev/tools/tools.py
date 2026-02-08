"""
Base tool infrastructure for AURORA-DEV.

Provides abstract base class and registry for all external tools
that agents can execute.

Example usage:
    >>> registry = ToolRegistry()
    >>> registry.register(PytestRunner())
    >>> result = await registry.run("pytest", {"path": "tests/"})
"""
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from aurora_dev.core.logging import get_logger


logger = get_logger(__name__)


class ToolStatus(Enum):
    """Status of tool execution."""
    
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class ToolResult:
    """
    Standardized result from tool execution.
    
    Attributes:
        tool_name: Name of the tool that was run.
        status: Execution status.
        output: Tool output (stdout, parsed results, etc.).
        error: Error message if failed.
        exit_code: Process exit code if applicable.
        duration_ms: Execution duration in milliseconds.
        metrics: Additional metrics from the tool.
        metadata: Extra metadata about the execution.
    """
    
    tool_name: str
    status: ToolStatus
    output: Any
    error: Optional[str] = None
    exit_code: Optional[int] = None
    duration_ms: float = 0
    metrics: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def success(self) -> bool:
        """Check if execution was successful."""
        return self.status == ToolStatus.SUCCESS
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "tool_name": self.tool_name,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "metrics": self.metrics,
            "metadata": self.metadata,
        }


class BaseTool(ABC):
    """
    Abstract base class for all tools.
    
    Subclasses must implement:
    - name: Tool identifier
    - description: What the tool does
    - run(): Execute the tool
    
    Optional overrides:
    - validate_config(): Validate input configuration
    - cleanup(): Clean up after execution
    """
    
    def __init__(self):
        """Initialize the tool."""
        self._logger = get_logger(__name__)
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool identifier."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description."""
        pass
    
    @property
    def timeout_seconds(self) -> int:
        """Default timeout for tool execution."""
        return 300  # 5 minutes
    
    @abstractmethod
    async def run(self, config: dict[str, Any]) -> ToolResult:
        """
        Execute the tool with given configuration.
        
        Args:
            config: Tool-specific configuration.
            
        Returns:
            ToolResult with execution outcome.
        """
        pass
    
    def validate_config(self, config: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate tool configuration.
        
        Args:
            config: Configuration to validate.
            
        Returns:
            Tuple of (is_valid, error_message).
        """
        return True, None
    
    async def cleanup(self) -> None:
        """Clean up after execution (override if needed)."""
        pass
    
    async def run_with_timeout(
        self,
        config: dict[str, Any],
        timeout: Optional[int] = None,
    ) -> ToolResult:
        """
        Execute tool with timeout.
        
        Args:
            config: Tool configuration.
            timeout: Optional timeout override.
            
        Returns:
            ToolResult with execution outcome.
        """
        timeout_secs = timeout or self.timeout_seconds
        
        try:
            result = await asyncio.wait_for(
                self.run(config),
                timeout=timeout_secs,
            )
            return result
        except asyncio.TimeoutError:
            self._logger.error(f"Tool {self.name} timed out after {timeout_secs}s")
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.TIMEOUT,
                output=None,
                error=f"Execution timed out after {timeout_secs} seconds",
            )
        finally:
            await self.cleanup()


class ToolRegistry:
    """
    Registry for discovering and running tools.
    
    Provides centralized management of available tools
    and unified execution interface.
    
    Example:
        >>> registry = ToolRegistry()
        >>> registry.register(PytestRunner())
        >>> registry.register(SemgrepScanner())
        >>> available = registry.list_tools()
        >>> result = await registry.run("pytest", {"path": "tests/"})
    """
    
    def __init__(self):
        """Initialize empty registry."""
        self._tools: dict[str, BaseTool] = {}
        self._logger = get_logger(__name__)
    
    def register(self, tool: BaseTool) -> None:
        """
        Register a tool with the registry.
        
        Args:
            tool: Tool instance to register.
        """
        if tool.name in self._tools:
            self._logger.warning(f"Overwriting existing tool: {tool.name}")
        
        self._tools[tool.name] = tool
        self._logger.info(f"Registered tool: {tool.name}")
    
    def unregister(self, name: str) -> None:
        """
        Remove a tool from the registry.
        
        Args:
            name: Tool name to remove.
        """
        if name in self._tools:
            del self._tools[name]
            self._logger.info(f"Unregistered tool: {name}")
    
    def get(self, name: str) -> Optional[BaseTool]:
        """
        Get a tool by name.
        
        Args:
            name: Tool name.
            
        Returns:
            Tool instance or None if not found.
        """
        return self._tools.get(name)
    
    def list_tools(self) -> list[dict[str, str]]:
        """
        List all registered tools.
        
        Returns:
            List of tool info dictionaries.
        """
        return [
            {"name": t.name, "description": t.description}
            for t in self._tools.values()
        ]
    
    async def run(
        self,
        tool_name: str,
        config: dict[str, Any],
        timeout: Optional[int] = None,
    ) -> ToolResult:
        """
        Run a tool by name.
        
        Args:
            tool_name: Name of tool to run.
            config: Tool configuration.
            timeout: Optional timeout override.
            
        Returns:
            ToolResult from execution.
        """
        tool = self._tools.get(tool_name)
        
        if not tool:
            return ToolResult(
                tool_name=tool_name,
                status=ToolStatus.FAILED,
                output=None,
                error=f"Tool not found: {tool_name}",
            )
        
        # Validate config
        is_valid, error = tool.validate_config(config)
        if not is_valid:
            return ToolResult(
                tool_name=tool_name,
                status=ToolStatus.FAILED,
                output=None,
                error=f"Invalid configuration: {error}",
            )
        
        # Execute
        self._logger.info(f"Running tool: {tool_name}")
        result = await tool.run_with_timeout(config, timeout)
        self._logger.info(
            f"Tool {tool_name} completed: {result.status.value}"
        )
        
        return result
    
    async def run_parallel(
        self,
        tool_configs: list[tuple[str, dict[str, Any]]],
    ) -> list[ToolResult]:
        """
        Run multiple tools in parallel.
        
        Args:
            tool_configs: List of (tool_name, config) tuples.
            
        Returns:
            List of ToolResults in same order as input.
        """
        tasks = [
            self.run(name, config)
            for name, config in tool_configs
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                tool_name = tool_configs[i][0]
                final_results.append(ToolResult(
                    tool_name=tool_name,
                    status=ToolStatus.FAILED,
                    output=None,
                    error=str(result),
                ))
            else:
                final_results.append(result)
        
        return final_results


# Default global registry
_default_registry: Optional[ToolRegistry] = None


def get_registry() -> ToolRegistry:
    """Get the default tool registry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = ToolRegistry()
    return _default_registry


def register_tool(tool: BaseTool) -> None:
    """Register a tool with the default registry."""
    get_registry().register(tool)
