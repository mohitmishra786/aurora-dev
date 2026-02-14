"""
Agent Health Monitor for AURORA-DEV.

Detects stuck agents, monitors heartbeats, and triggers
auto-recovery actions (restart or re-assignment).

Gap B6: Missing stuck-agent detection and recovery.
"""
import asyncio
import time
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


@dataclass
class AgentHeartbeat:
    """Heartbeat record for an agent."""
    
    agent_id: str
    last_heartbeat: float = 0.0
    last_task_id: Optional[str] = None
    status: str = "idle"
    consecutive_stuck: int = 0
    
    @property
    def seconds_since_heartbeat(self) -> float:
        if self.last_heartbeat == 0:
            return 0.0
        return time.time() - self.last_heartbeat
    
    def beat(self, task_id: Optional[str] = None, status: str = "working") -> None:
        self.last_heartbeat = time.time()
        self.last_task_id = task_id
        self.status = status
        self.consecutive_stuck = 0


class AgentHealthMonitor:
    """Monitors agent health and detects stuck agents.
    
    Runs a polling loop that checks agent heartbeats every
    `poll_interval_seconds`. If an agent hasn't sent a heartbeat
    within `stuck_threshold_seconds`, it's marked as stuck and
    recovery action is triggered.
    
    Example:
        >>> monitor = AgentHealthMonitor(
        ...     stuck_threshold=900,  # 15 minutes
        ...     poll_interval=30,     # check every 30s
        ... )
        >>> monitor.register_agent("agent-001")
        >>> monitor.on_stuck(lambda aid, tid: reassign(aid, tid))
        >>> await monitor.start()
    """
    
    def __init__(
        self,
        stuck_threshold: float = 900.0,   # 15 minutes
        poll_interval: float = 30.0,       # 30 seconds
        max_restarts: int = 3,
    ) -> None:
        self._stuck_threshold = stuck_threshold
        self._poll_interval = poll_interval
        self._max_restarts = max_restarts
        self._heartbeats: dict[str, AgentHeartbeat] = {}
        self._stuck_callbacks: list[Callable[[str, Optional[str]], None]] = []
        self._running = False
        self._monitor_task: Optional[asyncio.Task[None]] = None
    
    def register_agent(self, agent_id: str) -> None:
        """Register an agent for health monitoring."""
        self._heartbeats[agent_id] = AgentHeartbeat(
            agent_id=agent_id,
            last_heartbeat=time.time(),
        )
    
    def record_heartbeat(
        self,
        agent_id: str,
        task_id: Optional[str] = None,
        status: str = "working",
    ) -> None:
        """Record a heartbeat from an agent."""
        if agent_id not in self._heartbeats:
            self.register_agent(agent_id)
        self._heartbeats[agent_id].beat(task_id, status)
    
    def on_stuck(self, callback: Callable[[str, Optional[str]], None]) -> None:
        """Register a callback for stuck agent events.
        
        Args:
            callback: Called with (agent_id, task_id) when agent is stuck.
        """
        self._stuck_callbacks.append(callback)
    
    async def start(self) -> None:
        """Start the health monitoring loop."""
        if self._running:
            return
        self._running = True
        self._monitor_task = asyncio.create_task(self._poll_loop())
        logger.info(
            f"Health monitor started: poll={self._poll_interval}s, "
            f"stuck_threshold={self._stuck_threshold}s"
        )
    
    async def stop(self) -> None:
        """Stop the health monitoring loop."""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitor stopped")
    
    async def _poll_loop(self) -> None:
        """Main polling loop."""
        while self._running:
            try:
                self._check_agents()
                await asyncio.sleep(self._poll_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(self._poll_interval)
    
    def _check_agents(self) -> None:
        """Check all agents for stuck status."""
        for agent_id, heartbeat in self._heartbeats.items():
            if heartbeat.status == "idle":
                continue
            
            elapsed = heartbeat.seconds_since_heartbeat
            
            if elapsed > self._stuck_threshold:
                heartbeat.consecutive_stuck += 1
                
                logger.warning(
                    f"Agent {agent_id} appears stuck: "
                    f"{elapsed:.0f}s since last heartbeat, "
                    f"consecutive={heartbeat.consecutive_stuck}"
                )
                
                if heartbeat.consecutive_stuck <= self._max_restarts:
                    self._trigger_recovery(agent_id, heartbeat.last_task_id)
                else:
                    logger.error(
                        f"Agent {agent_id} exceeded max restarts "
                        f"({self._max_restarts}), marking as dead"
                    )
                    heartbeat.status = "dead"
    
    def _trigger_recovery(
        self,
        agent_id: str,
        task_id: Optional[str],
    ) -> None:
        """Trigger recovery callbacks for a stuck agent."""
        for callback in self._stuck_callbacks:
            try:
                callback(agent_id, task_id)
            except Exception as e:
                logger.error(f"Stuck callback error for {agent_id}: {e}")
    
    def get_status(self) -> dict[str, Any]:
        """Get health status for all monitored agents.
        
        Returns:
            Dict with agent health information.
        """
        agents: dict[str, Any] = {}
        for agent_id, hb in self._heartbeats.items():
            agents[agent_id] = {
                "status": hb.status,
                "last_heartbeat_secs_ago": round(hb.seconds_since_heartbeat, 1),
                "last_task_id": hb.last_task_id,
                "consecutive_stuck": hb.consecutive_stuck,
                "is_stuck": (
                    hb.status == "working"
                    and hb.seconds_since_heartbeat > self._stuck_threshold
                ),
            }
        
        return {
            "running": self._running,
            "agent_count": len(self._heartbeats),
            "agents": agents,
        }
