"""
Unit tests for GitWorktreeManager.

Tests worktree creation, removal, listing, and cleanup.
All Git operations are mocked to avoid requiring a real Git repository.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_repo():
    """Mock Git repository."""
    with patch("aurora_dev.tools.git_worktree.Repo") as mock:
        repo = MagicMock()
        repo.working_dir = "/tmp/test-repo"
        repo.bare = False
        mock.return_value = repo
        yield repo


class TestGitWorktreeManager:
    """Tests for GitWorktreeManager."""

    def test_initialization(self, mock_repo):
        """Test manager initializes with repo path."""
        from aurora_dev.tools.git_worktree import GitWorktreeManager
        
        manager = GitWorktreeManager(repo_path="/tmp/test-repo")
        
        assert manager.repo_path == "/tmp/test-repo"
        assert manager._agent_worktrees == {}

    @pytest.mark.asyncio
    async def test_create_worktree(self, mock_repo):
        """Test creating a worktree for an agent."""
        from aurora_dev.tools.git_worktree import GitWorktreeManager
        
        manager = GitWorktreeManager(repo_path="/tmp/test-repo")
        
        with patch("asyncio.create_subprocess_exec") as mock_proc:
            process = AsyncMock()
            process.returncode = 0
            process.communicate.return_value = (b"", b"")
            mock_proc.return_value = process
            
            # Mock branch check
            mock_repo.heads = []
            mock_repo.remotes = MagicMock()
            mock_repo.remotes.origin.refs = []
            
            path = await manager.create_worktree(
                branch_name="feature/test",
                agent_id="agent-1",
            )
            
            assert path is not None
            assert "agent-1" in manager._agent_worktrees

    @pytest.mark.asyncio
    async def test_remove_worktree(self, mock_repo):
        """Test removing a worktree."""
        from aurora_dev.tools.git_worktree import GitWorktreeManager
        
        manager = GitWorktreeManager(repo_path="/tmp/test-repo")
        
        with patch("asyncio.create_subprocess_exec") as mock_proc:
            process = AsyncMock()
            process.returncode = 0
            process.communicate.return_value = (b"", b"")
            mock_proc.return_value = process
            
            await manager.remove_worktree("/tmp/test-repo/.worktrees/test")
            
            mock_proc.assert_called_once()

    def test_get_worktree_path_unknown_agent(self, mock_repo):
        """Test getting worktree path for unknown agent returns None."""
        from aurora_dev.tools.git_worktree import GitWorktreeManager
        
        manager = GitWorktreeManager(repo_path="/tmp/test-repo")
        assert manager.get_worktree_path("unknown-agent") is None

    @pytest.mark.asyncio
    async def test_list_worktrees(self, mock_repo):
        """Test listing worktrees."""
        from aurora_dev.tools.git_worktree import GitWorktreeManager
        
        manager = GitWorktreeManager(repo_path="/tmp/test-repo")
        
        porcelain_output = (
            b"worktree /tmp/test-repo\n"
            b"HEAD abc123\n"
            b"branch refs/heads/main\n"
            b"\n"
        )
        
        with patch("asyncio.create_subprocess_exec") as mock_proc:
            process = AsyncMock()
            process.returncode = 0
            process.communicate.return_value = (porcelain_output, b"")
            mock_proc.return_value = process
            
            worktrees = await manager.list_worktrees()
            assert isinstance(worktrees, list)
