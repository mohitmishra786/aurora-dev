"""
External Research Tools for AURORA-DEV.

Provides real-time data from external APIs including GitHub,
PyPI, npm, and web search for the Research Agent.

Example usage:
    >>> github = GitHubSearchClient(token="ghp_xxx")
    >>> repos = await github.search_repositories("fastapi authentication")
    >>> advisories = await github.get_advisories("lodash")
"""
import asyncio
from typing import Any, Optional

import httpx

from aurora_dev.core.config import get_settings
from aurora_dev.core.logging import get_logger

logger = get_logger(__name__)


class GitHubSearchClient:
    """GitHub REST API client for repository and code search.
    
    Provides access to GitHub's search, advisory, and repository APIs
    for real-time technology research.
    """

    def __init__(self, token: Optional[str] = None) -> None:
        """Initialize with GitHub token.
        
        Args:
            token: GitHub Personal Access Token (optional, uses config if not provided).
        """
        settings = get_settings()
        self.token = token or settings.github.token
        self.base_url = settings.github.api_base_url
        self._headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            self._headers["Authorization"] = f"Bearer {self.token}"

    async def search_repositories(
        self,
        query: str,
        sort: str = "stars",
        per_page: int = 10,
    ) -> list[dict[str, Any]]:
        """Search GitHub repositories.
        
        Args:
            query: Search query string.
            sort: Sort field (stars, forks, updated).
            per_page: Number of results to return.
            
        Returns:
            List of repository info dicts with stars, forks, description.
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/search/repositories",
                    headers=self._headers,
                    params={
                        "q": query,
                        "sort": sort,
                        "order": "desc",
                        "per_page": per_page,
                    },
                )
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data.get("items", []):
                    results.append({
                        "name": item["full_name"],
                        "description": item.get("description", ""),
                        "stars": item["stargazers_count"],
                        "forks": item["forks_count"],
                        "language": item.get("language", "Unknown"),
                        "last_updated": item["updated_at"],
                        "url": item["html_url"],
                        "license": item.get("license", {}).get("spdx_id", "None"),
                        "open_issues": item["open_issues_count"],
                    })
                
                logger.debug(f"GitHub search: {len(results)} results for '{query}'")
                return results
                
        except httpx.HTTPStatusError as e:
            logger.error(f"GitHub API error: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"GitHub search failed: {e}")
            return []

    async def search_code(
        self,
        query: str,
        language: Optional[str] = None,
        per_page: int = 10,
    ) -> list[dict[str, Any]]:
        """Search code across GitHub repositories.
        
        Args:
            query: Code search query.
            language: Filter by programming language.
            per_page: Number of results.
            
        Returns:
            List of code search results.
        """
        search_query = query
        if language:
            search_query += f" language:{language}"
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/search/code",
                    headers=self._headers,
                    params={
                        "q": search_query,
                        "per_page": per_page,
                    },
                )
                response.raise_for_status()
                data = response.json()
                
                results = []
                for item in data.get("items", []):
                    results.append({
                        "name": item["name"],
                        "path": item["path"],
                        "repository": item["repository"]["full_name"],
                        "url": item["html_url"],
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"GitHub code search failed: {e}")
            return []

    async def get_advisories(
        self,
        package: str,
        ecosystem: str = "pip",
    ) -> list[dict[str, Any]]:
        """Fetch security advisories for a package.
        
        Args:
            package: Package name to check.
            ecosystem: Package ecosystem (pip, npm, go, etc.).
            
        Returns:
            List of security advisory dicts.
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    f"{self.base_url}/advisories",
                    headers=self._headers,
                    params={
                        "ecosystem": ecosystem,
                        "affects": package,
                        "per_page": 20,
                    },
                )
                response.raise_for_status()
                data = response.json()
                
                advisories = []
                for item in data if isinstance(data, list) else []:
                    advisories.append({
                        "ghsa_id": item.get("ghsa_id", ""),
                        "summary": item.get("summary", ""),
                        "severity": item.get("severity", "unknown"),
                        "published_at": item.get("published_at", ""),
                        "cve_id": item.get("cve_id"),
                        "url": item.get("html_url", ""),
                    })
                
                logger.debug(
                    f"Found {len(advisories)} advisories for {package}"
                )
                return advisories
                
        except Exception as e:
            logger.error(f"Advisory lookup failed for {package}: {e}")
            return []


class PackageRegistryClient:
    """Client for querying package registries (PyPI, npm).
    
    Provides download stats, version info, and dependency data.
    """

    async def get_pypi_info(self, package: str) -> dict[str, Any]:
        """Get package info from PyPI.
        
        Args:
            package: Python package name.
            
        Returns:
            Package information dict.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"https://pypi.org/pypi/{package}/json"
                )
                response.raise_for_status()
                data = response.json()
                info = data.get("info", {})
                
                return {
                    "name": info.get("name", package),
                    "version": info.get("version", ""),
                    "summary": info.get("summary", ""),
                    "author": info.get("author", ""),
                    "license": info.get("license", ""),
                    "home_page": info.get("home_page", ""),
                    "project_url": info.get("project_url", ""),
                    "requires_python": info.get("requires_python", ""),
                    "keywords": info.get("keywords", ""),
                    "classifiers": info.get("classifiers", [])[:5],
                }
                
        except Exception as e:
            logger.error(f"PyPI lookup failed for {package}: {e}")
            return {"name": package, "error": str(e)}

    async def get_npm_info(self, package: str) -> dict[str, Any]:
        """Get package info from npm registry.
        
        Args:
            package: npm package name.
            
        Returns:
            Package information dict.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"https://registry.npmjs.org/{package}"
                )
                response.raise_for_status()
                data = response.json()
                latest = data.get("dist-tags", {}).get("latest", "")
                latest_info = data.get("versions", {}).get(latest, {})
                
                return {
                    "name": data.get("name", package),
                    "version": latest,
                    "description": data.get("description", ""),
                    "license": latest_info.get("license", ""),
                    "homepage": latest_info.get("homepage", ""),
                    "repository": str(data.get("repository", {}).get("url", "")),
                    "keywords": data.get("keywords", [])[:10],
                    "maintainers": [
                        m.get("name", "") for m in data.get("maintainers", [])[:5]
                    ],
                }
                
        except Exception as e:
            logger.error(f"npm lookup failed for {package}: {e}")
            return {"name": package, "error": str(e)}


class WebSearchClient:
    """Simple web search client using httpx.
    
    Provides basic web search capability for research tasks.
    Uses DuckDuckGo Instant Answer API as a free, no-auth option.
    """

    async def search(
        self,
        query: str,
        max_results: int = 5,
    ) -> list[dict[str, str]]:
        """Perform a web search.
        
        Args:
            query: Search query.
            max_results: Maximum number of results.
            
        Returns:
            List of search result dicts with title, url, snippet.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.duckduckgo.com/",
                    params={
                        "q": query,
                        "format": "json",
                        "no_html": "1",
                        "skip_disambig": "1",
                    },
                )
                response.raise_for_status()
                data = response.json()
                
                results = []
                
                # Abstract (main answer)
                if data.get("Abstract"):
                    results.append({
                        "title": data.get("Heading", query),
                        "url": data.get("AbstractURL", ""),
                        "snippet": data.get("Abstract", ""),
                    })
                
                # Related topics
                for topic in data.get("RelatedTopics", [])[:max_results]:
                    if isinstance(topic, dict) and "Text" in topic:
                        results.append({
                            "title": topic.get("Text", "")[:100],
                            "url": topic.get("FirstURL", ""),
                            "snippet": topic.get("Text", ""),
                        })
                
                return results[:max_results]
                
        except Exception as e:
            logger.error(f"Web search failed: {e}")
            return []
