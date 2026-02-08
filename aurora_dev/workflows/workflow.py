"""
LangGraph workflow state machine for AURORA-DEV.

This module provides the core workflow engine using LangGraph
for agent coordination, parallel execution, and state management.

Example usage:
    >>> from aurora_dev.workflows import WorkflowEngine, WorkflowState
    >>> engine = WorkflowEngine()
    >>> state = WorkflowState(
    ...     task_id="task-123",
    ...     task_type="feature",
    ...     description="Add user wishlist feature",
    ... )
    >>> result = await engine.run(state)
"""
import asyncio
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional, TypedDict

from langgraph.graph import END, StateGraph

from aurora_dev.core.logging import get_logger


logger = get_logger(__name__)


class WorkflowStatus(Enum):
    """Status of a workflow execution."""
    
    PENDING = "pending"
    PLANNING = "planning"
    EXECUTING = "executing"
    TESTING = "testing"
    REFLEXION = "reflexion"
    REVIEWING = "reviewing"
    DEPLOYING = "deploying"
    COMPLETED = "completed"
    FAILED = "failed"


class PhaseResult(TypedDict, total=False):
    """Result from a workflow phase."""
    
    agent: str
    status: str
    output: Any
    duration_ms: float
    error: Optional[str]
    needs_reflexion: bool


class WorkflowState(TypedDict, total=False):
    """
    State for LangGraph workflow execution.
    
    This typed dict is passed through the graph and modified
    by each node. LangGraph uses this to track execution state.
    
    Attributes:
        task_id: Unique task identifier.
        task_type: Type of task (feature, bugfix, refactor).
        description: Human-readable task description.
        status: Current workflow status.
        current_phase: Current execution phase name.
        attempt_number: Current retry attempt (1-5).
        max_attempts: Maximum retry attempts.
        phase_results: Results from each completed phase.
        reflections: Accumulated reflection outputs.
        final_result: Final workflow output.
        error: Error message if failed.
        metadata: Additional workflow metadata.
    """
    
    task_id: str
    task_type: str
    description: str
    status: str
    current_phase: str
    attempt_number: int
    max_attempts: int
    phase_results: dict[str, PhaseResult]
    reflections: list[dict[str, Any]]
    final_result: Optional[dict[str, Any]]
    error: Optional[str]
    metadata: dict[str, Any]


def create_initial_state(
    task_type: str,
    description: str,
    task_id: Optional[str] = None,
    max_attempts: int = 5,
    metadata: Optional[dict] = None,
) -> WorkflowState:
    """
    Create initial workflow state.
    
    Args:
        task_type: Type of task (feature, bugfix, refactor).
        description: Task description.
        task_id: Optional task ID (generated if not provided).
        max_attempts: Maximum reflexion retry attempts.
        metadata: Additional metadata.
        
    Returns:
        Initialized WorkflowState.
    """
    return WorkflowState(
        task_id=task_id or str(uuid.uuid4()),
        task_type=task_type,
        description=description,
        status=WorkflowStatus.PENDING.value,
        current_phase="init",
        attempt_number=1,
        max_attempts=max_attempts,
        phase_results={},
        reflections=[],
        final_result=None,
        error=None,
        metadata=metadata or {},
    )


@dataclass
class AgentNode:
    """
    Wrapper to run an agent as a LangGraph node.
    
    This class provides a callable interface for agents
    that can be used as nodes in a LangGraph workflow.
    
    Attributes:
        name: Node name for the graph.
        agent_factory: Factory function to create agent instance.
        task_builder: Function to build task dict from state.
    """
    
    name: str
    agent_factory: Callable[[], Any]
    task_builder: Callable[[WorkflowState], dict[str, Any]]
    
    async def __call__(self, state: WorkflowState) -> WorkflowState:
        """
        Execute the agent and update workflow state.
        
        Args:
            state: Current workflow state.
            
        Returns:
            Updated workflow state with phase result.
        """
        import time
        
        start_time = time.time()
        agent = self.agent_factory()
        task = self.task_builder(state)
        
        logger.info(
            f"Executing agent node: {self.name}",
            extra={"task_id": state["task_id"], "phase": self.name},
        )
        
        try:
            # Execute agent
            response = agent.execute(task)
            duration_ms = (time.time() - start_time) * 1000
            
            # Build phase result
            result: PhaseResult = {
                "agent": self.name,
                "status": "success" if response.success else "failed",
                "output": response.content,
                "duration_ms": duration_ms,
                "error": response.error,
                "needs_reflexion": not response.success,
            }
            
            # Update state
            new_results = dict(state.get("phase_results", {}))
            new_results[self.name] = result
            
            return WorkflowState(
                **state,
                current_phase=self.name,
                phase_results=new_results,
                status=WorkflowStatus.REFLEXION.value if result["needs_reflexion"] 
                       else state["status"],
            )
            
        except Exception as e:
            logger.error(f"Agent node {self.name} failed: {e}")
            duration_ms = (time.time() - start_time) * 1000
            
            result: PhaseResult = {
                "agent": self.name,
                "status": "error",
                "output": None,
                "duration_ms": duration_ms,
                "error": str(e),
                "needs_reflexion": True,
            }
            
            new_results = dict(state.get("phase_results", {}))
            new_results[self.name] = result
            
            return WorkflowState(
                **state,
                current_phase=self.name,
                phase_results=new_results,
                status=WorkflowStatus.REFLEXION.value,
                error=str(e),
            )


class ConditionalRouter:
    """
    Router for conditional edges in LangGraph.
    
    Routes workflow based on phase results, reflexion needs,
    and attempt count.
    """
    
    @staticmethod
    def should_reflexion(state: WorkflowState) -> str:
        """
        Determine if reflexion is needed.
        
        Args:
            state: Current workflow state.
            
        Returns:
            Next node name: "reflexion", "retry", or "continue".
        """
        current_phase = state.get("current_phase", "")
        phase_results = state.get("phase_results", {})
        attempt = state.get("attempt_number", 1)
        max_attempts = state.get("max_attempts", 5)
        
        if current_phase not in phase_results:
            return "continue"
        
        result = phase_results[current_phase]
        
        if result.get("needs_reflexion"):
            if attempt >= max_attempts:
                logger.warning(
                    f"Max attempts ({max_attempts}) reached for {current_phase}"
                )
                return "fail"
            return "reflexion"
        
        return "continue"
    
    @staticmethod
    def route_by_task_type(state: WorkflowState) -> str:
        """
        Route based on task type.
        
        Args:
            state: Current workflow state.
            
        Returns:
            Next node name based on task type.
        """
        task_type = state.get("task_type", "feature")
        
        routes = {
            "feature": "planning",
            "bugfix": "investigation",
            "refactor": "analysis",
            "security": "audit",
        }
        
        return routes.get(task_type, "planning")
    
    @staticmethod
    def route_after_testing(state: WorkflowState) -> str:
        """
        Route after testing phase.
        
        Args:
            state: Current workflow state.
            
        Returns:
            Next node: "review", "reflexion", or "fail".
        """
        phase_results = state.get("phase_results", {})
        testing_result = phase_results.get("testing", {})
        
        if testing_result.get("status") == "success":
            return "review"
        elif testing_result.get("needs_reflexion"):
            return "reflexion"
        else:
            return "fail"


@dataclass
class WorkflowEngine:
    """
    Engine for executing LangGraph workflows.
    
    This class manages workflow execution, including
    parallel agent coordination and state persistence.
    
    Attributes:
        project_id: Project identifier.
        graph: The compiled LangGraph.
    """
    
    project_id: Optional[str] = None
    graph: Optional[Any] = None
    _execution_history: list[dict] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize logger."""
        self._logger = get_logger(__name__, project_id=self.project_id)
    
    async def run(
        self,
        initial_state: WorkflowState,
        graph: Optional[StateGraph] = None,
    ) -> WorkflowState:
        """
        Execute a workflow from initial state.
        
        Args:
            initial_state: Starting workflow state.
            graph: Optional custom graph (uses default if not provided).
            
        Returns:
            Final workflow state after execution.
        """
        if graph is None and self.graph is None:
            raise ValueError("No graph provided. Build a graph first.")
        
        execution_graph = graph or self.graph
        
        self._logger.info(
            f"Starting workflow: {initial_state['task_type']}",
            extra={"task_id": initial_state["task_id"]},
        )
        
        start_time = datetime.now()
        
        try:
            # Run the graph
            final_state = await execution_graph.ainvoke(initial_state)
            
            # Record execution
            execution_record = {
                "task_id": initial_state["task_id"],
                "task_type": initial_state["task_type"],
                "start_time": start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "status": final_state.get("status"),
                "attempts": final_state.get("attempt_number", 1),
            }
            self._execution_history.append(execution_record)
            
            self._logger.info(
                f"Workflow completed: {final_state.get('status')}",
                extra={"task_id": initial_state["task_id"]},
            )
            
            return final_state
            
        except Exception as e:
            self._logger.error(f"Workflow execution failed: {e}")
            
            return WorkflowState(
                **initial_state,
                status=WorkflowStatus.FAILED.value,
                error=str(e),
            )
    
    async def run_parallel(
        self,
        states: list[WorkflowState],
        graph: Optional[StateGraph] = None,
    ) -> list[WorkflowState]:
        """
        Execute multiple workflows in parallel.
        
        Args:
            states: List of initial workflow states.
            graph: Optional custom graph.
            
        Returns:
            List of final workflow states.
        """
        self._logger.info(f"Starting {len(states)} parallel workflows")
        
        tasks = [self.run(state, graph) for state in states]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                final_results.append(WorkflowState(
                    **states[i],
                    status=WorkflowStatus.FAILED.value,
                    error=str(result),
                ))
            else:
                final_results.append(result)
        
        return final_results
    
    def get_execution_history(self) -> list[dict]:
        """Get history of workflow executions."""
        return list(self._execution_history)


# Utility functions for workflow building

def create_planning_node(state: WorkflowState) -> WorkflowState:
    """
    Planning phase node.
    
    Parses requirements, creates task graph, assigns agents.
    """
    logger.info(f"Planning phase for task: {state['task_id']}")
    
    # Simulate planning (actual implementation would use Maestro)
    new_state = WorkflowState(
        **state,
        current_phase="planning",
        status=WorkflowStatus.PLANNING.value,
        phase_results={
            **state.get("phase_results", {}),
            "planning": {
                "agent": "maestro",
                "status": "success",
                "output": {"tasks": [], "assignments": {}},
                "duration_ms": 0,
                "needs_reflexion": False,
            }
        },
    )
    
    return new_state


def create_completion_node(state: WorkflowState) -> WorkflowState:
    """
    Completion node - marks workflow as done.
    """
    logger.info(f"Completing workflow: {state['task_id']}")
    
    return WorkflowState(
        **state,
        status=WorkflowStatus.COMPLETED.value,
        final_result={
            "phases_completed": list(state.get("phase_results", {}).keys()),
            "total_attempts": state.get("attempt_number", 1),
            "reflections_count": len(state.get("reflections", [])),
        },
    )


def create_failure_node(state: WorkflowState) -> WorkflowState:
    """
    Failure node - marks workflow as failed.
    """
    logger.error(f"Workflow failed: {state['task_id']}")
    
    return WorkflowState(
        **state,
        status=WorkflowStatus.FAILED.value,
        error=state.get("error") or "Maximum retry attempts exceeded",
    )
