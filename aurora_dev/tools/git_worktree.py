"""
Git Worktree Manager for AURORA-DEV.

Provides parallel execution support by managing Git worktrees,
allowing multiple agents to work on different features simultaneously
without file locking issues.

Example usage:
    >>> manager = GitWorktreeManager("/path/to/repo")
    >>> worktree_path = await manager.create_worktree("feature/auth", "agent-backend-1")
    >>> # Agent works in worktree_path...
    >>> await manager.remove_worktree(worktree_path)
"""
import asyncio
import os
import shutil
from pathlib import Path
from typing import Any, Optional

from aurora_dev.core.logging import get_logger

logger = get_logger(__name__)

try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False


class WorktreeInfo:
    """Information about a Git worktree."""

    def __init__(
        self,
        path: str,
        branch: str,
        agent_id: Optional[str] = None,
        is_main: bool = False,
    ) -> None:
        self.path = path
        self.branch = branch
        self.agent_id = agent_id
        self.is_main = is_main

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "path": self.path,
            "branch": self.branch,
            "agent_id": self.agent_id,
            "is_main": self.is_main,
        }


class GitWorktreeManager:
    """Manages Git worktrees for parallel agent execution.
    
    Each agent gets its own worktree (a separate checkout of the repo)
    so they can modify files independently without conflicts.
    
    Attributes:
        repo_path: Path to the main Git repository.
        worktree_base: Directory where worktrees are created.
    """

    def __init__(
        self,
        repo_path: str,
        worktree_base: Optional[str] = None,
    ) -> None:
        """Initialize the worktree manager.
        
        Args:
            repo_path: Path to the main Git repository.
            worktree_base: Base directory for worktrees (defaults to repo_path/.worktrees).
        """
        if not GIT_AVAILABLE:
            raise ImportError(
                "GitPython is not installed. "
                "Install it with: pip install gitpython"
            )
        
        self.repo_path = os.path.abspath(repo_path)
        self.worktree_base = worktree_base or os.path.join(
            self.repo_path, ".worktrees"
        )
        self._repo = git.Repo(self.repo_path)
        self._agent_worktrees: dict[str, str] = {}  # agent_id -> worktree_path
        
        # Ensure worktree base directory exists
        os.makedirs(self.worktree_base, exist_ok=True)
        
        logger.info(
            "GitWorktreeManager initialized",
            repo_path=self.repo_path,
            worktree_base=self.worktree_base,
        )

    async def create_worktree(
        self,
        branch_name: str,
        agent_id: Optional[str] = None,
        base_branch: str = "main",
    ) -> str:
        """Create a new Git worktree for an agent.
        
        Args:
            branch_name: Name of the branch for the worktree.
            agent_id: Optional agent identifier for tracking.
            base_branch: Branch to base the new worktree on.
            
        Returns:
            Absolute path to the created worktree.
            
        Raises:
            RuntimeError: If worktree creation fails.
        """
        # Sanitize branch name
        safe_branch = branch_name.replace("/", "-").replace(" ", "-")
        worktree_path = os.path.join(self.worktree_base, safe_branch)
        
        if os.path.exists(worktree_path):
            logger.warning(
                f"Worktree path already exists: {worktree_path}",
            )
            if agent_id:
                self._agent_worktrees[agent_id] = worktree_path
            return worktree_path
        
        try:
            # Create the branch if it doesn't exist
            existing_branches = [b.name for b in self._repo.branches]
            if branch_name not in existing_branches:
                # Create branch from base
                base_ref = self._repo.refs[base_branch] if base_branch in [
                    r.name for r in self._repo.refs
                ] else self._repo.head.commit
                self._repo.create_head(branch_name, base_ref)
            
            # Run git worktree add
            process = await asyncio.create_subprocess_exec(
                "git", "worktree", "add", worktree_path, branch_name,
                cwd=self.repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                raise RuntimeError(
                    f"Failed to create worktree: {error_msg}"
                )
            
            if agent_id:
                self._agent_worktrees[agent_id] = worktree_path
            
            logger.info(
                "Created worktree",
                path=worktree_path,
                branch=branch_name,
                agent_id=agent_id,
            )
            
            return worktree_path
            
        except Exception as e:
            logger.error(f"Worktree creation failed: {e}")
            raise

    async def remove_worktree(
        self,
        worktree_path: str,
        force: bool = False,
    ) -> None:
        """Remove a Git worktree.
        
        Args:
            worktree_path: Path to the worktree to remove.
            force: Force removal even with uncommitted changes.
        """
        try:
            cmd = ["git", "worktree", "remove", worktree_path]
            if force:
                cmd.append("--force")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=self.repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.warning(f"Worktree removal issue: {error_msg}")
                # Try force cleanup if directory exists
                if os.path.exists(worktree_path):
                    shutil.rmtree(worktree_path, ignore_errors=True)
            
            # Remove from tracking
            agents_to_remove = [
                aid for aid, path in self._agent_worktrees.items()
                if path == worktree_path
            ]
            for aid in agents_to_remove:
                del self._agent_worktrees[aid]
            
            logger.info("Removed worktree", path=worktree_path)
            
        except Exception as e:
            logger.error(f"Worktree removal failed: {e}")
            raise

    async def list_worktrees(self) -> list[WorktreeInfo]:
        """List all active worktrees.
        
        Returns:
            List of WorktreeInfo objects for each active worktree.
        """
        try:
            process = await asyncio.create_subprocess_exec(
                "git", "worktree", "list", "--porcelain",
                cwd=self.repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Failed to list worktrees: {stderr.decode()}")
                return []
            
            worktrees = []
            current_path = None
            current_branch = ""
            
            for line in stdout.decode().strip().split("\n"):
                line = line.strip()
                if not line:
                    if current_path:
                        # Find agent for this worktree
                        agent_id = None
                        for aid, wpath in self._agent_worktrees.items():
                            if wpath == current_path:
                                agent_id = aid
                                break
                        
                        worktrees.append(WorktreeInfo(
                            path=current_path,
                            branch=current_branch,
                            agent_id=agent_id,
                            is_main=(current_path == self.repo_path),
                        ))
                    current_path = None
                    current_branch = ""
                elif line.startswith("worktree "):
                    current_path = line[len("worktree "):]
                elif line.startswith("branch "):
                    current_branch = line[len("branch refs/heads/"):]
            
            # Handle last entry
            if current_path:
                agent_id = None
                for aid, wpath in self._agent_worktrees.items():
                    if wpath == current_path:
                        agent_id = aid
                        break
                worktrees.append(WorktreeInfo(
                    path=current_path,
                    branch=current_branch,
                    agent_id=agent_id,
                    is_main=(current_path == self.repo_path),
                ))
            
            return worktrees
            
        except Exception as e:
            logger.error(f"Failed to list worktrees: {e}")
            return []

    def get_worktree_path(self, agent_id: str) -> Optional[str]:
        """Get the worktree path assigned to an agent.
        
        Args:
            agent_id: The agent's identifier.
            
        Returns:
            Worktree path if assigned, None otherwise.
        """
        return self._agent_worktrees.get(agent_id)

    async def cleanup_all(self) -> None:
        """Remove all managed worktrees and clean up.
        
        Used during shutdown or project completion.
        """
        worktrees = await self.list_worktrees()
        for wt in worktrees:
            if not wt.is_main:
                await self.remove_worktree(wt.path, force=True)
        
        # Prune stale worktree references
        process = await asyncio.create_subprocess_exec(
            "git", "worktree", "prune",
            cwd=self.repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await process.communicate()
        
        self._agent_worktrees.clear()
        logger.info("Cleaned up all worktrees")
