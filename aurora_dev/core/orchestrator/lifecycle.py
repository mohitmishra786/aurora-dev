"""
Agent Lifecycle Manager for AURORA-DEV.

Provides agent spawning, termination, session management,
and health monitoring for the agent ecosystem.
"""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional, Type
from uuid import uuid4


logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent lifecycle states.
    
    Tracks the lifecycle of an agent instance.
    """
    
    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    PAUSED = "paused"
    STOPPING = "stopping"
    TERMINATED = "terminated"
    ERROR = "error"


@dataclass
class AgentSession:
    """Session information for an agent instance.
    
    Attributes:
        session_id: Unique session identifier.
        agent_type: Type of agent.
        project_id: Associated project ID.
        state: Current agent state.
        created_at: Session creation timestamp.
        started_at: Optional start timestamp.
        terminated_at: Optional termination timestamp.
        tasks_completed: Number of tasks completed.
        tasks_failed: Number of tasks failed.
        last_heartbeat: Last health check timestamp.
        metadata: Additional session metadata.
    """
    
    session_id: str = field(default_factory=lambda: str(uuid4()))
    agent_type: str = ""
    project_id: Optional[str] = None
    state: AgentState = AgentState.CREATED
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    terminated_at: Optional[datetime] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    last_heartbeat: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_active(self) -> bool:
        """Check if agent is in an active state.
        
        Returns:
            True if agent is active.
        """
        return self.state in {AgentState.READY, AgentState.BUSY, AgentState.INITIALIZING}
    
    @property
    def uptime_seconds(self) -> Optional[float]:
        """Calculate session uptime.
        
        Returns:
            Uptime in seconds if started.
        """
        if self.started_at is None:
            return None
        end_time = self.terminated_at or datetime.now(timezone.utc)
        return (end_time - self.started_at).total_seconds()
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation.
        """
        return {
            "session_id": self.session_id,
            "agent_type": self.agent_type,
            "project_id": self.project_id,
            "state": self.state.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "terminated_at": self.terminated_at.isoformat() if self.terminated_at else None,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "last_heartbeat": self.last_heartbeat.isoformat(),
            "uptime_seconds": self.uptime_seconds,
        }


@dataclass
class HealthCheck:
    """Health check result for an agent.
    
    Attributes:
        session_id: Agent session ID.
        healthy: Whether agent is healthy.
        timestamp: Check timestamp.
        latency_ms: Response latency in milliseconds.
        memory_mb: Memory usage in MB.
        cpu_percent: CPU usage percentage.
        error: Optional error message.
    """
    
    session_id: str
    healthy: bool
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    latency_ms: float = 0.0
    memory_mb: float = 0.0
    cpu_percent: float = 0.0
    error: Optional[str] = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary.
        
        Returns:
            Dictionary representation.
        """
        return {
            "session_id": self.session_id,
            "healthy": self.healthy,
            "timestamp": self.timestamp.isoformat(),
            "latency_ms": self.latency_ms,
            "memory_mb": self.memory_mb,
            "cpu_percent": self.cpu_percent,
            "error": self.error,
        }


class AgentLifecycleManager:
    """Manager for agent lifecycle and health monitoring.
    
    Handles agent spawning, termination, session management,
    and health checks.
    
    Attributes:
        sessions: Active agent sessions.
        agent_registry: Registry of available agent types.
        max_agents: Maximum concurrent agents.
    """
    
    def __init__(self, max_agents: int = 20) -> None:
        """Initialize the lifecycle manager.
        
        Args:
            max_agents: Maximum concurrent agents.
        """
        self.sessions: dict[str, AgentSession] = {}
        self.agent_registry: dict[str, Type] = {}
        self.max_agents = max_agents
        self._lock = asyncio.Lock()
        
        self._register_default_agents()
        
        logger.info(f"AgentLifecycleManager initialized (max_agents={max_agents})")
    
    def _register_default_agents(self) -> None:
        """Register default agent types."""
        from aurora_dev.agents.base_agent import BaseAgent
        
        agent_types = [
            "maestro",
            "memory_coordinator",
            "architect",
            "backend",
            "frontend",
            "database",
            "test_engineer",
            "security_auditor",
            "code_reviewer",
            "devops",
        ]
        
        for agent_type in agent_types:
            self.agent_registry[agent_type] = BaseAgent
    
    def register_agent_type(
        self,
        agent_type: str,
        agent_class: Type,
    ) -> None:
        """Register an agent type.
        
        Args:
            agent_type: Type identifier.
            agent_class: Agent class.
        """
        self.agent_registry[agent_type] = agent_class
        logger.info(f"Registered agent type: {agent_type}")
    
    async def spawn(
        self,
        agent_type: str,
        project_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> AgentSession:
        """Spawn a new agent instance.
        
        Args:
            agent_type: Type of agent to spawn.
            project_id: Associated project ID.
            metadata: Additional metadata.
            
        Returns:
            Agent session.
            
        Raises:
            ValueError: If agent type is unknown or capacity reached.
        """
        async with self._lock:
            if agent_type not in self.agent_registry:
                raise ValueError(f"Unknown agent type: {agent_type}")
            
            active_count = sum(1 for s in self.sessions.values() if s.is_active)
            if active_count >= self.max_agents:
                raise ValueError(f"Maximum agent capacity reached: {self.max_agents}")
            
            session = AgentSession(
                agent_type=agent_type,
                project_id=project_id,
                state=AgentState.INITIALIZING,
                metadata=metadata or {},
            )
            
            self.sessions[session.session_id] = session
            
            logger.info(f"Spawned agent: {agent_type} ({session.session_id})")
        
        try:
            await self._initialize_agent(session)
            session.state = AgentState.READY
            session.started_at = datetime.now(timezone.utc)
            logger.info(f"Agent ready: {session.session_id}")
        except Exception as e:
            session.state = AgentState.ERROR
            logger.error(f"Agent initialization failed: {e}")
            raise
        
        return session
    
    async def _initialize_agent(self, session: AgentSession) -> None:
        """Initialize an agent instance.
        
        Args:
            session: Agent session.
        """
        await asyncio.sleep(0.1)
    
    async def terminate(
        self,
        session_id: str,
        force: bool = False,
    ) -> bool:
        """Terminate an agent instance.
        
        Args:
            session_id: Session identifier.
            force: Force termination without cleanup.
            
        Returns:
            True if termination was successful.
        """
        session = self.sessions.get(session_id)
        if session is None:
            logger.warning(f"Session not found: {session_id}")
            return False
        
        if not session.is_active and not force:
            logger.warning(f"Session already inactive: {session_id}")
            return False
        
        session.state = AgentState.STOPPING
        
        if not force:
            try:
                await self._cleanup_agent(session)
            except Exception as e:
                logger.error(f"Agent cleanup failed: {e}")
        
        session.state = AgentState.TERMINATED
        session.terminated_at = datetime.now(timezone.utc)
        
        logger.info(f"Agent terminated: {session_id}")
        
        return True
    
    async def _cleanup_agent(self, session: AgentSession) -> None:
        """Clean up agent resources.
        
        Args:
            session: Agent session.
        """
        await asyncio.sleep(0.05)
    
    def pause(self, session_id: str) -> bool:
        """Pause an agent.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            True if pause was successful.
        """
        session = self.sessions.get(session_id)
        if session is None or session.state != AgentState.READY:
            return False
        
        session.state = AgentState.PAUSED
        logger.info(f"Agent paused: {session_id}")
        
        return True
    
    def resume(self, session_id: str) -> bool:
        """Resume a paused agent.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            True if resume was successful.
        """
        session = self.sessions.get(session_id)
        if session is None or session.state != AgentState.PAUSED:
            return False
        
        session.state = AgentState.READY
        logger.info(f"Agent resumed: {session_id}")
        
        return True
    
    def update_state(
        self,
        session_id: str,
        state: AgentState,
    ) -> None:
        """Update agent state.
        
        Args:
            session_id: Session identifier.
            state: New state.
        """
        session = self.sessions.get(session_id)
        if session:
            session.state = state
            logger.debug(f"Agent state updated: {session_id} -> {state.value}")
    
    def record_task_completion(
        self,
        session_id: str,
        success: bool,
    ) -> None:
        """Record task completion for an agent.
        
        Args:
            session_id: Session identifier.
            success: Whether task was successful.
        """
        session = self.sessions.get(session_id)
        if session:
            if success:
                session.tasks_completed += 1
            else:
                session.tasks_failed += 1
    
    async def health_check(
        self,
        session_id: str,
    ) -> HealthCheck:
        """Perform health check on an agent.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            Health check result.
        """
        session = self.sessions.get(session_id)
        
        if session is None:
            return HealthCheck(
                session_id=session_id,
                healthy=False,
                error="Session not found",
            )
        
        start_time = datetime.now(timezone.utc)
        
        try:
            await asyncio.sleep(0.01)
            
            latency = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            session.last_heartbeat = datetime.now(timezone.utc)
            
            return HealthCheck(
                session_id=session_id,
                healthy=session.is_active,
                latency_ms=latency,
            )
        except Exception as e:
            return HealthCheck(
                session_id=session_id,
                healthy=False,
                error=str(e),
            )
    
    async def health_check_all(self) -> list[HealthCheck]:
        """Perform health checks on all active agents.
        
        Returns:
            List of health check results.
        """
        results = []
        
        for session_id, session in self.sessions.items():
            if session.is_active:
                result = await self.health_check(session_id)
                results.append(result)
        
        return results
    
    def get_session(self, session_id: str) -> Optional[AgentSession]:
        """Get an agent session.
        
        Args:
            session_id: Session identifier.
            
        Returns:
            Agent session or None.
        """
        return self.sessions.get(session_id)
    
    def list_sessions(
        self,
        project_id: Optional[str] = None,
        agent_type: Optional[str] = None,
        active_only: bool = False,
    ) -> list[AgentSession]:
        """List agent sessions with optional filtering.
        
        Args:
            project_id: Filter by project ID.
            agent_type: Filter by agent type.
            active_only: Only return active sessions.
            
        Returns:
            List of matching sessions.
        """
        sessions = list(self.sessions.values())
        
        if project_id:
            sessions = [s for s in sessions if s.project_id == project_id]
        
        if agent_type:
            sessions = [s for s in sessions if s.agent_type == agent_type]
        
        if active_only:
            sessions = [s for s in sessions if s.is_active]
        
        return sessions
    
    def get_statistics(self) -> dict[str, Any]:
        """Get lifecycle manager statistics.
        
        Returns:
            Dictionary with statistics.
        """
        sessions = list(self.sessions.values())
        
        active = sum(1 for s in sessions if s.is_active)
        by_type = {}
        
        for session in sessions:
            if session.agent_type not in by_type:
                by_type[session.agent_type] = {"active": 0, "total": 0}
            by_type[session.agent_type]["total"] += 1
            if session.is_active:
                by_type[session.agent_type]["active"] += 1
        
        total_completed = sum(s.tasks_completed for s in sessions)
        total_failed = sum(s.tasks_failed for s in sessions)
        
        return {
            "total_sessions": len(sessions),
            "active_sessions": active,
            "capacity_used": active / self.max_agents if self.max_agents > 0 else 0,
            "by_type": by_type,
            "total_tasks_completed": total_completed,
            "total_tasks_failed": total_failed,
            "success_rate": total_completed / (total_completed + total_failed) if (total_completed + total_failed) > 0 else 0,
        }
    
    async def cleanup_terminated(self) -> int:
        """Clean up terminated sessions.
        
        Returns:
            Number of sessions cleaned up.
        """
        terminated = [
            sid for sid, s in self.sessions.items()
            if s.state == AgentState.TERMINATED
        ]
        
        for sid in terminated:
            del self.sessions[sid]
        
        if terminated:
            logger.info(f"Cleaned up {len(terminated)} terminated sessions")
        
        return len(terminated)


if __name__ == "__main__":
    async def main():
        manager = AgentLifecycleManager()
        
        session = await manager.spawn(
            agent_type="backend",
            project_id="proj-123",
        )
        print(f"Spawned: {session.to_dict()}")
        
        health = await manager.health_check(session.session_id)
        print(f"Health: {health.to_dict()}")
        
        print(f"Stats: {manager.get_statistics()}")
        
        await manager.terminate(session.session_id)
        print(f"Final state: {session.state.value}")
    
    asyncio.run(main())
