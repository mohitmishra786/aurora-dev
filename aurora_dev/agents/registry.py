"""
Agent Registry for AURORA-DEV.

This module provides a centralized registry for managing agent instances,
enabling discovery, lifecycle management, and agent lookup.
"""
from threading import Lock
from typing import Any, Optional

from aurora_dev.agents.base_agent import AgentRole, AgentStatus, BaseAgent
from aurora_dev.core.logging import get_logger

logger = get_logger("agent_registry")


class AgentRegistry:
    """
    Centralized registry for managing agent instances.
    
    Provides thread-safe registration, unregistration, and lookup of agents.
    Supports filtering by role, status, and project.
    """
    
    _instance: Optional["AgentRegistry"] = None
    _lock: Lock = Lock()
    
    def __new__(cls) -> "AgentRegistry":
        """Implement singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        """Initialize the registry."""
        if self._initialized:
            return
            
        self._agents: dict[str, BaseAgent] = {}
        self._role_index: dict[AgentRole, set[str]] = {}
        self._project_index: dict[str, set[str]] = {}
        self._registry_lock = Lock()
        self._initialized = True
        
        logger.info("Agent registry initialized")
    
    def register(self, agent: BaseAgent) -> None:
        """
        Register an agent with the registry.
        
        Args:
            agent: The agent to register.
            
        Raises:
            ValueError: If agent is already registered.
        """
        with self._registry_lock:
            if agent.agent_id in self._agents:
                raise ValueError(f"Agent {agent.agent_id} already registered")
            
            self._agents[agent.agent_id] = agent
            
            # Update role index
            if agent.role not in self._role_index:
                self._role_index[agent.role] = set()
            self._role_index[agent.role].add(agent.agent_id)
            
            # Update project index
            project_id = agent._project_id
            if project_id:
                if project_id not in self._project_index:
                    self._project_index[project_id] = set()
                self._project_index[project_id].add(agent.agent_id)
            
            logger.info(
                f"Agent registered: {agent.name}",
                extra={
                    "agent_id": agent.agent_id,
                    "role": agent.role.value,
                },
            )
    
    def unregister(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Unregister an agent from the registry.
        
        Args:
            agent_id: The agent ID to unregister.
            
        Returns:
            The unregistered agent, or None if not found.
        """
        with self._registry_lock:
            agent = self._agents.pop(agent_id, None)
            if agent:
                # Remove from role index
                if agent.role in self._role_index:
                    self._role_index[agent.role].discard(agent_id)
                    if not self._role_index[agent.role]:
                        del self._role_index[agent.role]
                
                # Remove from project index
                project_id = agent._project_id
                if project_id and project_id in self._project_index:
                    self._project_index[project_id].discard(agent_id)
                    if not self._project_index[project_id]:
                        del self._project_index[project_id]
                
                logger.info(
                    f"Agent unregistered: {agent.name}",
                    extra={"agent_id": agent_id},
                )
            
            return agent
    
    def get(self, agent_id: str) -> Optional[BaseAgent]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: The agent ID to look up.
            
        Returns:
            The agent, or None if not found.
        """
        return self._agents.get(agent_id)
    
    def get_by_role(self, role: AgentRole) -> list[BaseAgent]:
        """
        Get all agents with a specific role.
        
        Args:
            role: The agent role to filter by.
            
        Returns:
            List of agents with the specified role.
        """
        agent_ids = self._role_index.get(role, set())
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]
    
    def get_by_project(self, project_id: str) -> list[BaseAgent]:
        """
        Get all agents assigned to a project.
        
        Args:
            project_id: The project ID to filter by.
            
        Returns:
            List of agents assigned to the project.
        """
        agent_ids = self._project_index.get(project_id, set())
        return [self._agents[aid] for aid in agent_ids if aid in self._agents]
    
    def get_by_status(self, status: AgentStatus) -> list[BaseAgent]:
        """
        Get all agents with a specific status.
        
        Args:
            status: The status to filter by.
            
        Returns:
            List of agents with the specified status.
        """
        return [a for a in self._agents.values() if a.status == status]
    
    def get_available(self, role: Optional[AgentRole] = None) -> list[BaseAgent]:
        """
        Get all available (idle) agents.
        
        Args:
            role: Optional role to filter by.
            
        Returns:
            List of available agents.
        """
        agents = self.get_by_status(AgentStatus.IDLE)
        if role:
            agents = [a for a in agents if a.role == role]
        return agents
    
    def get_all(self) -> list[BaseAgent]:
        """
        Get all registered agents.
        
        Returns:
            List of all agents.
        """
        return list(self._agents.values())
    
    def count(self) -> int:
        """
        Get the total number of registered agents.
        
        Returns:
            Number of agents.
        """
        return len(self._agents)
    
    def get_stats(self) -> dict[str, Any]:
        """
        Get registry statistics.
        
        Returns:
            Dictionary with registry statistics.
        """
        status_counts: dict[str, int] = {}
        role_counts: dict[str, int] = {}
        total_tokens = 0
        total_requests = 0
        
        for agent in self._agents.values():
            # Count by status
            status = agent.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
            
            # Count by role
            role = agent.role.value
            role_counts[role] = role_counts.get(role, 0) + 1
            
            # Sum tokens
            total_tokens += agent.total_usage.total_tokens
            total_requests += agent.request_count
        
        return {
            "total_agents": self.count(),
            "agents_by_status": status_counts,
            "agents_by_role": role_counts,
            "total_tokens_used": total_tokens,
            "total_api_requests": total_requests,
            "projects": list(self._project_index.keys()),
        }
    
    def clear(self) -> None:
        """Clear all registered agents."""
        with self._registry_lock:
            self._agents.clear()
            self._role_index.clear()
            self._project_index.clear()
            logger.warning("Agent registry cleared")
    
    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (for testing)."""
        with cls._lock:
            if cls._instance:
                cls._instance._agents.clear()
                cls._instance._role_index.clear()
                cls._instance._project_index.clear()
            cls._instance = None


def get_registry() -> AgentRegistry:
    """
    Get the global agent registry instance.
    
    Returns:
        The AgentRegistry singleton.
    """
    return AgentRegistry()
