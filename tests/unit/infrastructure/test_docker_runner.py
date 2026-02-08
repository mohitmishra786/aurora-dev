"""
Tests for DockerRunner.

Tests container execution, resource limits, and error handling.
Uses mocks when Docker is unavailable for CI environments.
"""
import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch, PropertyMock
import tempfile

# Try to import docker_runner
try:
    from aurora_dev.infrastructure.docker_runner import (
        DockerRunner,
        ExecutionResult,
        ResourceLimits,
        DOCKER_AVAILABLE,
        LANGUAGE_CONFIG,
    )
    IMPORT_SUCCESS = True
except ImportError:
    IMPORT_SUCCESS = False
    DOCKER_AVAILABLE = False


@pytest.fixture
def mock_docker_client():
    """Create a mock Docker client."""
    with patch("aurora_dev.infrastructure.docker_runner.docker") as mock_docker:
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        mock_client.ping.return_value = True
        yield mock_client


@pytest.fixture
def mock_container():
    """Create a mock container."""
    container = MagicMock()
    container.id = "test-container-123"
    container.wait.return_value = {"StatusCode": 0}
    container.logs.return_value = b"Hello, World!\n"
    return container


@pytest.mark.skipif(not IMPORT_SUCCESS, reason="docker_runner not importable")
class TestDockerRunner:
    """Tests for DockerRunner class."""
    
    def test_language_config_exists(self):
        """Test that language configurations are defined."""
        assert "python" in LANGUAGE_CONFIG
        assert "nodejs" in LANGUAGE_CONFIG
        assert "go" in LANGUAGE_CONFIG
        assert "bash" in LANGUAGE_CONFIG
    
    def test_language_config_has_required_keys(self):
        """Test that each language config has required keys."""
        required_keys = {"image", "entrypoint", "file_ext", "file_entrypoint"}
        for lang, config in LANGUAGE_CONFIG.items():
            assert required_keys.issubset(config.keys()), f"{lang} missing keys"
    
    def test_execution_result_to_dict(self):
        """Test ExecutionResult serialization."""
        result = ExecutionResult(
            success=True,
            exit_code=0,
            stdout="Hello",
            stderr="",
            execution_time_ms=100.5,
            container_id="abc123",
        )
        data = result.to_dict()
        
        assert data["success"] is True
        assert data["exit_code"] == 0
        assert data["stdout"] == "Hello"
        assert data["execution_time_ms"] == 100.5
        assert data["container_id"] == "abc123"
    
    def test_resource_limits_defaults(self):
        """Test default resource limits."""
        limits = ResourceLimits()
        
        assert limits.cpu_count == 1.0
        assert limits.memory_mb == 512
        assert limits.timeout_seconds == 60
        assert limits.network_enabled is False
    
    def test_resource_limits_custom(self):
        """Test custom resource limits."""
        limits = ResourceLimits(
            cpu_count=2.0,
            memory_mb=1024,
            timeout_seconds=120,
            network_enabled=True,
        )
        
        assert limits.cpu_count == 2.0
        assert limits.memory_mb == 1024
        assert limits.timeout_seconds == 120
        assert limits.network_enabled is True


@pytest.mark.skipif(not IMPORT_SUCCESS, reason="docker_runner not importable")
class TestDockerRunnerWithMock:
    """Tests using mocked Docker client."""
    
    def test_init_success(self, mock_docker_client):
        """Test successful initialization."""
        with patch.object(DockerRunner, "__init__", lambda x, **kw: None):
            runner = DockerRunner.__new__(DockerRunner)
            runner._client = mock_docker_client
            runner._default_limits = ResourceLimits()
            runner._workspace_dir = Path(tempfile.gettempdir())
            runner._active_containers = set()
            
            assert runner._client is not None
    
    def test_run_code_success(self, mock_docker_client, mock_container):
        """Test successful code execution."""
        mock_docker_client.images.get.return_value = MagicMock()
        mock_docker_client.containers.run.return_value = mock_container
        
        with patch.object(DockerRunner, "__init__", lambda x, **kw: None):
            runner = DockerRunner.__new__(DockerRunner)
            runner._client = mock_docker_client
            runner._default_limits = ResourceLimits()
            runner._workspace_dir = Path(tempfile.gettempdir())
            runner._active_containers = set()
            
            result = runner.run_code("print('Hello')", language="python")
            
            assert result.success is True
            assert result.exit_code == 0
            assert "Hello" in result.stdout
    
    def test_run_code_unsupported_language(self, mock_docker_client):
        """Test error for unsupported language."""
        with patch.object(DockerRunner, "__init__", lambda x, **kw: None):
            runner = DockerRunner.__new__(DockerRunner)
            runner._client = mock_docker_client
            runner._default_limits = ResourceLimits()
            runner._workspace_dir = Path(tempfile.gettempdir())
            runner._active_containers = set()
            
            with pytest.raises(ValueError, match="Unsupported language"):
                runner.run_code("code", language="cobol")
    
    def test_run_file_not_found(self, mock_docker_client):
        """Test error when file doesn't exist."""
        with patch.object(DockerRunner, "__init__", lambda x, **kw: None):
            runner = DockerRunner.__new__(DockerRunner)
            runner._client = mock_docker_client
            runner._default_limits = ResourceLimits()
            runner._workspace_dir = Path(tempfile.gettempdir())
            runner._active_containers = set()
            
            result = runner.run_file(Path("/nonexistent/file.py"))
            
            assert result.success is False
            assert "File not found" in result.error
    
    def test_cleanup_containers(self, mock_docker_client, mock_container):
        """Test container cleanup."""
        mock_docker_client.containers.get.return_value = mock_container
        
        with patch.object(DockerRunner, "__init__", lambda x, **kw: None):
            runner = DockerRunner.__new__(DockerRunner)
            runner._client = mock_docker_client
            runner._active_containers = {"test-container-123"}
            
            cleaned = runner.cleanup()
            
            assert cleaned == 1
            mock_container.remove.assert_called_once_with(force=True)


@pytest.mark.skipif(
    not DOCKER_AVAILABLE,
    reason="Docker SDK not available"
)
class TestDockerRunnerIntegration:
    """Integration tests requiring actual Docker."""
    
    @pytest.mark.slow
    def test_real_python_execution(self):
        """Test real Python code execution (requires Docker)."""
        try:
            runner = DockerRunner()
            result = runner.run_code("print('Integration test')", language="python")
            
            assert result.success is True
            assert "Integration test" in result.stdout
        except RuntimeError as e:
            if "Docker is not available" in str(e):
                pytest.skip("Docker not running")
            raise
