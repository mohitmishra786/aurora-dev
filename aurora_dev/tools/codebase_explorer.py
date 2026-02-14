"""
Proactive Codebase Explorer for AURORA-DEV agents.

Agents use this to scan and understand existing code patterns,
dependencies, and conventions before making modifications.
This ensures agents don't duplicate existing utilities or
introduce conflicting patterns.

Gap B2: Missing proactive codebase exploration.
"""
import asyncio
import os
import re
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class CodebaseInsight:
    """An insight discovered from exploring the codebase."""
    
    category: str  # "pattern", "dependency", "convention", "utility"
    description: str
    file_path: str = ""
    line_range: tuple[int, int] = (0, 0)
    confidence: float = 1.0
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "category": self.category,
            "description": self.description,
            "file_path": self.file_path,
            "line_range": list(self.line_range),
            "confidence": self.confidence,
        }


class CodebaseExplorer:
    """Proactive codebase exploration for agents.
    
    Before modifying code, agents should explore the codebase to:
    1. Identify existing patterns and conventions
    2. Find reusable utilities and helpers
    3. Understand dependency relationships
    4. Detect naming conventions and code style
    
    Example:
        >>> explorer = CodebaseExplorer("/path/to/repo")
        >>> insights = await explorer.explore("authentication")
    """
    
    IGNORE_DIRS = {
        ".git", "__pycache__", "node_modules", ".venv",
        "venv", ".tox", ".mypy_cache", "dist", "build",
    }
    
    def __init__(self, repo_path: str) -> None:
        self._repo_path = Path(repo_path)
        self._file_index: dict[str, list[str]] = {}
        self._insights_cache: dict[str, list[CodebaseInsight]] = {}
    
    async def explore(
        self,
        topic: str,
        file_extensions: Optional[list[str]] = None,
        max_files: int = 100,
    ) -> list[CodebaseInsight]:
        """Explore the codebase for patterns related to a topic.
        
        Args:
            topic: What to look for (e.g., "authentication", "database").
            file_extensions: File types to scan (default: .py, .ts, .js).
            max_files: Maximum files to examine.
            
        Returns:
            List of insights discovered.
        """
        if topic in self._insights_cache:
            return self._insights_cache[topic]
        
        extensions = file_extensions or [".py", ".ts", ".js", ".tsx", ".jsx"]
        insights: list[CodebaseInsight] = []
        
        # 1. Find relevant files
        relevant_files = await self._find_relevant_files(
            topic, extensions, max_files,
        )
        
        # 2. Analyze patterns
        for file_path in relevant_files:
            try:
                file_insights = await self._analyze_file(file_path, topic)
                insights.extend(file_insights)
            except Exception as e:
                logger.debug(f"Error analyzing {file_path}: {e}")
        
        # 3. Detect conventions
        convention_insights = await self._detect_conventions(extensions)
        insights.extend(convention_insights)
        
        self._insights_cache[topic] = insights
        return insights
    
    async def _find_relevant_files(
        self,
        topic: str,
        extensions: list[str],
        max_files: int,
    ) -> list[Path]:
        """Find files relevant to the topic using grep."""
        relevant: list[Path] = []
        
        try:
            process = await asyncio.create_subprocess_exec(
                "grep", "-rl", "--include=*.py", "--include=*.ts",
                "--include=*.js", topic, str(self._repo_path),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await process.communicate()
            
            for line in stdout.decode().strip().split("\n"):
                if line and len(relevant) < max_files:
                    relevant.append(Path(line))
                    
        except Exception:
            # Fallback: walk directory
            count = 0
            for root, dirs, files in os.walk(self._repo_path):
                dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
                for f in files:
                    if any(f.endswith(ext) for ext in extensions):
                        relevant.append(Path(root) / f)
                        count += 1
                        if count >= max_files:
                            break
                if count >= max_files:
                    break
        
        return relevant
    
    async def _analyze_file(
        self,
        file_path: Path,
        topic: str,
    ) -> list[CodebaseInsight]:
        """Analyze a single file for patterns and utilities."""
        insights: list[CodebaseInsight] = []
        
        try:
            content = file_path.read_text(errors="ignore")
        except Exception:
            return insights
        
        lines = content.split("\n")
        
        # Detect utility functions
        for i, line in enumerate(lines):
            if re.match(r"^(def|async def|class) ", line):
                name = line.split("(")[0].split()[-1] if "(" in line else ""
                if name and topic.lower() in name.lower():
                    insights.append(CodebaseInsight(
                        category="utility",
                        description=f"Found '{name}' related to '{topic}'",
                        file_path=str(file_path),
                        line_range=(i + 1, i + 1),
                    ))
        
        # Detect import patterns
        for i, line in enumerate(lines):
            if "import" in line and topic.lower() in line.lower():
                insights.append(CodebaseInsight(
                    category="dependency",
                    description=f"Import related to '{topic}': {line.strip()}",
                    file_path=str(file_path),
                    line_range=(i + 1, i + 1),
                ))
        
        return insights
    
    async def _detect_conventions(
        self,
        extensions: list[str],
    ) -> list[CodebaseInsight]:
        """Detect coding conventions from the codebase."""
        insights: list[CodebaseInsight] = []
        
        # Detect test naming convention
        test_files = list(self._repo_path.rglob("test_*.py"))
        test_files_alt = list(self._repo_path.rglob("*_test.py"))
        
        if len(test_files) > len(test_files_alt):
            insights.append(CodebaseInsight(
                category="convention",
                description="Test naming convention: test_*.py (prefix style)",
                confidence=0.9,
            ))
        elif test_files_alt:
            insights.append(CodebaseInsight(
                category="convention",
                description="Test naming convention: *_test.py (suffix style)",
                confidence=0.9,
            ))
        
        # Detect if project uses type hints (Python)
        sample_py = list(self._repo_path.rglob("*.py"))[:20]
        type_hint_count = 0
        for f in sample_py:
            try:
                content = f.read_text(errors="ignore")
                if "->" in content or ": str" in content or ": int" in content:
                    type_hint_count += 1
            except Exception:
                pass
        
        if type_hint_count > len(sample_py) * 0.5:
            insights.append(CodebaseInsight(
                category="convention",
                description="Project uses type hints extensively",
                confidence=0.8,
            ))
        
        return insights
    
    async def find_similar_implementations(
        self,
        description: str,
        language: str = "python",
    ) -> list[dict[str, Any]]:
        """Find existing implementations similar to what's being built.
        
        Args:
            description: What the new implementation does.
            language: Target language.
            
        Returns:
            List of similar existing implementations.
        """
        ext = ".py" if language == "python" else ".ts"
        keywords = description.lower().split()[:5]
        
        similar: list[dict[str, Any]] = []
        
        for keyword in keywords:
            files = await self._find_relevant_files(keyword, [ext], 20)
            for f in files:
                similar.append({
                    "file": str(f),
                    "keyword": keyword,
                    "relevance": "keyword_match",
                })
        
        # Deduplicate
        seen = set()
        unique = []
        for item in similar:
            if item["file"] not in seen:
                seen.add(item["file"])
                unique.append(item)
        
        return unique[:10]
    
    def get_project_structure(self, max_depth: int = 3) -> dict[str, Any]:
        """Get a tree view of the project structure.
        
        Args:
            max_depth: Maximum directory depth.
            
        Returns:
            Nested dict representing project structure.
        """
        def _walk(path: Path, depth: int) -> dict[str, Any]:
            result: dict[str, Any] = {}
            if depth >= max_depth:
                return result
            
            try:
                for item in sorted(path.iterdir()):
                    if item.name in self.IGNORE_DIRS or item.name.startswith("."):
                        continue
                    if item.is_dir():
                        result[item.name + "/"] = _walk(item, depth + 1)
                    else:
                        result[item.name] = item.stat().st_size
            except PermissionError:
                pass
            
            return result
        
        return _walk(self._repo_path, 0)
