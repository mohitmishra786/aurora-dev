"""
Code execution tools for AURORA-DEV.

Provides tools for running tests, executing shell commands,
and managing Docker containers.

Example usage:
    >>> runner = PytestRunner()
    >>> result = await runner.run({"path": "tests/", "verbose": True})
"""
import asyncio
import os
import shutil
import time
from typing import Any, Optional

from aurora_dev.tools.tools import BaseTool, ToolResult, ToolStatus
from aurora_dev.core.logging import get_logger


logger = get_logger(__name__)


class ShellRunner(BaseTool):
    """
    Safe shell command execution tool.
    
    Executes shell commands with proper sandboxing,
    timeout handling, and output capture.
    
    Config:
        command: Shell command to execute
        cwd: Working directory (optional)
        env: Environment variables (optional)
        timeout: Command timeout in seconds (optional)
    """
    
    @property
    def name(self) -> str:
        return "shell"
    
    @property
    def description(self) -> str:
        return "Execute shell commands safely with output capture"
    
    @property
    def timeout_seconds(self) -> int:
        return 120  # 2 minutes default
    
    def validate_config(self, config: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate shell command configuration."""
        if "command" not in config:
            return False, "Missing required 'command' field"
        
        # Basic safety checks
        command = config["command"]
        dangerous_patterns = ["rm -rf /", ":(){ :|:& };:", "dd if="]
        for pattern in dangerous_patterns:
            if pattern in command:
                return False, f"Potentially dangerous command pattern: {pattern}"
        
        return True, None
    
    async def run(self, config: dict[str, Any]) -> ToolResult:
        """Execute shell command."""
        command = config["command"]
        cwd = config.get("cwd", os.getcwd())
        env = config.get("env", {})
        timeout = config.get("timeout", self.timeout_seconds)
        
        start_time = time.time()
        
        self._logger.info(f"Executing: {command[:100]}...")
        
        try:
            # Merge environment
            full_env = {**os.environ, **env}
            
            # Create subprocess
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
                env=full_env,
            )
            
            # Wait for completion
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout,
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Decode output
            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")
            
            success = process.returncode == 0
            
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.SUCCESS if success else ToolStatus.FAILED,
                output={
                    "stdout": stdout_str,
                    "stderr": stderr_str,
                },
                error=stderr_str if not success else None,
                exit_code=process.returncode,
                duration_ms=duration_ms,
                metadata={"command": command, "cwd": cwd},
            )
            
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.TIMEOUT,
                output=None,
                error=f"Command timed out after {timeout}s",
                duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._logger.error(f"Shell execution failed: {e}")
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILED,
                output=None,
                error=str(e),
                duration_ms=duration_ms,
            )


class PytestRunner(BaseTool):
    """
    Pytest test runner tool.
    
    Runs Python tests using pytest with JSON output
    for structured result parsing.
    
    Config:
        path: Test path or file (default: "tests/")
        markers: Pytest markers to select (optional)
        verbose: Enable verbose output (optional)
        coverage: Enable coverage reporting (optional)
        extra_args: Additional pytest arguments (optional)
    """
    
    @property
    def name(self) -> str:
        return "pytest"
    
    @property
    def description(self) -> str:
        return "Run Python tests with pytest and parse results"
    
    @property
    def timeout_seconds(self) -> int:
        return 600  # 10 minutes for test suites
    
    def validate_config(self, config: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate pytest configuration."""
        # Check pytest is available
        if not shutil.which("pytest"):
            return False, "pytest not found in PATH"
        
        path = config.get("path", "tests/")
        if not os.path.exists(path):
            return False, f"Test path does not exist: {path}"
        
        return True, None
    
    async def run(self, config: dict[str, Any]) -> ToolResult:
        """Run pytest and parse results."""
        path = config.get("path", "tests/")
        markers = config.get("markers")
        verbose = config.get("verbose", False)
        coverage = config.get("coverage", False)
        extra_args = config.get("extra_args", [])
        cwd = config.get("cwd", os.getcwd())
        
        start_time = time.time()
        
        # Build command
        cmd_parts = ["python", "-m", "pytest", path]
        
        if verbose:
            cmd_parts.append("-v")
        
        if markers:
            cmd_parts.extend(["-m", markers])
        
        if coverage:
            cmd_parts.extend(["--cov", "--cov-report=json"])
        
        # Add JSON report for parsing
        cmd_parts.extend(["--tb=short", "-q"])
        
        cmd_parts.extend(extra_args)
        
        command = " ".join(cmd_parts)
        
        self._logger.info(f"Running pytest: {command}")
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout_seconds,
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")
            
            # Parse pytest output
            parsed = self._parse_pytest_output(stdout_str)
            
            success = process.returncode == 0
            
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.SUCCESS if success else ToolStatus.FAILED,
                output={
                    "raw_output": stdout_str,
                    "parsed": parsed,
                },
                error=stderr_str if not success else None,
                exit_code=process.returncode,
                duration_ms=duration_ms,
                metrics={
                    "tests_passed": parsed.get("passed", 0),
                    "tests_failed": parsed.get("failed", 0),
                    "tests_skipped": parsed.get("skipped", 0),
                },
            )
            
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.TIMEOUT,
                output=None,
                error=f"Tests timed out after {self.timeout_seconds}s",
                duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._logger.error(f"Pytest failed: {e}")
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILED,
                output=None,
                error=str(e),
                duration_ms=duration_ms,
            )
    
    def _parse_pytest_output(self, output: str) -> dict[str, Any]:
        """Parse pytest output for test counts."""
        import re
        
        result = {
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "errors": 0,
            "warnings": 0,
        }
        
        # Parse summary line: "5 passed, 2 failed, 1 skipped"
        patterns = [
            (r"(\d+) passed", "passed"),
            (r"(\d+) failed", "failed"),
            (r"(\d+) skipped", "skipped"),
            (r"(\d+) error", "errors"),
            (r"(\d+) warning", "warnings"),
        ]
        
        for pattern, key in patterns:
            match = re.search(pattern, output)
            if match:
                result[key] = int(match.group(1))
        
        return result


class DockerRunner(BaseTool):
    """
    Docker container execution tool.
    
    Runs commands inside Docker containers for
    isolated and reproducible execution.
    
    Supports optional security sandbox mode with:
    - Network isolation policies
    - Resource limits (CPU, memory, disk I/O)
    - Secure secret injection
    
    Config:
        image: Docker image to use
        command: Command to run inside container
        volumes: Volume mounts (optional)
        env: Environment variables (optional)
        network: Network mode (optional)
        remove: Remove container after run (default: True)
        secure_mode: Enable security sandbox (optional)
        resource_limits: Resource constraints (optional)
        network_policy: Network isolation policy (optional)
    """
    
    def __init__(self):
        """Initialize DockerRunner with optional security sandbox."""
        super().__init__()
        self._sandbox = None
    
    def _get_sandbox(self):
        """Lazy-load security sandbox to avoid import cycles."""
        if self._sandbox is None:
            try:
                from aurora_dev.tools.security_sandbox import (
                    SecureSandbox,
                    SandboxConfig,
                    NetworkPolicy,
                    ResourceLimits,
                )
                self._sandbox_available = True
                self._SecureSandbox = SecureSandbox
                self._SandboxConfig = SandboxConfig
                self._NetworkPolicy = NetworkPolicy
                self._ResourceLimits = ResourceLimits
            except ImportError:
                self._sandbox_available = False
        return self._sandbox_available
    
    @property
    def name(self) -> str:
        return "docker"
    
    @property
    def description(self) -> str:
        return "Run commands in Docker containers for isolated execution"
    
    @property
    def timeout_seconds(self) -> int:
        return 600  # 10 minutes
    
    def validate_config(self, config: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate Docker configuration."""
        if not shutil.which("docker"):
            return False, "docker not found in PATH"
        
        if "image" not in config:
            return False, "Missing required 'image' field"
        
        if "command" not in config:
            return False, "Missing required 'command' field"
        
        return True, None
    
    async def run(self, config: dict[str, Any]) -> ToolResult:
        """Run command in Docker container.
        
        Args:
            config: Configuration dict with:
                - image: Docker image name
                - command: Command to run
                - volumes: Optional volume mounts
                - env: Optional environment variables
                - network: Optional network mode
                - remove: Remove container after (default: True)
                - secure_mode: Enable security sandbox
                - resource_limits: CPU/memory limits dict
                - network_policy: Network isolation policy string
        
        Returns:
            ToolResult with stdout, stderr, and exit code.
        """
        image = config["image"]
        command = config["command"]
        volumes = config.get("volumes", [])
        env = config.get("env", {})
        network = config.get("network")
        remove = config.get("remove", True)
        secure_mode = config.get("secure_mode", False)
        
        start_time = time.time()
        
        # Use security sandbox if requested and available
        if secure_mode and self._get_sandbox():
            return await self._run_secure(config, start_time)
        
        # Standard Docker execution
        # Build docker run command
        docker_cmd = ["docker", "run"]
        
        if remove:
            docker_cmd.append("--rm")
        
        for vol in volumes:
            docker_cmd.extend(["-v", vol])
        
        for key, value in env.items():
            docker_cmd.extend(["-e", f"{key}={value}"])
        
        if network:
            docker_cmd.extend(["--network", network])
        
        docker_cmd.append(image)
        docker_cmd.extend(command.split())
        
        full_command = " ".join(docker_cmd)
        
        self._logger.info(f"Running Docker: {image} - {command[:50]}...")
        
        try:
            process = await asyncio.create_subprocess_shell(
                full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout_seconds,
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")
            
            success = process.returncode == 0
            
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.SUCCESS if success else ToolStatus.FAILED,
                output={
                    "stdout": stdout_str,
                    "stderr": stderr_str,
                },
                error=stderr_str if not success else None,
                exit_code=process.returncode,
                duration_ms=duration_ms,
                metadata={"image": image, "command": command},
            )
            
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.TIMEOUT,
                output=None,
                error=f"Container execution timed out after {self.timeout_seconds}s",
                duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._logger.error(f"Docker execution failed: {e}")
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILED,
                output=None,
                error=str(e),
                duration_ms=duration_ms,
            )
    
    async def _run_secure(self, config: dict[str, Any], start_time: float) -> ToolResult:
        """Run command with security sandbox.
        
        Applies network policies, resource limits, and secure configuration.
        """
        image = config["image"]
        command = config["command"]
        volumes = config.get("volumes", [])
        env = config.get("env", {})
        
        # Parse resource limits
        resource_config = config.get("resource_limits", {})
        resource_limits = self._ResourceLimits(
            cpu_limit=resource_config.get("cpu_limit", 1.0),
            memory_limit=resource_config.get("memory_limit", "512m"),
            disk_io_limit=resource_config.get("disk_io_limit"),
            max_processes=resource_config.get("max_processes", 50),
            timeout_seconds=config.get("timeout", self.timeout_seconds),
        )
        
        # Parse network policy
        network_policy_str = config.get("network_policy", "RESTRICTED")
        try:
            network_policy = self._NetworkPolicy[network_policy_str.upper()]
        except KeyError:
            network_policy = self._NetworkPolicy.RESTRICTED
        
        # Create sandbox config
        sandbox_config = self._SandboxConfig(
            network_policy=network_policy,
            resource_limits=resource_limits,
            allowed_hosts=config.get("allowed_hosts", []),
            read_only_root=config.get("read_only_root", True),
        )
        
        # Create and run sandbox
        sandbox = self._SecureSandbox(sandbox_config)
        
        self._logger.info(
            f"Running secure Docker: {image} - {command[:50]}... "
            f"(policy={network_policy.name})"
        )
        
        try:
            # Convert volumes to dict format
            volume_dict = {}
            for vol in volumes:
                if ":" in vol:
                    host, container = vol.split(":", 1)
                    volume_dict[host] = container
            
            exit_code, stdout, stderr = await sandbox.run(
                image=image,
                command=command.split() if isinstance(command, str) else command,
                volumes=volume_dict,
                env=env,
            )
            
            duration_ms = (time.time() - start_time) * 1000
            success = exit_code == 0
            
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.SUCCESS if success else ToolStatus.FAILED,
                output={
                    "stdout": stdout,
                    "stderr": stderr,
                },
                error=stderr if not success else None,
                exit_code=exit_code,
                duration_ms=duration_ms,
                metadata={
                    "image": image,
                    "command": command,
                    "secure_mode": True,
                    "network_policy": network_policy.name,
                },
            )
            
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.TIMEOUT,
                output=None,
                error=f"Secure container timed out after {resource_limits.timeout_seconds}s",
                duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._logger.error(f"Secure Docker execution failed: {e}")
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILED,
                output=None,
                error=str(e),
                duration_ms=duration_ms,
            )


class ESLintRunner(BaseTool):
    """
    ESLint JavaScript/TypeScript linter tool.
    
    Runs ESLint for code quality checks on JS/TS files.
    
    Config:
        path: File or directory to lint
        fix: Auto-fix issues (optional)
        config: Custom config file (optional)
    """
    
    @property
    def name(self) -> str:
        return "eslint"
    
    @property
    def description(self) -> str:
        return "Lint JavaScript/TypeScript code with ESLint"
    
    def validate_config(self, config: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate ESLint configuration."""
        if not shutil.which("npx"):
            return False, "npx not found in PATH"
        
        if "path" not in config:
            return False, "Missing required 'path' field"
        
        return True, None
    
    async def run(self, config: dict[str, Any]) -> ToolResult:
        """Run ESLint on specified path."""
        path = config["path"]
        fix = config.get("fix", False)
        eslint_config = config.get("config")
        cwd = config.get("cwd", os.getcwd())
        
        start_time = time.time()
        
        # Build command
        cmd_parts = ["npx", "eslint", path, "--format", "json"]
        
        if fix:
            cmd_parts.append("--fix")
        
        if eslint_config:
            cmd_parts.extend(["--config", eslint_config])
        
        command = " ".join(cmd_parts)
        
        self._logger.info(f"Running ESLint: {command}")
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout_seconds,
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            stdout_str = stdout.decode("utf-8", errors="replace")
            stderr_str = stderr.decode("utf-8", errors="replace")
            
            # Parse JSON output
            import json
            try:
                results = json.loads(stdout_str) if stdout_str.strip() else []
            except json.JSONDecodeError:
                results = []
            
            # Count issues
            error_count = sum(r.get("errorCount", 0) for r in results)
            warning_count = sum(r.get("warningCount", 0) for r in results)
            
            success = error_count == 0
            
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.SUCCESS if success else ToolStatus.FAILED,
                output={
                    "results": results,
                    "summary": {
                        "files": len(results),
                        "errors": error_count,
                        "warnings": warning_count,
                    },
                },
                error=None if success else f"{error_count} errors found",
                exit_code=process.returncode,
                duration_ms=duration_ms,
                metrics={
                    "errors": error_count,
                    "warnings": warning_count,
                },
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._logger.error(f"ESLint failed: {e}")
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILED,
                output=None,
                error=str(e),
                duration_ms=duration_ms,
            )


class FileReader(BaseTool):
    """
    File reading tool for agents.
    
    Reads file contents with optional line range selection,
    providing agents the ability to inspect source code.
    
    Config:
        path: File path to read
        start_line: Starting line number (1-indexed, optional)
        end_line: Ending line number (inclusive, optional)
        max_size_kb: Maximum file size to read in KB (default: 500)
    """
    
    @property
    def name(self) -> str:
        return "read_file"
    
    @property
    def description(self) -> str:
        return "Read file contents with optional line range"
    
    def validate_config(self, config: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate file read configuration."""
        if "path" not in config:
            return False, "Missing required 'path' field"
        
        path = config["path"]
        if not os.path.exists(path):
            return False, f"File does not exist: {path}"
        
        if not os.path.isfile(path):
            return False, f"Path is not a file: {path}"
        
        max_size_kb = config.get("max_size_kb", 500)
        file_size = os.path.getsize(path) / 1024
        if file_size > max_size_kb:
            return False, f"File too large ({file_size:.0f}KB > {max_size_kb}KB limit)"
        
        return True, None
    
    async def run(self, config: dict[str, Any]) -> ToolResult:
        """Read file contents."""
        path = config["path"]
        start_line = config.get("start_line")
        end_line = config.get("end_line")
        
        start_time = time.time()
        
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            
            total_lines = len(lines)
            
            # Apply line range
            if start_line is not None or end_line is not None:
                start = max(0, (start_line or 1) - 1)
                end = min(total_lines, end_line or total_lines)
                selected_lines = lines[start:end]
                # Add line numbers
                content = "".join(
                    f"{i + start + 1}: {line}"
                    for i, line in enumerate(selected_lines)
                )
            else:
                content = "".join(lines)
            
            duration_ms = (time.time() - start_time) * 1000
            
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.SUCCESS,
                output={
                    "content": content,
                    "total_lines": total_lines,
                    "file_path": path,
                },
                duration_ms=duration_ms,
                metadata={"path": path},
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._logger.error(f"File read failed: {e}")
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILED,
                output=None,
                error=str(e),
                duration_ms=duration_ms,
            )


class GrepSearch(BaseTool):
    """
    Recursive grep search tool for agents.
    
    Searches for patterns in files using subprocess grep,
    returning matches with file names and line numbers.
    
    Config:
        pattern: Search pattern (string or regex)
        path: Directory or file to search
        regex: Treat pattern as regex (default: False)
        case_insensitive: Case-insensitive search (default: False)
        include: File glob pattern to include (optional)
        max_results: Maximum results to return (default: 50)
    """
    
    @property
    def name(self) -> str:
        return "grep"
    
    @property
    def description(self) -> str:
        return "Search for patterns in files recursively"
    
    def validate_config(self, config: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate grep configuration."""
        if "pattern" not in config:
            return False, "Missing required 'pattern' field"
        
        if "path" not in config:
            return False, "Missing required 'path' field"
        
        path = config["path"]
        if not os.path.exists(path):
            return False, f"Path does not exist: {path}"
        
        return True, None
    
    async def run(self, config: dict[str, Any]) -> ToolResult:
        """Execute grep search."""
        pattern = config["pattern"]
        path = config["path"]
        use_regex = config.get("regex", False)
        case_insensitive = config.get("case_insensitive", False)
        include = config.get("include")
        max_results = config.get("max_results", 50)
        
        start_time = time.time()
        
        # Build grep command
        cmd_parts = ["grep", "-rn"]
        
        if not use_regex:
            cmd_parts.append("-F")  # Fixed string (literal)
        
        if case_insensitive:
            cmd_parts.append("-i")
        
        if include:
            cmd_parts.extend(["--include", include])
        
        cmd_parts.extend([pattern, path])
        
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd_parts,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=30,
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            stdout_str = stdout.decode("utf-8", errors="replace")
            
            # Parse results
            matches = []
            for line in stdout_str.strip().split("\n"):
                if not line:
                    continue
                # Format: file:line_number:content
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    matches.append({
                        "file": parts[0],
                        "line": int(parts[1]) if parts[1].isdigit() else 0,
                        "content": parts[2].strip(),
                    })
                
                if len(matches) >= max_results:
                    break
            
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.SUCCESS,
                output={
                    "matches": matches,
                    "total_matches": len(matches),
                    "truncated": len(matches) >= max_results,
                },
                duration_ms=duration_ms,
                metadata={"pattern": pattern, "path": path},
            )
            
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.TIMEOUT,
                output=None,
                error="Grep search timed out after 30s",
                duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._logger.error(f"Grep search failed: {e}")
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILED,
                output=None,
                error=str(e),
                duration_ms=duration_ms,
            )


class GlobSearch(BaseTool):
    """
    File listing tool using glob patterns.
    
    Lists files matching a glob pattern, returning
    paths with size and modification time.
    
    Config:
        pattern: Glob pattern (e.g., "**/*.py")
        path: Base directory to search from
        max_results: Maximum number of files (default: 100)
    """
    
    @property
    def name(self) -> str:
        return "glob"
    
    @property
    def description(self) -> str:
        return "List files matching a glob pattern"
    
    def validate_config(self, config: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate glob configuration."""
        if "pattern" not in config:
            return False, "Missing required 'pattern' field"
        
        if "path" not in config:
            return False, "Missing required 'path' field"
        
        path = config["path"]
        if not os.path.isdir(path):
            return False, f"Directory does not exist: {path}"
        
        return True, None
    
    async def run(self, config: dict[str, Any]) -> ToolResult:
        """Execute glob search."""
        from pathlib import Path
        from datetime import datetime
        
        pattern = config["pattern"]
        base_path = config["path"]
        max_results = config.get("max_results", 100)
        
        start_time = time.time()
        
        try:
            base = Path(base_path)
            matches = []
            
            for file_path in base.glob(pattern):
                if len(matches) >= max_results:
                    break
                
                try:
                    stat = file_path.stat()
                    matches.append({
                        "path": str(file_path),
                        "name": file_path.name,
                        "size_bytes": stat.st_size,
                        "modified": datetime.fromtimestamp(
                            stat.st_mtime
                        ).isoformat(),
                        "is_dir": file_path.is_dir(),
                    })
                except OSError:
                    continue
            
            duration_ms = (time.time() - start_time) * 1000
            
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.SUCCESS,
                output={
                    "files": matches,
                    "total_found": len(matches),
                    "truncated": len(matches) >= max_results,
                },
                duration_ms=duration_ms,
                metadata={"pattern": pattern, "path": base_path},
            )
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._logger.error(f"Glob search failed: {e}")
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILED,
                output=None,
                error=str(e),
                duration_ms=duration_ms,
            )

