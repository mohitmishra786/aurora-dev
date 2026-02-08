"""
Unit tests for the ProjectManager.
"""
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch
import tempfile
import os

from aurora_dev.core.project_manager import (
    ProjectManager,
    Project,
    ProjectConfig,
    ProjectContext,
    ProjectStatus,
    CostTracker,
)


class TestProjectConfig:
    """Test ProjectConfig dataclass."""
    
    def test_to_dict(self):
        """Test serialization."""
        config = ProjectConfig(
            language="python",
            framework="fastapi",
            database="postgresql",
        )
        
        d = config.to_dict()
        
        assert d["language"] == "python"
        assert d["framework"] == "fastapi"
        assert d["database"] == "postgresql"
    
    def test_from_dict(self):
        """Test deserialization."""
        data = {
            "language": "typescript",
            "framework": "next",
            "database": "mongodb",
            "deployment": "docker",
            "custom_settings": {"key": "value"},
        }
        
        config = ProjectConfig.from_dict(data)
        
        assert config.language == "typescript"
        assert config.framework == "next"
        assert config.custom_settings["key"] == "value"


class TestCostTracker:
    """Test CostTracker."""
    
    def test_add_usage(self):
        """Test adding token usage."""
        tracker = CostTracker()
        
        tracker.add_usage(1000000, 500000)  # 1M input, 500k output
        
        # Cost: (1M / 1M * $3) + (500k / 1M * $15) = $3 + $7.5 = $10.5
        assert tracker.input_tokens == 1000000
        assert tracker.output_tokens == 500000
        assert tracker.total_cost_usd == pytest.approx(10.5, rel=0.01)
    
    def test_is_over_budget(self):
        """Test budget checking."""
        tracker = CostTracker(daily_limit_usd=10.0)
        
        assert tracker.is_over_budget() is False
        
        # Add usage that exceeds budget
        tracker.add_usage(3333334, 0)  # ~$10 of input tokens
        
        assert tracker.is_over_budget() is True
    
    def test_remaining_budget(self):
        """Test remaining budget calculation."""
        tracker = CostTracker(daily_limit_usd=100.0)
        
        assert tracker.remaining_budget() == 100.0
        
        tracker.add_usage(1000000, 0)  # $3
        
        assert tracker.remaining_budget() == pytest.approx(97.0, rel=0.01)


class TestProjectContext:
    """Test ProjectContext."""
    
    def test_get_memory_key(self):
        """Test namespaced memory key generation."""
        context = ProjectContext(
            project_id="my-project",
            project_name="My Project",
            project_path=Path("/projects/my-project"),
            config=ProjectConfig(),
            memory_prefix="aurora:project:my-project",
        )
        
        key = context.get_memory_key("task:123")
        
        assert key == "aurora:project:my-project:task:123"
    
    def test_get_cache_key(self):
        """Test namespaced cache key generation."""
        context = ProjectContext(
            project_id="my-project",
            project_name="My Project",
            project_path=Path("/projects/my-project"),
            config=ProjectConfig(),
            memory_prefix="aurora:project:my-project",
        )
        
        key = context.get_cache_key("prompt:abc")
        
        assert key == "cache:aurora:project:my-project:prompt:abc"


class TestProjectManager:
    """Test ProjectManager functionality."""
    
    @pytest.fixture
    def manager(self):
        """Create manager instance."""
        return ProjectManager()
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir
    
    @pytest.mark.asyncio
    async def test_create_project(self, manager, temp_project_dir):
        """Test project creation."""
        project = await manager.create(
            name="Test Project",
            path=temp_project_dir,
            config=ProjectConfig(language="python"),
        )
        
        assert project.id == "test-project"
        assert project.name == "Test Project"
        assert project.path == Path(temp_project_dir)
        assert project.status == ProjectStatus.IDLE
    
    @pytest.mark.asyncio
    async def test_create_duplicate_fails(self, manager, temp_project_dir):
        """Test duplicate project creation fails."""
        await manager.create(name="Test", path=temp_project_dir)
        
        with pytest.raises(ValueError, match="already exists"):
            await manager.create(name="Test", path=temp_project_dir)
    
    @pytest.mark.asyncio
    async def test_switch_project(self, manager, temp_project_dir):
        """Test project switching."""
        await manager.create(name="Project A", path=temp_project_dir)
        
        context = await manager.switch("project-a")
        
        assert context.project_id == "project-a"
        assert manager.get_current().id == "project-a"
        assert manager.get_current().status == ProjectStatus.ACTIVE
    
    @pytest.mark.asyncio
    async def test_switch_nonexistent_fails(self, manager):
        """Test switching to nonexistent project fails."""
        with pytest.raises(ValueError, match="not found"):
            await manager.switch("nonexistent")
    
    @pytest.mark.asyncio
    async def test_list_projects(self, manager, temp_project_dir):
        """Test listing all projects."""
        await manager.create(name="Project 1", path=temp_project_dir)
        await manager.create(name="Project 2", path=temp_project_dir + "2")
        
        projects = manager.list_projects()
        
        assert len(projects) == 2
    
    @pytest.mark.asyncio
    async def test_archive_project(self, manager, temp_project_dir):
        """Test archiving project."""
        await manager.create(name="Archive Me", path=temp_project_dir)
        await manager.switch("archive-me")
        
        await manager.archive("archive-me")
        
        project = manager._projects["archive-me"]
        assert project.status == ProjectStatus.ARCHIVED
        assert manager.get_current() is None
    
    @pytest.mark.asyncio
    async def test_delete_project(self, manager, temp_project_dir):
        """Test deleting project from manager."""
        await manager.create(name="Delete Me", path=temp_project_dir)
        
        await manager.delete("delete-me")
        
        assert "delete-me" not in manager._projects
    
    def test_add_usage(self, manager):
        """Test adding usage to project."""
        # Manually add a project
        manager._projects["test"] = Project(
            id="test",
            name="Test",
            path=Path("/tmp/test"),
            status=ProjectStatus.IDLE,
            config=ProjectConfig(),
            cost_tracker=CostTracker(),
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        manager.add_usage("test", 1000, 500)
        
        summary = manager.get_cost_summary("test")
        assert summary["input_tokens"] == 1000
        assert summary["output_tokens"] == 500
        assert summary["total_cost_usd"] > 0
    
    @pytest.mark.asyncio
    async def test_auto_detect_python_project(self, manager, temp_project_dir):
        """Test auto-detection of Python project."""
        # Create pyproject.toml with fastapi
        pyproject = Path(temp_project_dir) / "pyproject.toml"
        pyproject.write_text('[tool.poetry]\nname = "test"\n\n[tool.poetry.dependencies]\nfastapi = "^0.100.0"\n')
        
        project = await manager.create(
            name="Python Project",
            path=temp_project_dir,
        )
        
        assert project.config.language == "python"
        assert project.config.framework == "fastapi"
    
    @pytest.mark.asyncio
    async def test_auto_detect_node_project(self, manager, temp_project_dir):
        """Test auto-detection of Node.js project."""
        import json
        
        package = Path(temp_project_dir) / "package.json"
        package.write_text(json.dumps({
            "name": "test",
            "dependencies": {
                "next": "^14.0.0",
                "react": "^18.0.0",
            },
            "devDependencies": {
                "typescript": "^5.0.0",
            },
        }))
        
        project = await manager.create(
            name="Node Project",
            path=temp_project_dir,
        )
        
        assert project.config.language == "typescript"
        assert project.config.framework == "next"
