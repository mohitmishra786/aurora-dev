"""
Security scanning tools for AURORA-DEV.

Provides tools for static analysis, secret detection,
and container vulnerability scanning.

Example usage:
    >>> scanner = SemgrepScanner()
    >>> result = await scanner.run({"path": "src/", "rules": "p/security-audit"})
"""
import asyncio
import json
import os
import shutil
import time
from typing import Any, Optional

from aurora_dev.tools.tools import BaseTool, ToolResult, ToolStatus
from aurora_dev.core.logging import get_logger


logger = get_logger(__name__)


class SemgrepScanner(BaseTool):
    """
    Semgrep static analysis security scanner.
    
    Runs Semgrep for SAST (Static Application Security Testing)
    to find vulnerabilities and code quality issues.
    
    Config:
        path: Directory or file to scan
        rules: Semgrep rules to use (e.g., "p/security-audit", "p/owasp-top-ten")
        config: Custom config file (optional)
        exclude: Patterns to exclude (optional)
    """
    
    @property
    def name(self) -> str:
        return "semgrep"
    
    @property
    def description(self) -> str:
        return "Static analysis security scanning with Semgrep"
    
    @property
    def timeout_seconds(self) -> int:
        return 300  # 5 minutes
    
    def validate_config(self, config: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate Semgrep configuration."""
        if not shutil.which("semgrep"):
            return False, "semgrep not found in PATH. Install with: pip install semgrep"
        
        if "path" not in config:
            return False, "Missing required 'path' field"
        
        path = config["path"]
        if not os.path.exists(path):
            return False, f"Path does not exist: {path}"
        
        return True, None
    
    async def run(self, config: dict[str, Any]) -> ToolResult:
        """Run Semgrep scan."""
        path = config["path"]
        rules = config.get("rules", "p/security-audit")
        custom_config = config.get("config")
        exclude = config.get("exclude", [])
        
        start_time = time.time()
        
        # Build command
        cmd_parts = ["semgrep", "--json", "--quiet"]
        
        if custom_config:
            cmd_parts.extend(["--config", custom_config])
        else:
            cmd_parts.extend(["--config", rules])
        
        for pattern in exclude:
            cmd_parts.extend(["--exclude", pattern])
        
        cmd_parts.append(path)
        
        command = " ".join(cmd_parts)
        
        self._logger.info(f"Running Semgrep: {rules} on {path}")
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
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
            
            # Parse JSON output
            try:
                results = json.loads(stdout_str) if stdout_str.strip() else {}
            except json.JSONDecodeError:
                results = {"error": "Failed to parse output", "raw": stdout_str}
            
            # Extract findings
            findings = results.get("results", [])
            errors = results.get("errors", [])
            
            # Categorize by severity
            severity_counts = {"ERROR": 0, "WARNING": 0, "INFO": 0}
            for finding in findings:
                severity = finding.get("extra", {}).get("severity", "INFO")
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Success if no errors (warnings are OK)
            has_errors = severity_counts.get("ERROR", 0) > 0
            
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.SUCCESS if not has_errors else ToolStatus.FAILED,
                output={
                    "findings": findings,
                    "errors": errors,
                    "summary": {
                        "total_findings": len(findings),
                        "by_severity": severity_counts,
                    },
                },
                error=f"{severity_counts['ERROR']} security errors found" if has_errors else None,
                exit_code=process.returncode,
                duration_ms=duration_ms,
                metrics={
                    "findings": len(findings),
                    "errors": severity_counts.get("ERROR", 0),
                    "warnings": severity_counts.get("WARNING", 0),
                },
            )
            
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.TIMEOUT,
                output=None,
                error=f"Scan timed out after {self.timeout_seconds}s",
                duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._logger.error(f"Semgrep scan failed: {e}")
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILED,
                output=None,
                error=str(e),
                duration_ms=duration_ms,
            )


class TruffleHogScanner(BaseTool):
    """
    TruffleHog secret detection scanner.
    
    Scans for exposed secrets, API keys, passwords,
    and other sensitive data in code.
    
    Config:
        path: Directory or file to scan
        only_verified: Only report verified secrets (optional)
        include_detectors: Specific detectors to use (optional)
        exclude_detectors: Detectors to exclude (optional)
    """
    
    @property
    def name(self) -> str:
        return "trufflehog"
    
    @property
    def description(self) -> str:
        return "Secret detection with TruffleHog"
    
    @property
    def timeout_seconds(self) -> int:
        return 300  # 5 minutes
    
    def validate_config(self, config: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate TruffleHog configuration."""
        if not shutil.which("trufflehog"):
            return False, "trufflehog not found in PATH"
        
        if "path" not in config:
            return False, "Missing required 'path' field"
        
        return True, None
    
    async def run(self, config: dict[str, Any]) -> ToolResult:
        """Run TruffleHog scan."""
        path = config["path"]
        only_verified = config.get("only_verified", False)
        include_detectors = config.get("include_detectors", [])
        exclude_detectors = config.get("exclude_detectors", [])
        
        start_time = time.time()
        
        # Build command
        cmd_parts = ["trufflehog", "filesystem", "--json"]
        
        if only_verified:
            cmd_parts.append("--only-verified")
        
        for detector in include_detectors:
            cmd_parts.extend(["--include-detectors", detector])
        
        for detector in exclude_detectors:
            cmd_parts.extend(["--exclude-detectors", detector])
        
        cmd_parts.append(path)
        
        command = " ".join(cmd_parts)
        
        self._logger.info(f"Running TruffleHog on: {path}")
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
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
            
            # Parse JSONL output (one JSON object per line)
            secrets = []
            for line in stdout_str.strip().split("\n"):
                if line.strip():
                    try:
                        secrets.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
            
            # Categorize by type
            secret_types: dict[str, int] = {}
            for secret in secrets:
                detector_type = secret.get("DetectorType", "unknown")
                secret_types[detector_type] = secret_types.get(detector_type, 0) + 1
            
            # Any secrets found is a failure
            has_secrets = len(secrets) > 0
            
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILED if has_secrets else ToolStatus.SUCCESS,
                output={
                    "secrets": secrets,
                    "summary": {
                        "total_secrets": len(secrets),
                        "by_type": secret_types,
                    },
                },
                error=f"{len(secrets)} secrets found!" if has_secrets else None,
                exit_code=process.returncode,
                duration_ms=duration_ms,
                metrics={
                    "secrets_found": len(secrets),
                    "secret_types": len(secret_types),
                },
            )
            
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.TIMEOUT,
                output=None,
                error=f"Scan timed out after {self.timeout_seconds}s",
                duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._logger.error(f"TruffleHog scan failed: {e}")
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILED,
                output=None,
                error=str(e),
                duration_ms=duration_ms,
            )


class TrivyScanner(BaseTool):
    """
    Trivy container and filesystem vulnerability scanner.
    
    Scans Docker images and filesystems for known
    vulnerabilities (CVEs).
    
    Config:
        target: Image name or filesystem path to scan
        scan_type: "image" or "fs" (default: "fs")
        severity: Minimum severity to report (optional)
        ignore_unfixed: Ignore unfixed vulnerabilities (optional)
    """
    
    @property
    def name(self) -> str:
        return "trivy"
    
    @property
    def description(self) -> str:
        return "Vulnerability scanning with Trivy"
    
    @property
    def timeout_seconds(self) -> int:
        return 600  # 10 minutes (image scanning can be slow)
    
    def validate_config(self, config: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate Trivy configuration."""
        if not shutil.which("trivy"):
            return False, "trivy not found in PATH"
        
        if "target" not in config:
            return False, "Missing required 'target' field"
        
        scan_type = config.get("scan_type", "fs")
        if scan_type not in ["image", "fs", "repo"]:
            return False, f"Invalid scan_type: {scan_type}"
        
        return True, None
    
    async def run(self, config: dict[str, Any]) -> ToolResult:
        """Run Trivy vulnerability scan."""
        target = config["target"]
        scan_type = config.get("scan_type", "fs")
        severity = config.get("severity", "UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL")
        ignore_unfixed = config.get("ignore_unfixed", False)
        
        start_time = time.time()
        
        # Build command
        cmd_parts = ["trivy", scan_type, "--format", "json", "--quiet"]
        
        cmd_parts.extend(["--severity", severity])
        
        if ignore_unfixed:
            cmd_parts.append("--ignore-unfixed")
        
        cmd_parts.append(target)
        
        command = " ".join(cmd_parts)
        
        self._logger.info(f"Running Trivy {scan_type} scan on: {target}")
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
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
            
            # Parse JSON output
            try:
                results = json.loads(stdout_str) if stdout_str.strip() else {}
            except json.JSONDecodeError:
                results = {"error": "Failed to parse output"}
            
            # Extract vulnerabilities
            vulnerabilities = []
            severity_counts = {
                "CRITICAL": 0,
                "HIGH": 0,
                "MEDIUM": 0,
                "LOW": 0,
                "UNKNOWN": 0,
            }
            
            # Handle different Trivy output formats
            scan_results = results.get("Results", [])
            for result in scan_results:
                vulns = result.get("Vulnerabilities", [])
                for vuln in vulns:
                    vulnerabilities.append(vuln)
                    sev = vuln.get("Severity", "UNKNOWN")
                    severity_counts[sev] = severity_counts.get(sev, 0) + 1
            
            # Critical or High vulnerabilities = failure
            has_critical = severity_counts.get("CRITICAL", 0) > 0
            has_high = severity_counts.get("HIGH", 0) > 0
            
            success = not (has_critical or has_high)
            
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.SUCCESS if success else ToolStatus.FAILED,
                output={
                    "vulnerabilities": vulnerabilities,
                    "summary": {
                        "total_vulnerabilities": len(vulnerabilities),
                        "by_severity": severity_counts,
                    },
                },
                error=(
                    f"{severity_counts['CRITICAL']} critical, {severity_counts['HIGH']} high vulnerabilities"
                    if not success else None
                ),
                exit_code=process.returncode,
                duration_ms=duration_ms,
                metrics={
                    "total": len(vulnerabilities),
                    "critical": severity_counts.get("CRITICAL", 0),
                    "high": severity_counts.get("HIGH", 0),
                    "medium": severity_counts.get("MEDIUM", 0),
                    "low": severity_counts.get("LOW", 0),
                },
            )
            
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.TIMEOUT,
                output=None,
                error=f"Scan timed out after {self.timeout_seconds}s",
                duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._logger.error(f"Trivy scan failed: {e}")
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILED,
                output=None,
                error=str(e),
                duration_ms=duration_ms,
            )


class DependencyCheckScanner(BaseTool):
    """
    OWASP Dependency-Check scanner.
    
    Scans project dependencies for known vulnerabilities.
    
    Config:
        path: Project directory to scan
        output_format: Report format (HTML, JSON, XML, etc.)
        suppression_file: File with suppressed vulnerabilities (optional)
    """
    
    @property
    def name(self) -> str:
        return "dependency-check"
    
    @property
    def description(self) -> str:
        return "OWASP Dependency-Check vulnerability scanner"
    
    @property
    def timeout_seconds(self) -> int:
        return 900  # 15 minutes (downloads CVE database)
    
    def validate_config(self, config: dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate configuration."""
        if not shutil.which("dependency-check"):
            return False, "dependency-check not found in PATH"
        
        if "path" not in config:
            return False, "Missing required 'path' field"
        
        return True, None
    
    async def run(self, config: dict[str, Any]) -> ToolResult:
        """Run Dependency-Check scan."""
        path = config["path"]
        output_format = config.get("output_format", "JSON")
        suppression = config.get("suppression_file")
        
        start_time = time.time()
        
        # Create temp output directory
        import tempfile
        output_dir = tempfile.mkdtemp()
        
        # Build command
        cmd_parts = [
            "dependency-check",
            "--scan", path,
            "--format", output_format,
            "--out", output_dir,
        ]
        
        if suppression:
            cmd_parts.extend(["--suppression", suppression])
        
        command = " ".join(cmd_parts)
        
        self._logger.info(f"Running Dependency-Check on: {path}")
        
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.timeout_seconds,
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Read JSON report if available
            report_file = os.path.join(output_dir, "dependency-check-report.json")
            results = {}
            if os.path.exists(report_file):
                with open(report_file) as f:
                    results = json.load(f)
            
            # Extract vulnerabilities
            dependencies = results.get("dependencies", [])
            vulnerabilities = []
            
            for dep in dependencies:
                vulns = dep.get("vulnerabilities", [])
                for vuln in vulns:
                    vuln["package"] = dep.get("fileName", "unknown")
                    vulnerabilities.append(vuln)
            
            # Clean up
            import shutil as sh
            sh.rmtree(output_dir, ignore_errors=True)
            
            has_vulnerabilities = len(vulnerabilities) > 0
            
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILED if has_vulnerabilities else ToolStatus.SUCCESS,
                output={
                    "vulnerabilities": vulnerabilities,
                    "total": len(vulnerabilities),
                },
                error=f"{len(vulnerabilities)} vulnerabilities found" if has_vulnerabilities else None,
                exit_code=process.returncode,
                duration_ms=duration_ms,
                metrics={"vulnerabilities": len(vulnerabilities)},
            )
            
        except asyncio.TimeoutError:
            duration_ms = (time.time() - start_time) * 1000
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.TIMEOUT,
                output=None,
                error=f"Scan timed out after {self.timeout_seconds}s",
                duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            self._logger.error(f"Dependency-Check failed: {e}")
            return ToolResult(
                tool_name=self.name,
                status=ToolStatus.FAILED,
                output=None,
                error=str(e),
                duration_ms=duration_ms,
            )
