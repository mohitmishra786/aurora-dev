"""
Unit tests for research tools (GitHub, PyPI, npm, web search).
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


class TestGitHubSearchClient:
    """Tests for GitHubSearchClient."""

    def test_initialization(self):
        """Test client initializes without errors."""
        from aurora_dev.tools.research_tools import GitHubSearchClient
        client = GitHubSearchClient()
        assert client is not None

    @pytest.mark.asyncio
    async def test_search_repositories(self):
        """Test searching GitHub repositories."""
        from aurora_dev.tools.research_tools import GitHubSearchClient
        
        client = GitHubSearchClient()
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "full_name": "test/repo",
                    "description": "A test repo",
                    "stargazers_count": 100,
                    "forks_count": 10,
                    "html_url": "https://github.com/test/repo",
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=MagicMock(get=AsyncMock(return_value=mock_response))
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
            
            results = await client.search_repositories("test")
            assert isinstance(results, list)


class TestPackageRegistryClient:
    """Tests for PackageRegistryClient."""

    def test_initialization(self):
        """Test client initializes without errors."""
        from aurora_dev.tools.research_tools import PackageRegistryClient
        client = PackageRegistryClient()
        assert client is not None

    @pytest.mark.asyncio
    async def test_get_pypi_info(self):
        """Test getting PyPI package info."""
        from aurora_dev.tools.research_tools import PackageRegistryClient
        
        client = PackageRegistryClient()
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "info": {
                "name": "fastapi",
                "version": "0.109.0",
                "summary": "A modern web framework",
            },
        }
        mock_response.raise_for_status = MagicMock()
        
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=MagicMock(get=AsyncMock(return_value=mock_response))
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)
            
            result = await client.get_pypi_info("fastapi")
            assert isinstance(result, dict)


class TestWebSearchClient:
    """Tests for WebSearchClient."""

    def test_initialization(self):
        """Test client initializes without errors."""
        from aurora_dev.tools.research_tools import WebSearchClient
        client = WebSearchClient()
        assert client is not None
