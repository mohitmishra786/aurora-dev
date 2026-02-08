"""
DockerRunner: Secure code execution environment for AURORA-DEV.

This module provides isolated Docker-based execution for agent-generated code.
Features:
- Container lifecycle management
- Resource limits (CPU, memory, timeout)
- Network isolation
- Volume mounting for code/artifacts
- Streaming output capture

Example usage:
    >>> runner = DockerRunner()
    >>> result = runner.run_code("print('Hello, World!')", language="python")
    >>> print(result.stdout)
    Hello, World!
"""
import asyncio
import logging
import shutil
import tempfile
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

try:
    import docker
    from docker.errors import (
        ContainerError,
        ImageNotFound,
        APIError as DockerAPIError,
    )
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    docker = None


logger = logging.getLogger(__name__)


class Language(Enum):
    """Supported programming languages for execution."""
    
    PYTHON = "python"
    NODEJS = "nodejs"
    GO = "go"
    RUST = "rust"
    BASH = "bash"


# Language-specific Docker images and configurations
LANGUAGE_CONFIG: dict[str, dict[str, Any]] = {
    "python": {
        "image": "python:3.11-slim",
        "entrypoint": ["python", "-c"],
        "file_ext": ".py",
        "file_entrypoint": ["python"],
    },
    "nodejs": {
        "image": "node:20-alpine",
        "entrypoint": ["node", "-e"],
        "file_ext": ".js",
        "file_entrypoint": ["node"],
    },
    "go": {
        "image": "golang:1.22-alpine",
        "entrypoint": ["go", "run"],
        "file_ext": ".go",
        "file_entrypoint": ["go", "run"],
    },
    "rust": {
        "image": "rust:1.76-slim",
        "entrypoint": ["rustc", "-o", "/tmp/out", "--"],
        "file_ext": ".rs",
        "file_entrypoint": ["sh", "-c", "rustc -o /tmp/out $0 && /tmp/out"],
    },
    "bash": {
        "image": "alpine:3.19",
        "entrypoint": ["sh", "-c"],
        "file_ext": ".sh",
        "file_entrypoint": ["sh"],
    },
}


@dataclass
class ExecutionResult:
    """Result from code execution."""
    
    success: bool
    exit_code: int
    stdout: str
    stderr: str
    execution_time_ms: float
    container_id: Optional[str] = None
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "exit_code": self.exit_code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "execution_time_ms": self.execution_time_ms,
            "container_id": self.container_id,
            "error": self.error,
            "metadata": self.metadata,
        }


@dataclass
class ResourceLimits:
    """Resource limits for container execution."""
    
    cpu_count: float = 1.0  # Number of CPUs
    memory_mb: int = 512    # Memory limit in MB
    timeout_seconds: int = 60  # Execution timeout
    disk_mb: int = 100      # Disk space limit (for tmpfs)
    network_enabled: bool = False  # Network access


class DockerRunner:
    """
    Docker-based code execution runner.
    
    Provides secure, isolated execution environment for agent-generated code.
    
    Attributes:
        client: Docker client instance.
        default_limits: Default resource limits.
        workspace_dir: Base directory for code files.
    """
    
    def __init__(
        self,
        default_limits: Optional[ResourceLimits] = None,
        workspace_dir: Optional[Path] = None,
    ) -> None:
        """
        Initialize the DockerRunner.
        
        Args:
            default_limits: Default resource limits for containers.
            workspace_dir: Base directory for temporary files.
            
        Raises:
            RuntimeError: If Docker is not available.
        """
        if not DOCKER_AVAILABLE:
            raise RuntimeError(
                "Docker SDK not installed. Install with: pip install docker"
            )
        
        try:
            self._client = docker.from_env()
            # Verify Docker is running
            self._client.ping()
        except Exception as e:
            raise RuntimeError(f"Docker is not available: {e}")
        
        self._default_limits = default_limits or ResourceLimits()
        self._workspace_dir = workspace_dir or Path(tempfile.gettempdir()) / "aurora_runner"
        self._workspace_dir.mkdir(parents=True, exist_ok=True)
        
        # Track active containers for cleanup
        self._active_containers: set[str] = set()
        
        logger.info(
            f"DockerRunner initialized",
            extra={"workspace": str(self._workspace_dir)},
        )
    
    def _get_language_config(self, language: str) -> dict[str, Any]:
        """Get configuration for a language."""
        lang = language.lower()
        if lang not in LANGUAGE_CONFIG:
            raise ValueError(f"Unsupported language: {language}")
        return LANGUAGE_CONFIG[lang]
    
    def _ensure_image(self, image: str) -> None:
        """Ensure the Docker image is available."""
        try:
            self._client.images.get(image)
            logger.debug(f"Image {image} already available")
        except ImageNotFound:
            logger.info(f"Pulling image: {image}")
            self._client.images.pull(image)
    
    def run_code(
        self,
        code: str,
        language: str = "python",
        limits: Optional[ResourceLimits] = None,
        env_vars: Optional[dict[str, str]] = None,
        working_dir: Optional[str] = None,
    ) -> ExecutionResult:
        """
        Execute code in a Docker container.
        
        Args:
            code: The code to execute.
            language: Programming language (python, nodejs, go, rust, bash).
            limits: Resource limits (uses defaults if not provided).
            env_vars: Environment variables to set.
            working_dir: Working directory inside container.
            
        Returns:
            ExecutionResult with output and status.
        """
        limits = limits or self._default_limits
        config = self._get_language_config(language)
        
        # Ensure image is available
        try:
            self._ensure_image(config["image"])
        except Exception as e:
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                execution_time_ms=0,
                error=f"Failed to pull image: {e}",
            )
        
        start_time = time.time()
        container = None
        
        try:
            # Prepare container configuration
            container_config = {
                "image": config["image"],
                "command": config["entrypoint"] + [code],
                "detach": True,
                "mem_limit": f"{limits.memory_mb}m",
                "cpu_period": 100000,
                "cpu_quota": int(100000 * limits.cpu_count),
                "network_mode": "bridge" if limits.network_enabled else "none",
                "environment": env_vars or {},
                "working_dir": working_dir or "/app",
                "read_only": True,  # Security: read-only root filesystem
                "tmpfs": {"/tmp": f"size={limits.disk_mb}m"},  # Writable /tmp
                "security_opt": ["no-new-privileges:true"],  # Security hardening
            }
            
            # Create and start container
            container = self._client.containers.run(**container_config)
            self._active_containers.add(container.id)
            
            # Wait for completion with timeout
            try:
                result = container.wait(timeout=limits.timeout_seconds)
                exit_code = result.get("StatusCode", -1)
            except Exception:
                # Timeout - kill the container
                container.kill()
                execution_time_ms = (time.time() - start_time) * 1000
                return ExecutionResult(
                    success=False,
                    exit_code=-1,
                    stdout="",
                    stderr="",
                    execution_time_ms=execution_time_ms,
                    container_id=container.id,
                    error=f"Execution timed out after {limits.timeout_seconds}s",
                )
            
            # Get output
            stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
            stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            return ExecutionResult(
                success=exit_code == 0,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                execution_time_ms=execution_time_ms,
                container_id=container.id,
            )
            
        except ContainerError as e:
            execution_time_ms = (time.time() - start_time) * 1000
            return ExecutionResult(
                success=False,
                exit_code=e.exit_status,
                stdout="",
                stderr=e.stderr.decode("utf-8", errors="replace") if e.stderr else "",
                execution_time_ms=execution_time_ms,
                container_id=container.id if container else None,
                error=str(e),
            )
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Docker execution failed: {e}")
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                execution_time_ms=execution_time_ms,
                error=str(e),
            )
            
        finally:
            # Cleanup container
            if container:
                try:
                    container.remove(force=True)
                    self._active_containers.discard(container.id)
                except Exception as e:
                    logger.warning(f"Failed to remove container: {e}")
    
    def run_file(
        self,
        file_path: Path,
        language: Optional[str] = None,
        limits: Optional[ResourceLimits] = None,
        env_vars: Optional[dict[str, str]] = None,
    ) -> ExecutionResult:
        """
        Execute a file in a Docker container.
        
        Args:
            file_path: Path to the file to execute.
            language: Programming language (auto-detected if not provided).
            limits: Resource limits.
            env_vars: Environment variables.
            
        Returns:
            ExecutionResult with output and status.
        """
        if not file_path.exists():
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                execution_time_ms=0,
                error=f"File not found: {file_path}",
            )
        
        # Auto-detect language from extension
        if language is None:
            ext_map = {".py": "python", ".js": "nodejs", ".go": "go", ".rs": "rust", ".sh": "bash"}
            language = ext_map.get(file_path.suffix.lower(), "bash")
        
        limits = limits or self._default_limits
        config = self._get_language_config(language)
        
        try:
            self._ensure_image(config["image"])
        except Exception as e:
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                execution_time_ms=0,
                error=f"Failed to pull image: {e}",
            )
        
        start_time = time.time()
        container = None
        
        try:
            # Mount the file into the container
            container_file_path = f"/app/{file_path.name}"
            volumes = {
                str(file_path.resolve()): {"bind": container_file_path, "mode": "ro"}
            }
            
            container_config = {
                "image": config["image"],
                "command": config["file_entrypoint"] + [container_file_path],
                "detach": True,
                "mem_limit": f"{limits.memory_mb}m",
                "cpu_period": 100000,
                "cpu_quota": int(100000 * limits.cpu_count),
                "network_mode": "bridge" if limits.network_enabled else "none",
                "environment": env_vars or {},
                "volumes": volumes,
                "working_dir": "/app",
                "tmpfs": {"/tmp": f"size={limits.disk_mb}m"},
                "security_opt": ["no-new-privileges:true"],
            }
            
            container = self._client.containers.run(**container_config)
            self._active_containers.add(container.id)
            
            try:
                result = container.wait(timeout=limits.timeout_seconds)
                exit_code = result.get("StatusCode", -1)
            except Exception:
                container.kill()
                execution_time_ms = (time.time() - start_time) * 1000
                return ExecutionResult(
                    success=False,
                    exit_code=-1,
                    stdout="",
                    stderr="",
                    execution_time_ms=execution_time_ms,
                    container_id=container.id,
                    error=f"Execution timed out after {limits.timeout_seconds}s",
                )
            
            stdout = container.logs(stdout=True, stderr=False).decode("utf-8", errors="replace")
            stderr = container.logs(stdout=False, stderr=True).decode("utf-8", errors="replace")
            
            execution_time_ms = (time.time() - start_time) * 1000
            
            return ExecutionResult(
                success=exit_code == 0,
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                execution_time_ms=execution_time_ms,
                container_id=container.id,
            )
            
        except Exception as e:
            execution_time_ms = (time.time() - start_time) * 1000
            logger.error(f"Docker file execution failed: {e}")
            return ExecutionResult(
                success=False,
                exit_code=-1,
                stdout="",
                stderr="",
                execution_time_ms=execution_time_ms,
                error=str(e),
            )
            
        finally:
            if container:
                try:
                    container.remove(force=True)
                    self._active_containers.discard(container.id)
                except Exception as e:
                    logger.warning(f"Failed to remove container: {e}")
    
    async def run_code_async(
        self,
        code: str,
        language: str = "python",
        limits: Optional[ResourceLimits] = None,
        env_vars: Optional[dict[str, str]] = None,
    ) -> ExecutionResult:
        """Async wrapper for run_code."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self.run_code(code, language, limits, env_vars),
        )
    
    def cleanup(self) -> int:
        """
        Cleanup any remaining active containers.
        
        Returns:
            Number of containers cleaned up.
        """
        cleaned = 0
        for container_id in list(self._active_containers):
            try:
                container = self._client.containers.get(container_id)
                container.remove(force=True)
                self._active_containers.discard(container_id)
                cleaned += 1
            except Exception as e:
                logger.warning(f"Failed to cleanup container {container_id}: {e}")
        
        if cleaned > 0:
            logger.info(f"Cleaned up {cleaned} containers")
        
        return cleaned
    
    def __del__(self) -> None:
        """Cleanup on destruction."""
        try:
            self.cleanup()
        except Exception:
            pass


# Singleton instance
_runner: Optional[DockerRunner] = None


def get_runner() -> DockerRunner:
    """Get the global DockerRunner instance."""
    global _runner
    if _runner is None:
        _runner = DockerRunner()
    return _runner


if __name__ == "__main__":
    # Demo usage
    runner = DockerRunner()
    
    # Test Python execution
    result = runner.run_code("print('Hello from Docker!')", language="python")
    print(f"Python: {result.stdout.strip()} (exit: {result.exit_code})")
    
    # Test with timeout
    limits = ResourceLimits(timeout_seconds=5)
    result = runner.run_code(
        "import time; time.sleep(10); print('Done')",
        language="python",
        limits=limits,
    )
    print(f"Timeout test: {result.error or result.stdout.strip()}")
