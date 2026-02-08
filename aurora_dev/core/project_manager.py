"""
Multi-project support for AURORA-DEV.

Enables concurrent management of multiple projects with
isolated memory, configuration, and cost tracking.

Example usage:
    >>> manager = ProjectManager()
    >>> project = await manager.create(
    ...     name="my-ecommerce",
    ...     path="/home/user/projects/ecommerce",
    ... )
    >>> await manager.switch("my-ecommerce")
"""
import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from aurora_dev.core.logging import get_logger


logger = get_logger(__name__)


class ProjectStatus(Enum):
    """Status of a project."""
    
    IDLE = "idle"
    ACTIVE = "active"
    BUILDING = "building"
    TESTING = "testing"
    DEPLOYING = "deploying"
    PAUSED = "paused"
    ARCHIVED = "archived"


@dataclass
class ProjectConfig:
    """
    Configuration for a project.
    
    Attributes:
        language: Primary programming language.
        framework: Main framework (e.g., FastAPI, React).
        database: Database type if applicable.
        deployment: Deployment target (e.g., Docker, K8s).
        custom_settings: Additional project-specific settings.
    """
    
    language: str = "python"
    framework: Optional[str] = None
    database: Optional[str] = None
    deployment: Optional[str] = None
    custom_settings: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "language": self.language,
            "framework": self.framework,
            "database": self.database,
            "deployment": self.deployment,
            "custom_settings": self.custom_settings,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectConfig":
        """Create from dictionary."""
        return cls(
            language=data.get("language", "python"),
            framework=data.get("framework"),
            database=data.get("database"),
            deployment=data.get("deployment"),
            custom_settings=data.get("custom_settings", {}),
        )


@dataclass
class CostTracker:
    """
    Per-project cost tracking.
    
    Tracks token usage and API costs for budget management.
    """
    
    input_tokens: int = 0
    output_tokens: int = 0
    total_cost_usd: float = 0.0
    daily_limit_usd: float = 100.0
    
    # Cost per 1M tokens
    INPUT_COST_PER_1M: float = 3.0  # Claude Sonnet
    OUTPUT_COST_PER_1M: float = 15.0
    
    def add_usage(self, input_tokens: int, output_tokens: int) -> None:
        """Add token usage and update cost."""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens
        
        input_cost = (input_tokens / 1_000_000) * self.INPUT_COST_PER_1M
        output_cost = (output_tokens / 1_000_000) * self.OUTPUT_COST_PER_1M
        self.total_cost_usd += input_cost + output_cost
    
    def is_over_budget(self) -> bool:
        """Check if daily budget exceeded."""
        return self.total_cost_usd >= self.daily_limit_usd
    
    def remaining_budget(self) -> float:
        """Get remaining daily budget."""
        return max(0, self.daily_limit_usd - self.total_cost_usd)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_cost_usd": self.total_cost_usd,
            "daily_limit_usd": self.daily_limit_usd,
        }


@dataclass
class Project:
    """
    Represents a managed project.
    
    Attributes:
        id: Unique project identifier.
        name: Human-readable project name.
        path: Filesystem path to project root.
        status: Current project status.
        config: Project configuration.
        cost_tracker: Per-project cost tracking.
        created_at: Creation timestamp.
        updated_at: Last update timestamp.
        metadata: Additional metadata.
    """
    
    id: str
    name: str
    path: Path
    status: ProjectStatus
    config: ProjectConfig
    cost_tracker: CostTracker
    created_at: datetime
    updated_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "path": str(self.path),
            "status": self.status.value,
            "config": self.config.to_dict(),
            "cost_tracker": self.cost_tracker.to_dict(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Project":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            name=data["name"],
            path=Path(data["path"]),
            status=ProjectStatus(data["status"]),
            config=ProjectConfig.from_dict(data["config"]),
            cost_tracker=CostTracker(**data.get("cost_tracker", {})),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ProjectContext:
    """
    Context for project-scoped operations.
    
    Used by agents to access project-specific settings
    and resources without global state pollution.
    
    Attributes:
        project_id: Current project ID.
        project_name: Project name.
        project_path: Project root path.
        config: Project configuration.
        memory_prefix: Redis key prefix for memory isolation.
        worktree_path: Git worktree path if parallel development.
    """
    
    project_id: str
    project_name: str
    project_path: Path
    config: ProjectConfig
    memory_prefix: str
    worktree_path: Optional[Path] = None
    
    def get_memory_key(self, key: str) -> str:
        """Get namespaced memory key."""
        return f"{self.memory_prefix}:{key}"
    
    def get_cache_key(self, key: str) -> str:
        """Get namespaced cache key."""
        return f"cache:{self.memory_prefix}:{key}"


class ProjectManager:
    """
    Manager for multi-project support.
    
    Handles project creation, switching, and lifecycle
    with isolated memory and cost tracking.
    
    Example:
        >>> manager = ProjectManager()
        >>> project = await manager.create(
        ...     name="ecommerce",
        ...     path="/projects/ecommerce",
        ...     config=ProjectConfig(language="python", framework="fastapi"),
        ... )
        >>> await manager.switch("ecommerce")
        >>> current = manager.get_current()
    """
    
    def __init__(self):
        """Initialize project manager."""
        self._projects: dict[str, Project] = {}
        self._current_project_id: Optional[str] = None
        self._logger = get_logger(__name__)
    
    async def create(
        self,
        name: str,
        path: str,
        config: Optional[ProjectConfig] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> Project:
        """
        Create a new project.
        
        Args:
            name: Project name (used as ID).
            path: Filesystem path to project.
            config: Optional project configuration.
            metadata: Optional additional metadata.
            
        Returns:
            Created Project instance.
        """
        # Generate ID from name
        project_id = name.lower().replace(" ", "-")
        
        if project_id in self._projects:
            raise ValueError(f"Project already exists: {project_id}")
        
        project_path = Path(path)
        
        # Auto-detect configuration if not provided
        if config is None:
            config = await self._detect_config(project_path)
        
        now = datetime.now()
        
        project = Project(
            id=project_id,
            name=name,
            path=project_path,
            status=ProjectStatus.IDLE,
            config=config,
            cost_tracker=CostTracker(),
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
        )
        
        self._projects[project_id] = project
        
        self._logger.info(
            f"Created project: {name}",
            extra={"project_id": project_id, "path": str(path)},
        )
        
        return project
    
    async def switch(self, project_id: str) -> ProjectContext:
        """
        Switch to a different project.
        
        Args:
            project_id: ID of project to switch to.
            
        Returns:
            ProjectContext for the new active project.
        """
        if project_id not in self._projects:
            raise ValueError(f"Project not found: {project_id}")
        
        # Deactivate current project
        if self._current_project_id:
            current = self._projects.get(self._current_project_id)
            if current:
                current.status = ProjectStatus.IDLE
                current.updated_at = datetime.now()
        
        # Activate new project
        project = self._projects[project_id]
        project.status = ProjectStatus.ACTIVE
        project.updated_at = datetime.now()
        self._current_project_id = project_id
        
        self._logger.info(f"Switched to project: {project_id}")
        
        return self.get_context(project_id)
    
    def get_context(self, project_id: Optional[str] = None) -> ProjectContext:
        """
        Get context for a project.
        
        Args:
            project_id: Project ID (uses current if not specified).
            
        Returns:
            ProjectContext for the project.
        """
        pid = project_id or self._current_project_id
        
        if not pid:
            raise ValueError("No project specified and no current project")
        
        project = self._projects.get(pid)
        if not project:
            raise ValueError(f"Project not found: {pid}")
        
        return ProjectContext(
            project_id=project.id,
            project_name=project.name,
            project_path=project.path,
            config=project.config,
            memory_prefix=f"aurora:project:{project.id}",
        )
    
    def get_current(self) -> Optional[Project]:
        """Get the current active project."""
        if not self._current_project_id:
            return None
        return self._projects.get(self._current_project_id)
    
    def list_projects(self) -> list[Project]:
        """List all projects."""
        return list(self._projects.values())
    
    def list_active(self) -> list[Project]:
        """List active (non-idle, non-archived) projects."""
        return [
            p for p in self._projects.values()
            if p.status not in [ProjectStatus.IDLE, ProjectStatus.ARCHIVED]
        ]
    
    async def archive(self, project_id: str) -> None:
        """
        Archive a project.
        
        Args:
            project_id: ID of project to archive.
        """
        if project_id not in self._projects:
            raise ValueError(f"Project not found: {project_id}")
        
        project = self._projects[project_id]
        project.status = ProjectStatus.ARCHIVED
        project.updated_at = datetime.now()
        
        # Clear current if archiving current
        if self._current_project_id == project_id:
            self._current_project_id = None
        
        self._logger.info(f"Archived project: {project_id}")
    
    async def delete(self, project_id: str) -> None:
        """
        Delete a project from manager.
        
        Note: This does not delete files on disk.
        
        Args:
            project_id: ID of project to delete.
        """
        if project_id not in self._projects:
            raise ValueError(f"Project not found: {project_id}")
        
        del self._projects[project_id]
        
        if self._current_project_id == project_id:
            self._current_project_id = None
        
        self._logger.info(f"Deleted project: {project_id}")
    
    def add_usage(
        self,
        project_id: str,
        input_tokens: int,
        output_tokens: int,
    ) -> None:
        """
        Add token usage to project's cost tracker.
        
        Args:
            project_id: Project ID.
            input_tokens: Input tokens used.
            output_tokens: Output tokens used.
        """
        project = self._projects.get(project_id)
        if project:
            project.cost_tracker.add_usage(input_tokens, output_tokens)
    
    def get_cost_summary(self, project_id: str) -> dict[str, Any]:
        """
        Get cost summary for a project.
        
        Args:
            project_id: Project ID.
            
        Returns:
            Cost summary dictionary.
        """
        project = self._projects.get(project_id)
        if not project:
            return {}
        
        tracker = project.cost_tracker
        return {
            "total_cost_usd": tracker.total_cost_usd,
            "input_tokens": tracker.input_tokens,
            "output_tokens": tracker.output_tokens,
            "remaining_budget": tracker.remaining_budget(),
            "is_over_budget": tracker.is_over_budget(),
        }
    
    async def _detect_config(self, path: Path) -> ProjectConfig:
        """
        Auto-detect project configuration from files.
        
        Looks for common configuration files to determine
        language, framework, and other settings.
        """
        config = ProjectConfig()
        
        # Python detection
        if (path / "pyproject.toml").exists() or (path / "requirements.txt").exists():
            config.language = "python"
            
            # Framework detection
            try:
                if (path / "pyproject.toml").exists():
                    content = (path / "pyproject.toml").read_text()
                    if "fastapi" in content.lower():
                        config.framework = "fastapi"
                    elif "django" in content.lower():
                        config.framework = "django"
                    elif "flask" in content.lower():
                        config.framework = "flask"
            except Exception:
                pass
        
        # Node.js detection
        elif (path / "package.json").exists():
            config.language = "javascript"
            
            try:
                import json
                pkg = json.loads((path / "package.json").read_text())
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                
                if "next" in deps:
                    config.framework = "next"
                elif "react" in deps:
                    config.framework = "react"
                elif "vue" in deps:
                    config.framework = "vue"
                elif "express" in deps:
                    config.framework = "express"
                
                if "typescript" in deps:
                    config.language = "typescript"
            except Exception:
                pass
        
        # Go detection
        elif (path / "go.mod").exists():
            config.language = "go"
        
        # Rust detection
        elif (path / "Cargo.toml").exists():
            config.language = "rust"
        
        # Docker detection
        if (path / "Dockerfile").exists():
            config.deployment = "docker"
        elif (path / "docker-compose.yml").exists():
            config.deployment = "docker-compose"
        
        # Kubernetes detection
        if (path / "k8s").exists() or (path / "kubernetes").exists():
            config.deployment = "kubernetes"
        
        self._logger.debug(
            f"Auto-detected config: {config.language}/{config.framework}"
        )
        
        return config


# Global project manager instance
_manager: Optional[ProjectManager] = None


def get_project_manager() -> ProjectManager:
    """Get the global project manager instance."""
    global _manager
    if _manager is None:
        _manager = ProjectManager()
    return _manager
