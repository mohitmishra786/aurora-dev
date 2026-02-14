"""
LangGraph-based Orchestration Engine for AURORA-DEV.

Wraps the existing OrchestrationEngine with LangGraph StateGraph
for standardized state machine management and checkpointing.

This provides:
- Declarative state transitions between project phases
- Built-in state persistence and checkpointing
- Visualization of workflow graphs
- Conditional edge routing based on phase outcomes
"""
from enum import Enum
from typing import Any, TypedDict, Optional

from aurora_dev.core.logging import get_logger

logger = get_logger(__name__)

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False


class ProjectPhase(str, Enum):
    """Project lifecycle phases."""
    PLANNING = "planning"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    REVIEW = "review"
    DEPLOYMENT = "deployment"
    COMPLETED = "completed"
    FAILED = "failed"


class ProjectState(TypedDict):
    """State maintained across the orchestration graph."""
    project_id: str
    current_phase: str
    phase_results: dict[str, Any]
    error: Optional[str]
    metadata: dict[str, Any]
    task_count: int
    completed_tasks: int
    failed_tasks: int


class LangGraphOrchestrator:
    """LangGraph-based orchestrator wrapping the existing engine.
    
    Uses LangGraph's StateGraph to define phase transitions as a
    directed graph with conditional edges. Each node delegates to
    the existing OrchestrationEngine's phase execution methods.
    
    Example:
        >>> orchestrator = LangGraphOrchestrator(engine)
        >>> result = await orchestrator.run(project_id="my-project", goal="Build API")
    """

    def __init__(self, engine: Optional[Any] = None) -> None:
        """Initialize with an optional existing OrchestrationEngine.
        
        Args:
            engine: Existing OrchestrationEngine instance (optional).
        """
        if not LANGGRAPH_AVAILABLE:
            raise ImportError(
                "langgraph is not installed. "
                "Install it with: pip install langgraph"
            )
        
        self._engine = engine
        self._graph = self._build_graph()
        
        logger.info("LangGraph orchestrator initialized")

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine.
        
        Returns:
            Compiled StateGraph with phase nodes and transitions.
        """
        graph = StateGraph(ProjectState)
        
        # Add phase nodes
        graph.add_node("planning", self._execute_planning)
        graph.add_node("design", self._execute_design)
        graph.add_node("implementation", self._execute_implementation)
        graph.add_node("testing", self._execute_testing)
        graph.add_node("review", self._execute_review)
        graph.add_node("deployment", self._execute_deployment)
        
        # Set entry point
        graph.set_entry_point("planning")
        
        # Add conditional edges
        graph.add_conditional_edges(
            "planning",
            self._route_after_phase,
            {
                "design": "design",
                "failed": END,
            },
        )
        graph.add_conditional_edges(
            "design",
            self._route_after_phase,
            {
                "implementation": "implementation",
                "failed": END,
            },
        )
        graph.add_conditional_edges(
            "implementation",
            self._route_after_phase,
            {
                "testing": "testing",
                "failed": END,
            },
        )
        graph.add_conditional_edges(
            "testing",
            self._route_after_phase,
            {
                "review": "review",
                "implementation": "implementation",  # Loop back on test failure
                "failed": END,
            },
        )
        graph.add_conditional_edges(
            "review",
            self._route_after_phase,
            {
                "deployment": "deployment",
                "implementation": "implementation",  # Loop back on review rejection
                "failed": END,
            },
        )
        graph.add_conditional_edges(
            "deployment",
            self._route_after_phase,
            {
                "completed": END,
                "failed": END,
            },
        )
        
        return graph.compile()

    def _route_after_phase(self, state: ProjectState) -> str:
        """Determine the next phase based on current state.
        
        Args:
            state: Current project state.
            
        Returns:
            Name of the next phase or END.
        """
        current = state["current_phase"]
        error = state.get("error")
        
        if error:
            logger.warning(f"Phase {current} failed: {error}")
            return "failed"
        
        # Define phase transitions
        transitions = {
            ProjectPhase.PLANNING.value: "design",
            ProjectPhase.DESIGN.value: "implementation",
            ProjectPhase.IMPLEMENTATION.value: "testing",
            ProjectPhase.TESTING.value: self._route_testing(state),
            ProjectPhase.REVIEW.value: self._route_review(state),
            ProjectPhase.DEPLOYMENT.value: "completed",
        }
        
        next_phase = transitions.get(current, "failed")
        logger.info(f"Transitioning from {current} to {next_phase}")
        return next_phase

    def _route_testing(self, state: ProjectState) -> str:
        """Route after testing phase."""
        results = state["phase_results"].get("testing", {})
        if results.get("all_passed", False):
            return "review"
        if state["failed_tasks"] > state["task_count"] * 0.5:
            return "failed"
        return "implementation"  # Loop back for fixes

    def _route_review(self, state: ProjectState) -> str:
        """Route after review phase."""
        results = state["phase_results"].get("review", {})
        if results.get("approved", False):
            return "deployment"
        return "implementation"  # Loop back for revisions

    async def _execute_planning(self, state: ProjectState) -> ProjectState:
        """Execute the planning phase."""
        state["current_phase"] = ProjectPhase.PLANNING.value
        logger.info(f"Executing planning phase for {state['project_id']}")
        
        if self._engine:
            try:
                result = await self._engine._execute_planning_phase(state["metadata"])
                state["phase_results"]["planning"] = result or {}
            except Exception as e:
                state["error"] = str(e)
        else:
            state["phase_results"]["planning"] = {"status": "completed"}
        
        return state

    async def _execute_design(self, state: ProjectState) -> ProjectState:
        """Execute the design phase."""
        state["current_phase"] = ProjectPhase.DESIGN.value
        logger.info(f"Executing design phase for {state['project_id']}")
        
        if self._engine:
            try:
                result = await self._engine._execute_design_phase(state["metadata"])
                state["phase_results"]["design"] = result or {}
            except Exception as e:
                state["error"] = str(e)
        else:
            state["phase_results"]["design"] = {"status": "completed"}
        
        return state

    async def _execute_implementation(self, state: ProjectState) -> ProjectState:
        """Execute the implementation phase."""
        state["current_phase"] = ProjectPhase.IMPLEMENTATION.value
        logger.info(f"Executing implementation phase for {state['project_id']}")
        
        if self._engine:
            try:
                result = await self._engine._execute_implementation_phase(state["metadata"])
                state["phase_results"]["implementation"] = result or {}
            except Exception as e:
                state["error"] = str(e)
        else:
            state["phase_results"]["implementation"] = {"status": "completed"}
        
        return state

    async def _execute_testing(self, state: ProjectState) -> ProjectState:
        """Execute the testing phase."""
        state["current_phase"] = ProjectPhase.TESTING.value
        logger.info(f"Executing testing phase for {state['project_id']}")
        
        if self._engine:
            try:
                result = await self._engine._execute_testing_phase(state["metadata"])
                state["phase_results"]["testing"] = result or {}
            except Exception as e:
                state["error"] = str(e)
        else:
            state["phase_results"]["testing"] = {"status": "completed", "all_passed": True}
        
        return state

    async def _execute_review(self, state: ProjectState) -> ProjectState:
        """Execute the review phase."""
        state["current_phase"] = ProjectPhase.REVIEW.value
        logger.info(f"Executing review phase for {state['project_id']}")
        
        if self._engine:
            try:
                result = await self._engine._execute_review_phase(state["metadata"])
                state["phase_results"]["review"] = result or {}
            except Exception as e:
                state["error"] = str(e)
        else:
            state["phase_results"]["review"] = {"status": "completed", "approved": True}
        
        return state

    async def _execute_deployment(self, state: ProjectState) -> ProjectState:
        """Execute the deployment phase."""
        state["current_phase"] = ProjectPhase.DEPLOYMENT.value
        logger.info(f"Executing deployment phase for {state['project_id']}")
        
        if self._engine:
            try:
                result = await self._engine._execute_deployment_phase(state["metadata"])
                state["phase_results"]["deployment"] = result or {}
            except Exception as e:
                state["error"] = str(e)
        else:
            state["phase_results"]["deployment"] = {"status": "completed"}
        
        return state

    async def run(
        self,
        project_id: str,
        goal: str,
        metadata: Optional[dict[str, Any]] = None,
    ) -> ProjectState:
        """Run the full orchestration pipeline.
        
        Args:
            project_id: Project identifier.
            goal: High-level project goal.
            metadata: Additional project metadata.
            
        Returns:
            Final ProjectState after all phases.
        """
        initial_state: ProjectState = {
            "project_id": project_id,
            "current_phase": "",
            "phase_results": {},
            "error": None,
            "metadata": {
                "goal": goal,
                "project_id": project_id,
                **(metadata or {}),
            },
            "task_count": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
        }
        
        logger.info(f"Starting LangGraph orchestration for project {project_id}")
        
        try:
            final_state = await self._graph.ainvoke(initial_state)
            logger.info(
                f"Orchestration completed for {project_id}",
                extra={"final_phase": final_state.get("current_phase")},
            )
            return final_state
        except Exception as e:
            logger.error(f"Orchestration failed: {e}")
            initial_state["error"] = str(e)
            initial_state["current_phase"] = ProjectPhase.FAILED.value
            return initial_state

    def get_graph_visualization(self) -> Optional[str]:
        """Get Mermaid diagram of the workflow graph.
        
        Returns:
            Mermaid diagram string or None if not available.
        """
        try:
            return self._graph.get_graph().draw_mermaid()
        except Exception:
            return None
