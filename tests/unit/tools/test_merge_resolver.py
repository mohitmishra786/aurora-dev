"""
Unit tests for MergeConflictResolver.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestMergeConflictResolver:
    """Tests for MergeConflictResolver."""

    @pytest.fixture
    def resolver(self):
        """Create a resolver with mocked Git."""
        with patch("aurora_dev.tools.merge_resolver.git") as mock_git, \
             patch("aurora_dev.tools.merge_resolver.logger"):
            mock_git.Repo.return_value.working_dir = "/tmp/test-repo"
            from aurora_dev.tools.merge_resolver import MergeConflictResolver
            return MergeConflictResolver(repo_path="/tmp/test-repo")

    @pytest.mark.asyncio
    async def test_detect_conflicts_none(self, resolver):
        """Test detecting no conflicts."""
        with patch("asyncio.create_subprocess_exec") as mock_proc:
            process = AsyncMock()
            process.returncode = 0
            process.communicate.return_value = (b"", b"")
            mock_proc.return_value = process
            
            conflicts = await resolver.detect_conflicts()
            assert conflicts == []

    @pytest.mark.asyncio
    async def test_detect_conflicts_found(self, resolver):
        """Test detecting conflicts in files."""
        with patch("asyncio.create_subprocess_exec") as mock_proc:
            process = AsyncMock()
            process.returncode = 0
            process.communicate.return_value = (b"file1.py\nfile2.py\n", b"")
            mock_proc.return_value = process
            
            # Mock _parse_conflict to return mock conflict info for each file
            mock_conflict = MagicMock()
            resolver._parse_conflict = AsyncMock(return_value=mock_conflict)
            
            conflicts = await resolver.detect_conflicts()
            assert len(conflicts) == 2

    @pytest.mark.asyncio
    async def test_auto_resolve_theirs(self, resolver):
        """Test auto-resolving with 'theirs' strategy."""
        conflict_content = (
            "before\n"
            "<<<<<<< HEAD\n"
            "our change\n"
            "=======\n"
            "their change\n"
            ">>>>>>> feature\n"
            "after\n"
        )
        
        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__ = lambda s: s
            mock_open.return_value.__exit__ = MagicMock(return_value=False)
            mock_open.return_value.read = MagicMock(return_value=conflict_content)
            mock_open.return_value.write = MagicMock()
            
            with patch("asyncio.create_subprocess_exec") as mock_proc:
                process = AsyncMock()
                process.returncode = 0
                process.communicate.return_value = (b"", b"")
                mock_proc.return_value = process
                
                from aurora_dev.tools.merge_resolver import MergeStrategy
                result = await resolver.auto_resolve(
                    "file.py",
                    strategy=MergeStrategy.THEIRS,
                )
                assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_abort_merge(self, resolver):
        """Test aborting a merge."""
        with patch("asyncio.create_subprocess_exec") as mock_proc:
            process = AsyncMock()
            process.returncode = 0
            process.communicate.return_value = (b"", b"")
            mock_proc.return_value = process
            
            result = await resolver.abort_merge()
            assert isinstance(result, bool)
