"""
Security Sandbox for AURORA-DEV Container Execution.

Provides network policies, resource limits, and secure secret injection
for containerized agent code execution.
"""
import json
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


logger = logging.getLogger(__name__)


class NetworkIsolationLevel(Enum):
    """Network isolation levels for containers."""
    
    NONE = "none"           # No network restrictions
    INTERNAL = "internal"   # Internal network only
    RESTRICTED = "restricted"  # Only allowed hosts
    ISOLATED = "isolated"   # No network access


@dataclass
class NetworkPolicy:
    """Network policy for container isolation.
    
    Defines which network resources containers can access.
    
    Attributes:
        isolation_level: Base isolation level.
        allowed_hosts: List of hostnames/IPs allowed (for RESTRICTED mode).
        blocked_internal: Block internal/private IP ranges.
        max_connections: Maximum concurrent connections.
        rate_limit_mbps: Network bandwidth limit in Mbps.
    """
    
    isolation_level: NetworkIsolationLevel = NetworkIsolationLevel.RESTRICTED
    
    # Allowed hosts for RESTRICTED mode
    allowed_hosts: list[str] = field(default_factory=lambda: [
        # Python packages
        "pypi.org",
        "files.pythonhosted.org",
        "pypi.python.org",
        
        # npm packages  
        "registry.npmjs.org",
        "registry.yarnpkg.com",
        
        # Docker Hub
        "registry.hub.docker.com",
        "registry-1.docker.io",
        "auth.docker.io",
        "production.cloudflare.docker.com",
        
        # GitHub (for git clone)
        "github.com",
        "api.github.com",
        "raw.githubusercontent.com",
        
        # Common CDNs
        "cdn.jsdelivr.net",
        "unpkg.com",
    ])
    
    blocked_internal: bool = True  # Block 10.x, 172.16-31.x, 192.168.x
    max_connections: int = 100
    rate_limit_mbps: Optional[int] = None  # None = unlimited
    
    def get_iptables_rules(self) -> list[str]:
        """Generate iptables rules for this policy.
        
        Returns:
            List of iptables commands.
        """
        rules = []
        
        if self.isolation_level == NetworkIsolationLevel.NONE:
            return []
        
        if self.isolation_level == NetworkIsolationLevel.ISOLATED:
            # Block all outbound traffic
            rules.append("iptables -A OUTPUT -j DROP")
            return rules
        
        if self.blocked_internal:
            # Block private IP ranges
            rules.extend([
                "iptables -A OUTPUT -d 10.0.0.0/8 -j DROP",
                "iptables -A OUTPUT -d 172.16.0.0/12 -j DROP",
                "iptables -A OUTPUT -d 192.168.0.0/16 -j DROP",
                "iptables -A OUTPUT -d 127.0.0.0/8 -j DROP",
            ])
        
        if self.isolation_level == NetworkIsolationLevel.RESTRICTED:
            # Default deny, then allow specific hosts
            rules.append("iptables -P OUTPUT DROP")
            
            # Allow DNS
            rules.append("iptables -A OUTPUT -p udp --dport 53 -j ACCEPT")
            rules.append("iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT")
            
            # Allow established connections
            rules.append("iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT")
            
            # Allow specific hosts (would need DNS resolution)
            for host in self.allowed_hosts:
                rules.append(f"# Allow {host}")
        
        if self.max_connections:
            rules.append(
                f"iptables -A OUTPUT -p tcp --syn -m connlimit "
                f"--connlimit-above {self.max_connections} -j DROP"
            )
        
        return rules
    
    def to_docker_args(self) -> list[str]:
        """Convert policy to docker run arguments.
        
        Returns:
            List of docker CLI arguments.
        """
        args = []
        
        if self.isolation_level == NetworkIsolationLevel.ISOLATED:
            args.extend(["--network", "none"])
        elif self.isolation_level == NetworkIsolationLevel.INTERNAL:
            args.extend(["--network", "aurora-internal"])
        elif self.isolation_level == NetworkIsolationLevel.RESTRICTED:
            args.extend(["--network", "aurora-sandbox"])
        
        return args


@dataclass
class ResourceLimits:
    """Resource limits for container execution.
    
    Attributes:
        memory_mb: Memory limit in MB.
        cpu_cores: CPU limit (e.g., 2.0 for 2 cores).
        pids_limit: Maximum number of processes.
        disk_read_mbps: Disk read limit in MB/s.
        disk_write_mbps: Disk write limit in MB/s.
        no_new_privileges: Prevent privilege escalation.
        read_only_rootfs: Make root filesystem read-only.
        drop_capabilities: Linux capabilities to drop.
    """
    
    memory_mb: int = 2048  # 2GB default
    cpu_cores: float = 2.0
    pids_limit: int = 256
    disk_read_mbps: Optional[int] = None
    disk_write_mbps: Optional[int] = None
    no_new_privileges: bool = True
    read_only_rootfs: bool = True
    drop_capabilities: list[str] = field(default_factory=lambda: [
        "ALL"  # Drop all capabilities by default
    ])
    add_capabilities: list[str] = field(default_factory=list)
    
    def to_docker_args(self) -> list[str]:
        """Convert limits to docker run arguments.
        
        Returns:
            List of docker CLI arguments.
        """
        args = []
        
        # Memory limit
        args.extend(["--memory", f"{self.memory_mb}m"])
        args.extend(["--memory-swap", f"{self.memory_mb}m"])  # Disable swap
        
        # CPU limit
        args.extend(["--cpus", str(self.cpu_cores)])
        
        # PID limit
        args.extend(["--pids-limit", str(self.pids_limit)])
        
        # Disk I/O limits
        if self.disk_read_mbps:
            args.extend(["--device-read-bps", f"/dev/sda:{self.disk_read_mbps}mb"])
        if self.disk_write_mbps:
            args.extend(["--device-write-bps", f"/dev/sda:{self.disk_write_mbps}mb"])
        
        # Security options
        if self.no_new_privileges:
            args.extend(["--security-opt", "no-new-privileges:true"])
        
        if self.read_only_rootfs:
            args.append("--read-only")
        
        # Capabilities
        for cap in self.drop_capabilities:
            args.extend(["--cap-drop", cap])
        
        for cap in self.add_capabilities:
            args.extend(["--cap-add", cap])
        
        return args


@dataclass
class SecretInjector:
    """Secure secret injection for containers.
    
    Uses Docker secrets or tmpfs mounts instead of environment variables.
    
    Attributes:
        use_docker_secrets: Use Docker Swarm secrets (requires swarm mode).
        secrets_mount_path: Path inside container for secrets.
        mask_in_logs: Replace secret values in logs.
    """
    
    use_docker_secrets: bool = False  # Requires Docker Swarm
    secrets_mount_path: str = "/run/secrets"
    mask_in_logs: bool = True
    
    _temp_dirs: list[str] = field(default_factory=list, repr=False)
    
    def inject_secrets_as_files(
        self,
        secrets: dict[str, str],
    ) -> tuple[str, list[str]]:
        """Create a temp directory with secrets as files.
        
        Secrets are written to individual files that can be
        mounted into the container via tmpfs.
        
        Args:
            secrets: Dictionary of secret_name -> secret_value.
            
        Returns:
            Tuple of (temp_dir_path, docker_args).
        """
        # Create temp directory for secrets
        temp_dir = tempfile.mkdtemp(prefix="aurora_secrets_")
        self._temp_dirs.append(temp_dir)
        
        # Write each secret to a file
        for name, value in secrets.items():
            secret_file = os.path.join(temp_dir, name)
            with open(secret_file, "w") as f:
                f.write(value)
            # Restrict permissions
            os.chmod(secret_file, 0o400)
        
        # Generate docker args to mount as tmpfs
        docker_args = [
            "--mount",
            f"type=bind,source={temp_dir},target={self.secrets_mount_path},readonly"
        ]
        
        logger.debug(f"Created secrets directory at {temp_dir}")
        return temp_dir, docker_args
    
    def inject_as_env_encrypted(
        self,
        secrets: dict[str, str],
        encryption_key: Optional[str] = None,
    ) -> list[str]:
        """Inject secrets as base64-encoded environment variables.
        
        Note: This is less secure than file-based injection.
        Only use when file mounting is not possible.
        
        Args:
            secrets: Dictionary of secret_name -> secret_value.
            encryption_key: Optional key for additional encryption.
            
        Returns:
            List of docker -e arguments.
        """
        import base64
        
        docker_args = []
        
        for name, value in secrets.items():
            # Base64 encode (not truly secure, but obscures)
            encoded = base64.b64encode(value.encode()).decode()
            docker_args.extend(["-e", f"{name}_B64={encoded}"])
        
        return docker_args
    
    def cleanup(self) -> None:
        """Clean up temporary secret directories."""
        import shutil
        
        for temp_dir in self._temp_dirs:
            try:
                shutil.rmtree(temp_dir)
                logger.debug(f"Cleaned up secrets directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to clean up secrets: {e}")
        
        self._temp_dirs.clear()
    
    def mask_secret_in_output(self, output: str, secrets: dict[str, str]) -> str:
        """Mask secret values in output string.
        
        Args:
            output: String that may contain secrets.
            secrets: Dictionary of secrets to mask.
            
        Returns:
            Output with secrets replaced by [MASKED].
        """
        if not self.mask_in_logs:
            return output
        
        masked = output
        for name, value in secrets.items():
            if value and len(value) > 3:
                masked = masked.replace(value, f"[{name}:MASKED]")
        
        return masked


@dataclass
class SandboxConfig:
    """Complete sandbox configuration for container execution.
    
    Combines network policy, resource limits, and secret injection.
    
    Attributes:
        network: Network policy for the container.
        resources: Resource limits for the container.
        secrets: Secret injector for the container.
        workdir: Working directory inside container.
        user: User to run as inside container.
        timeout_seconds: Maximum execution time.
    """
    
    network: NetworkPolicy = field(default_factory=NetworkPolicy)
    resources: ResourceLimits = field(default_factory=ResourceLimits)
    secrets: SecretInjector = field(default_factory=SecretInjector)
    workdir: str = "/workspace"
    user: str = "1000:1000"  # Non-root user
    timeout_seconds: int = 300  # 5 minutes default
    
    def to_docker_args(self, secrets: Optional[dict[str, str]] = None) -> list[str]:
        """Generate complete docker run arguments.
        
        Args:
            secrets: Optional secrets to inject.
            
        Returns:
            List of docker CLI arguments.
        """
        args = []
        
        # Network policy
        args.extend(self.network.to_docker_args())
        
        # Resource limits
        args.extend(self.resources.to_docker_args())
        
        # User
        args.extend(["--user", self.user])
        
        # Working directory
        args.extend(["--workdir", self.workdir])
        
        # Secrets (if provided)
        if secrets:
            _, secret_args = self.secrets.inject_secrets_as_files(secrets)
            args.extend(secret_args)
        
        return args


class SecureSandbox:
    """Secure sandbox for executing agent code in containers.
    
    Wraps Docker execution with security policies.
    """
    
    def __init__(self, config: Optional[SandboxConfig] = None) -> None:
        """Initialize the secure sandbox.
        
        Args:
            config: Sandbox configuration.
        """
        self.config = config or SandboxConfig()
        self._active_containers: list[str] = []
    
    async def setup_network(self) -> bool:
        """Set up Docker network with security policies.
        
        Creates the aurora-sandbox network if it doesn't exist.
        
        Returns:
            True if network is ready.
        """
        try:
            # Check if network exists
            result = subprocess.run(
                ["docker", "network", "ls", "--format", "{{.Name}}"],
                capture_output=True,
                text=True,
            )
            
            if "aurora-sandbox" in result.stdout:
                logger.debug("aurora-sandbox network already exists")
                return True
            
            # Create network with isolation
            subprocess.run(
                [
                    "docker", "network", "create",
                    "--driver", "bridge",
                    "--internal",  # No external access by default
                    "--opt", "com.docker.network.bridge.enable_icc=false",
                    "aurora-sandbox",
                ],
                check=True,
            )
            
            logger.info("Created aurora-sandbox network")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to setup network: {e}")
            return False
    
    async def run(
        self,
        image: str,
        command: list[str],
        volumes: Optional[dict[str, str]] = None,
        secrets: Optional[dict[str, str]] = None,
        env: Optional[dict[str, str]] = None,
    ) -> tuple[int, str, str]:
        """Run a command in a sandboxed container.
        
        Args:
            image: Docker image to use.
            command: Command to execute.
            volumes: Optional volume mounts (source -> target).
            secrets: Optional secrets to inject.
            env: Optional environment variables.
            
        Returns:
            Tuple of (exit_code, stdout, stderr).
        """
        import asyncio
        
        docker_args = ["docker", "run", "--rm"]
        
        # Add sandbox configuration
        docker_args.extend(self.config.to_docker_args(secrets))
        
        # Add volumes
        if volumes:
            for source, target in volumes.items():
                docker_args.extend(["-v", f"{source}:{target}"])
        
        # Add environment variables (non-secret)
        if env:
            for key, value in env.items():
                docker_args.extend(["-e", f"{key}={value}"])
        
        # Add image and command
        docker_args.append(image)
        docker_args.extend(command)
        
        logger.info(f"Running sandboxed container: {image}")
        logger.debug(f"Command: {' '.join(docker_args)}")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *docker_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=self.config.timeout_seconds,
                )
            except asyncio.TimeoutError:
                process.kill()
                await process.wait()
                return -1, "", f"Execution timed out after {self.config.timeout_seconds}s"
            
            stdout_str = stdout.decode() if stdout else ""
            stderr_str = stderr.decode() if stderr else ""
            
            # Mask secrets in output
            if secrets:
                stdout_str = self.config.secrets.mask_secret_in_output(stdout_str, secrets)
                stderr_str = self.config.secrets.mask_secret_in_output(stderr_str, secrets)
            
            return process.returncode or 0, stdout_str, stderr_str
            
        except Exception as e:
            logger.error(f"Container execution failed: {e}")
            return -1, "", str(e)
        finally:
            # Cleanup secrets
            if secrets:
                self.config.secrets.cleanup()
    
    def cleanup(self) -> None:
        """Clean up any remaining resources."""
        self.config.secrets.cleanup()
        
        # Kill any orphaned containers
        for container_id in self._active_containers:
            try:
                subprocess.run(
                    ["docker", "kill", container_id],
                    capture_output=True,
                )
            except Exception:
                pass
        
        self._active_containers.clear()


if __name__ == "__main__":
    # Demo sandbox configuration
    config = SandboxConfig(
        network=NetworkPolicy(
            isolation_level=NetworkIsolationLevel.RESTRICTED,
            allowed_hosts=["pypi.org", "github.com"],
        ),
        resources=ResourceLimits(
            memory_mb=1024,
            cpu_cores=1.0,
            read_only_rootfs=False,  # Allow writes for pip install
        ),
    )
    
    sandbox = SecureSandbox(config)
    
    print("Sandbox Configuration:")
    print(f"  Network: {config.network.isolation_level.value}")
    print(f"  Allowed hosts: {config.network.allowed_hosts[:3]}...")
    print(f"  Memory: {config.resources.memory_mb}MB")
    print(f"  CPU: {config.resources.cpu_cores} cores")
    print(f"  Read-only: {config.resources.read_only_rootfs}")
    print(f"\nDocker args: {' '.join(config.to_docker_args())}")
