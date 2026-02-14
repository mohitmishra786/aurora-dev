"""
Unit tests for FileReader, GrepSearch, and GlobSearch tools.
"""
import pytest
import os
import tempfile
from pathlib import Path


class TestFileReader:
    """Tests for FileReader tool."""

    def test_initialization(self):
        """Test FileReader initializes."""
        from aurora_dev.tools.code_tools import FileReader
        reader = FileReader()
        assert reader is not None

    @pytest.mark.asyncio
    async def test_read_file(self):
        """Test reading a file returns content."""
        from aurora_dev.tools.code_tools import FileReader
        
        reader = FileReader()
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("line 1\nline 2\nline 3\n")
            f.flush()
            
            try:
                result = await reader.execute({"file_path": f.name})
                assert result["success"] is True
                assert "line 1" in result["content"]
            finally:
                os.unlink(f.name)

    @pytest.mark.asyncio
    async def test_read_file_with_line_range(self):
        """Test reading specific line range."""
        from aurora_dev.tools.code_tools import FileReader
        
        reader = FileReader()
        
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write("line 1\nline 2\nline 3\nline 4\nline 5\n")
            f.flush()
            
            try:
                result = await reader.execute({
                    "file_path": f.name,
                    "start_line": 2,
                    "end_line": 4,
                })
                assert result["success"] is True
                assert "line 2" in result["content"]
            finally:
                os.unlink(f.name)

    @pytest.mark.asyncio
    async def test_read_nonexistent_file(self):
        """Test reading a file that doesn't exist."""
        from aurora_dev.tools.code_tools import FileReader
        
        reader = FileReader()
        result = await reader.execute({"file_path": "/nonexistent/file.py"})
        assert result["success"] is False


class TestGrepSearch:
    """Tests for GrepSearch tool."""

    def test_initialization(self):
        """Test GrepSearch initializes."""
        from aurora_dev.tools.code_tools import GrepSearch
        searcher = GrepSearch()
        assert searcher is not None

    @pytest.mark.asyncio
    async def test_grep_finds_pattern(self):
        """Test grep finds a pattern in files."""
        from aurora_dev.tools.code_tools import GrepSearch
        
        searcher = GrepSearch()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def hello_world():\n    pass\n")
            
            result = await searcher.execute({
                "pattern": "hello_world",
                "directory": tmpdir,
            })
            assert result["success"] is True
            assert len(result.get("matches", [])) > 0


class TestGlobSearch:
    """Tests for GlobSearch tool."""

    def test_initialization(self):
        """Test GlobSearch initializes."""
        from aurora_dev.tools.code_tools import GlobSearch
        searcher = GlobSearch()
        assert searcher is not None

    @pytest.mark.asyncio
    async def test_glob_finds_files(self):
        """Test glob finds matching files."""
        from aurora_dev.tools.code_tools import GlobSearch
        
        searcher = GlobSearch()
        
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "test.py").touch()
            (Path(tmpdir) / "test.js").touch()
            (Path(tmpdir) / "readme.md").touch()
            
            result = await searcher.execute({
                "pattern": "*.py",
                "directory": tmpdir,
            })
            assert result["success"] is True
            assert len(result.get("matches", [])) == 1
