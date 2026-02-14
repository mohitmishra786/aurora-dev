"""
Merge Conflict Resolver for AURORA-DEV.

Handles detection and resolution of Git merge conflicts when
multiple agents modify overlapping files via worktrees.

Example usage:
    >>> resolver = MergeConflictResolver("/path/to/repo")
    >>> conflicts = await resolver.detect_conflicts("/path/to/worktree")
    >>> for conflict in conflicts:
    ...     await resolver.auto_resolve(conflict.file_path, strategy="theirs")
"""
import asyncio
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from aurora_dev.core.logging import get_logger

logger = get_logger(__name__)

try:
    import git
    GIT_AVAILABLE = True
except ImportError:
    GIT_AVAILABLE = False


class MergeStrategy(str, Enum):
    """Strategies for resolving merge conflicts."""
    OURS = "ours"
    THEIRS = "theirs"
    COMBINED = "combined"  # Attempt to keep both changes


@dataclass
class ConflictInfo:
    """Information about a merge conflict."""
    
    file_path: str
    ours_content: str = ""
    theirs_content: str = ""
    base_content: str = ""
    conflict_markers: list[dict[str, str]] = field(default_factory=list)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "file_path": self.file_path,
            "num_conflicts": len(self.conflict_markers),
            "ours_preview": self.ours_content[:200] if self.ours_content else "",
            "theirs_preview": self.theirs_content[:200] if self.theirs_content else "",
        }


@dataclass
class MergeResult:
    """Result from a merge operation."""
    
    success: bool
    merged_files: list[str] = field(default_factory=list)
    conflicts: list[ConflictInfo] = field(default_factory=list)
    error: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "merged_files": self.merged_files,
            "num_conflicts": len(self.conflicts),
            "conflicts": [c.to_dict() for c in self.conflicts],
            "error": self.error,
        }


class MergeConflictResolver:
    """Resolves Git merge conflicts for multi-agent workflows.
    
    Provides detection, analysis, and resolution of merge conflicts
    that arise when multiple agents work on overlapping files.
    """

    def __init__(self, repo_path: str) -> None:
        """Initialize the merge conflict resolver.
        
        Args:
            repo_path: Path to the main Git repository.
        """
        if not GIT_AVAILABLE:
            raise ImportError(
                "GitPython is not installed. "
                "Install it with: pip install gitpython"
            )
        
        self.repo_path = os.path.abspath(repo_path)
        self._repo = git.Repo(self.repo_path)
        
        logger.info(
            "MergeConflictResolver initialized",
            repo_path=self.repo_path,
        )

    async def merge_worktree(
        self,
        source_branch: str,
        target_branch: str = "main",
    ) -> MergeResult:
        """Merge a worktree branch into the target branch.
        
        Args:
            source_branch: Branch to merge from (typically an agent's worktree branch).
            target_branch: Branch to merge into (defaults to "main").
            
        Returns:
            MergeResult with merge outcome details.
        """
        try:
            # Checkout target branch
            process = await asyncio.create_subprocess_exec(
                "git", "checkout", target_branch,
                cwd=self.repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return MergeResult(
                    success=False,
                    error=f"Failed to checkout {target_branch}: {stderr.decode()}"
                )
            
            # Attempt merge
            process = await asyncio.create_subprocess_exec(
                "git", "merge", source_branch, "--no-ff",
                cwd=self.repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                # Merge succeeded without conflicts
                logger.info(
                    f"Merged {source_branch} into {target_branch} successfully"
                )
                return MergeResult(success=True)
            
            # Merge has conflicts - detect them
            conflicts = await self.detect_conflicts(self.repo_path)
            
            return MergeResult(
                success=False,
                conflicts=conflicts,
                error=f"Merge conflicts detected in {len(conflicts)} file(s)",
            )
            
        except Exception as e:
            logger.error(f"Merge failed: {e}")
            return MergeResult(success=False, error=str(e))

    async def detect_conflicts(
        self,
        repo_path: Optional[str] = None,
    ) -> list[ConflictInfo]:
        """Detect merge conflicts in the repository.
        
        Args:
            repo_path: Path to check for conflicts (defaults to main repo).
            
        Returns:
            List of ConflictInfo objects for each conflicting file.
        """
        check_path = repo_path or self.repo_path
        
        try:
            # Use git diff to find conflicted files
            process = await asyncio.create_subprocess_exec(
                "git", "diff", "--name-only", "--diff-filter=U",
                cwd=check_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logger.debug("No conflicts detected or not in merge state")
                return []
            
            conflicted_files = stdout.decode().strip().split("\n")
            conflicted_files = [f for f in conflicted_files if f.strip()]
            
            conflicts = []
            for file_path in conflicted_files:
                conflict = await self._parse_conflict(
                    os.path.join(check_path, file_path),
                    file_path,
                )
                if conflict:
                    conflicts.append(conflict)
            
            logger.info(f"Detected {len(conflicts)} conflicting file(s)")
            return conflicts
            
        except Exception as e:
            logger.error(f"Conflict detection failed: {e}")
            return []

    async def _parse_conflict(
        self,
        full_path: str,
        relative_path: str,
    ) -> Optional[ConflictInfo]:
        """Parse conflict markers in a file.
        
        Args:
            full_path: Absolute path to the conflicted file.
            relative_path: Relative path for display.
            
        Returns:
            ConflictInfo with parsed conflict details.
        """
        try:
            with open(full_path, "r") as f:
                content = f.read()
        except FileNotFoundError:
            return None
        
        # Parse conflict markers: <<<<<<<, =======, >>>>>>>
        conflict_pattern = re.compile(
            r'<<<<<<<\s*(.*?)\n(.*?)=======\n(.*?)>>>>>>>\s*(.*?)\n',
            re.DOTALL,
        )
        
        markers = []
        for match in conflict_pattern.finditer(content):
            markers.append({
                "ours_label": match.group(1).strip(),
                "ours_content": match.group(2),
                "theirs_content": match.group(3),
                "theirs_label": match.group(4).strip(),
            })
        
        if not markers:
            return None
        
        return ConflictInfo(
            file_path=relative_path,
            ours_content=markers[0]["ours_content"] if markers else "",
            theirs_content=markers[0]["theirs_content"] if markers else "",
            conflict_markers=markers,
        )

    async def auto_resolve(
        self,
        file_path: str,
        strategy: MergeStrategy = MergeStrategy.THEIRS,
    ) -> bool:
        """Automatically resolve conflicts in a file.
        
        Args:
            file_path: Path to the conflicted file.
            strategy: Resolution strategy to use.
            
        Returns:
            True if resolution was successful.
        """
        full_path = os.path.join(self.repo_path, file_path)
        
        try:
            with open(full_path, "r") as f:
                content = f.read()
            
            # Apply resolution strategy
            conflict_pattern = re.compile(
                r'<<<<<<<\s*.*?\n(.*?)=======\n(.*?)>>>>>>>\s*.*?\n',
                re.DOTALL,
            )
            
            if strategy == MergeStrategy.OURS:
                resolved = conflict_pattern.sub(r'\1', content)
            elif strategy == MergeStrategy.THEIRS:
                resolved = conflict_pattern.sub(r'\2', content)
            elif strategy == MergeStrategy.COMBINED:
                # Keep both sides
                resolved = conflict_pattern.sub(r'\1\2', content)
            else:
                logger.error(f"Unknown strategy: {strategy}")
                return False
            
            # Write resolved content
            with open(full_path, "w") as f:
                f.write(resolved)
            
            # Stage the resolved file
            process = await asyncio.create_subprocess_exec(
                "git", "add", file_path,
                cwd=self.repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            
            logger.info(
                f"Resolved conflict in {file_path}",
                strategy=strategy.value,
            )
            return True
            
        except Exception as e:
            logger.error(f"Conflict resolution failed for {file_path}: {e}")
            return False

    async def abort_merge(self) -> bool:
        """Abort the current merge operation.
        
        Returns:
            True if abort was successful.
        """
        try:
            process = await asyncio.create_subprocess_exec(
                "git", "merge", "--abort",
                cwd=self.repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await process.communicate()
            
            logger.info("Merge aborted")
            return process.returncode == 0
            
        except Exception as e:
            logger.error(f"Failed to abort merge: {e}")
            return False

    def get_conflict_diff(self, file_path: str) -> Optional[str]:
        """Get a readable diff of conflict markers.
        
        Args:
            file_path: Relative path to the conflicted file.
            
        Returns:
            Formatted diff string or None if file not found.
        """
        full_path = os.path.join(self.repo_path, file_path)
        
        try:
            with open(full_path, "r") as f:
                content = f.read()
            
            lines = content.split("\n")
            diff_lines = []
            in_conflict = False
            section = None
            
            for line in lines:
                if line.startswith("<<<<<<<"):
                    in_conflict = True
                    section = "ours"
                    diff_lines.append(f"--- CONFLICT START ---")
                elif line.startswith("======="):
                    section = "theirs"
                    diff_lines.append(f"--- vs ---")
                elif line.startswith(">>>>>>>"):
                    in_conflict = False
                    section = None
                    diff_lines.append(f"--- CONFLICT END ---")
                elif in_conflict:
                    prefix = "- " if section == "ours" else "+ "
                    diff_lines.append(f"{prefix}{line}")
                else:
                    diff_lines.append(f"  {line}")
            
            return "\n".join(diff_lines)
            
        except FileNotFoundError:
            return None
