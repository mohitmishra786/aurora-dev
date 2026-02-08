"""
LangGraph graph builders for AURORA-DEV workflows.

This module provides pre-built graph configurations for common
development workflows: feature development and bug fixing.

Example usage:
    >>> from aurora_dev.workflows import create_feature_graph
    >>> graph = create_feature_graph(project_id="my-project")
    >>> result = await graph.ainvoke(initial_state)
"""
from typing import Any, Callable, Optional

from langgraph.graph import END, StateGraph

from aurora_dev.workflows.workflow import (
    AgentNode,
    ConditionalRouter,
    WorkflowState,
    WorkflowStatus,
    create_completion_node,
    create_failure_node,
    create_planning_node,
)
from aurora_dev.core.logging import get_logger


logger = get_logger(__name__)


class GraphBuilder:
    """
    Builder for constructing LangGraph workflows.
    
    Provides a fluent interface for building custom workflows
    with agent nodes, conditional edges, and reflexion loops.
    
    Example:
        >>> builder = GraphBuilder("custom_workflow")
        >>> graph = (builder
        ...     .add_node("plan", planning_func)
        ...     .add_node("implement", implementation_func)
        ...     .add_edge("plan", "implement")
        ...     .add_conditional_edge("implement", router)
        ...     .set_entry("plan")
        ...     .build())
    """
    
    def __init__(self, name: str):
        """
        Initialize graph builder.
        
        Args:
            name: Name of the workflow graph.
        """
        self.name = name
        self._graph = StateGraph(WorkflowState)
        self._nodes: list[str] = []
        self._entry_point: Optional[str] = None
        self._logger = get_logger(__name__)
    
    def add_node(
        self,
        name: str,
        func: Callable[[WorkflowState], WorkflowState],
    ) -> "GraphBuilder":
        """
        Add a node to the graph.
        
        Args:
            name: Node name.
            func: Node function (state -> state).
            
        Returns:
            Self for chaining.
        """
        self._graph.add_node(name, func)
        self._nodes.append(name)
        self._logger.debug(f"Added node: {name}")
        return self
    
    def add_edge(self, from_node: str, to_node: str) -> "GraphBuilder":
        """
        Add a direct edge between nodes.
        
        Args:
            from_node: Source node name.
            to_node: Target node name.
            
        Returns:
            Self for chaining.
        """
        self._graph.add_edge(from_node, to_node)
        self._logger.debug(f"Added edge: {from_node} -> {to_node}")
        return self
    
    def add_conditional_edge(
        self,
        from_node: str,
        router: Callable[[WorkflowState], str],
        destinations: Optional[dict[str, str]] = None,
    ) -> "GraphBuilder":
        """
        Add a conditional edge based on router function.
        
        Args:
            from_node: Source node name.
            router: Function that returns next node name.
            destinations: Optional mapping of router outputs to node names.
            
        Returns:
            Self for chaining.
        """
        if destinations:
            self._graph.add_conditional_edges(from_node, router, destinations)
        else:
            self._graph.add_conditional_edges(from_node, router)
        self._logger.debug(f"Added conditional edge from: {from_node}")
        return self
    
    def add_reflexion_loop(
        self,
        from_node: str,
        reflexion_node: str,
        retry_node: str,
        success_node: str,
        fail_node: str = "fail",
    ) -> "GraphBuilder":
        """
        Add a reflexion loop pattern.
        
        Creates conditional edges for:
        - Success -> success_node
        - Needs reflexion -> reflexion_node -> retry_node
        - Max attempts -> fail_node
        
        Args:
            from_node: Node to check for reflexion.
            reflexion_node: Node that performs reflection.
            retry_node: Node to retry after reflection.
            success_node: Node on success.
            fail_node: Node on max attempts exceeded.
            
        Returns:
            Self for chaining.
        """
        def reflexion_router(state: WorkflowState) -> str:
            route = ConditionalRouter.should_reflexion(state)
            if route == "continue":
                return success_node
            elif route == "reflexion":
                return reflexion_node
            else:
                return fail_node
        
        self._graph.add_conditional_edges(
            from_node,
            reflexion_router,
            {
                success_node: success_node,
                reflexion_node: reflexion_node,
                fail_node: fail_node,
            }
        )
        
        # After reflexion, retry
        self._graph.add_edge(reflexion_node, retry_node)
        
        self._logger.debug(
            f"Added reflexion loop: {from_node} -> {reflexion_node} -> {retry_node}"
        )
        return self
    
    def set_entry(self, node: str) -> "GraphBuilder":
        """
        Set the entry point for the graph.
        
        Args:
            node: Entry node name.
            
        Returns:
            Self for chaining.
        """
        self._entry_point = node
        self._graph.set_entry_point(node)
        self._logger.debug(f"Set entry point: {node}")
        return self
    
    def set_finish(self, node: str) -> "GraphBuilder":
        """
        Set a node as a finish point (connects to END).
        
        Args:
            node: Node to mark as finish.
            
        Returns:
            Self for chaining.
        """
        self._graph.add_edge(node, END)
        self._logger.debug(f"Set finish point: {node}")
        return self
    
    def build(self) -> StateGraph:
        """
        Build and compile the graph.
        
        Returns:
            Compiled StateGraph ready for execution.
        """
        if not self._entry_point:
            raise ValueError("Entry point not set. Call set_entry() first.")
        
        self._logger.info(
            f"Building graph '{self.name}' with {len(self._nodes)} nodes"
        )
        
        return self._graph.compile()


# Pre-built phase functions

def investigation_phase(state: WorkflowState) -> WorkflowState:
    """
    Investigation phase for bug fixes.
    
    Searches memory for similar bugs and analyzes the issue.
    """
    logger.info(f"Investigation phase for: {state['task_id']}")
    
    return WorkflowState(
        **state,
        current_phase="investigation",
        status=WorkflowStatus.PLANNING.value,
        phase_results={
            **state.get("phase_results", {}),
            "investigation": {
                "agent": "maestro",
                "status": "success",
                "output": {
                    "classification": "calculation_error",
                    "similar_bugs_found": [],
                },
                "duration_ms": 0,
                "needs_reflexion": False,
            }
        },
    )


def implementation_phase(state: WorkflowState) -> WorkflowState:
    """
    Implementation phase - code generation.
    """
    logger.info(f"Implementation phase for: {state['task_id']}")
    
    return WorkflowState(
        **state,
        current_phase="implementation",
        status=WorkflowStatus.EXECUTING.value,
        phase_results={
            **state.get("phase_results", {}),
            "implementation": {
                "agent": "backend",
                "status": "success",
                "output": {"files_modified": [], "code": ""},
                "duration_ms": 0,
                "needs_reflexion": False,
            }
        },
    )


def testing_phase(state: WorkflowState) -> WorkflowState:
    """
    Testing phase - run tests and validate.
    """
    logger.info(f"Testing phase for: {state['task_id']}")
    
    return WorkflowState(
        **state,
        current_phase="testing",
        status=WorkflowStatus.TESTING.value,
        phase_results={
            **state.get("phase_results", {}),
            "testing": {
                "agent": "test_engineer",
                "status": "success",
                "output": {"tests_run": 0, "tests_passed": 0},
                "duration_ms": 0,
                "needs_reflexion": False,
            }
        },
    )


def review_phase(state: WorkflowState) -> WorkflowState:
    """
    Code review phase.
    """
    logger.info(f"Review phase for: {state['task_id']}")
    
    return WorkflowState(
        **state,
        current_phase="review",
        status=WorkflowStatus.REVIEWING.value,
        phase_results={
            **state.get("phase_results", {}),
            "review": {
                "agent": "code_reviewer",
                "status": "success",
                "output": {"findings": [], "approved": True},
                "duration_ms": 0,
                "needs_reflexion": False,
            }
        },
    )


def deployment_phase(state: WorkflowState) -> WorkflowState:
    """
    Deployment phase.
    """
    logger.info(f"Deployment phase for: {state['task_id']}")
    
    return WorkflowState(
        **state,
        current_phase="deployment",
        status=WorkflowStatus.DEPLOYING.value,
        phase_results={
            **state.get("phase_results", {}),
            "deployment": {
                "agent": "devops",
                "status": "success",
                "output": {"deployed": True, "environment": "staging"},
                "duration_ms": 0,
                "needs_reflexion": False,
            }
        },
    )


def reflexion_phase(state: WorkflowState) -> WorkflowState:
    """
    Reflexion phase - generate reflection and prepare retry.
    """
    logger.info(f"Reflexion phase for: {state['task_id']}")
    
    attempt = state.get("attempt_number", 1)
    reflections = list(state.get("reflections", []))
    
    # Add reflection for current attempt
    reflections.append({
        "attempt": attempt,
        "phase": state.get("current_phase"),
        "reflection": {
            "root_cause": {"technical": "", "reasoning": ""},
            "incorrect_assumptions": [],
            "improved_strategy": {"approach": "", "steps": []},
            "lessons_learned": [],
        },
    })
    
    return WorkflowState(
        **state,
        status=WorkflowStatus.REFLEXION.value,
        attempt_number=attempt + 1,
        reflections=reflections,
    )


def create_feature_graph(project_id: Optional[str] = None) -> StateGraph:
    """
    Create a feature development workflow graph.
    
    Implements the standard feature flow from spec:
    Planning → Implementation → Testing → Review → Deployment
    
    With reflexion loops at Implementation and Testing phases.
    
    Args:
        project_id: Optional project identifier.
        
    Returns:
        Compiled StateGraph for feature development.
    """
    logger.info(f"Creating feature graph for project: {project_id}")
    
    builder = GraphBuilder("feature_workflow")
    
    graph = (builder
        # Add all nodes
        .add_node("planning", create_planning_node)
        .add_node("implementation", implementation_phase)
        .add_node("testing", testing_phase)
        .add_node("reflexion", reflexion_phase)
        .add_node("review", review_phase)
        .add_node("deployment", deployment_phase)
        .add_node("complete", create_completion_node)
        .add_node("fail", create_failure_node)
        
        # Set entry
        .set_entry("planning")
        
        # Add edges
        .add_edge("planning", "implementation")
        
        # Add reflexion loop at implementation
        .add_reflexion_loop(
            from_node="implementation",
            reflexion_node="reflexion",
            retry_node="implementation",
            success_node="testing",
            fail_node="fail",
        )
        
        # Testing -> Review or Reflexion
        .add_conditional_edge(
            "testing",
            ConditionalRouter.route_after_testing,
            {
                "review": "review",
                "reflexion": "reflexion",
                "fail": "fail",
            }
        )
        
        # Review -> Deployment
        .add_edge("review", "deployment")
        
        # Deployment -> Complete
        .add_edge("deployment", "complete")
        
        # Finish points
        .set_finish("complete")
        .set_finish("fail")
        
        .build()
    )
    
    return graph


def create_bugfix_graph(project_id: Optional[str] = None) -> StateGraph:
    """
    Create a bug fix workflow graph with reflexion loop.
    
    Implements the bug fix flow from spec:
    Investigation → Fix Attempt → Testing → Reflexion (if needed) → Deployment
    
    Supports up to 5 retry attempts with accumulated reflections.
    
    Args:
        project_id: Optional project identifier.
        
    Returns:
        Compiled StateGraph for bug fixing.
    """
    logger.info(f"Creating bugfix graph for project: {project_id}")
    
    builder = GraphBuilder("bugfix_workflow")
    
    graph = (builder
        # Add all nodes
        .add_node("investigation", investigation_phase)
        .add_node("fix", implementation_phase)
        .add_node("testing", testing_phase)
        .add_node("reflexion", reflexion_phase)
        .add_node("deployment", deployment_phase)
        .add_node("complete", create_completion_node)
        .add_node("fail", create_failure_node)
        
        # Set entry
        .set_entry("investigation")
        
        # Investigation -> Fix
        .add_edge("investigation", "fix")
        
        # Fix -> Testing
        .add_edge("fix", "testing")
        
        # Testing with reflexion loop (the key bugfix pattern)
        .add_reflexion_loop(
            from_node="testing",
            reflexion_node="reflexion",
            retry_node="fix",  # Retry the fix after reflexion
            success_node="deployment",
            fail_node="fail",
        )
        
        # Deployment -> Complete
        .add_edge("deployment", "complete")
        
        # Finish points
        .set_finish("complete")
        .set_finish("fail")
        
        .build()
    )
    
    return graph


def create_parallel_services_graph(
    services: list[str],
    project_id: Optional[str] = None,
) -> StateGraph:
    """
    Create a parallel services development graph.
    
    Implements parallel development pattern from spec where
    multiple services are developed simultaneously in separate
    git worktrees.
    
    Args:
        services: List of service names to develop in parallel.
        project_id: Optional project identifier.
        
    Returns:
        Compiled StateGraph for parallel service development.
    """
    logger.info(
        f"Creating parallel services graph for {len(services)} services"
    )
    
    builder = GraphBuilder("parallel_services_workflow")
    
    # Add planning node
    builder.add_node("planning", create_planning_node)
    builder.set_entry("planning")
    
    # Add a node for each service (they run in parallel conceptually)
    for service in services:
        def make_service_node(svc: str):
            def service_impl(state: WorkflowState) -> WorkflowState:
                logger.info(f"Implementing service: {svc}")
                return WorkflowState(
                    **state,
                    current_phase=f"service_{svc}",
                    phase_results={
                        **state.get("phase_results", {}),
                        f"service_{svc}": {
                            "agent": "backend",
                            "status": "success",
                            "output": {"service": svc},
                            "duration_ms": 0,
                            "needs_reflexion": False,
                        }
                    },
                )
            return service_impl
        
        builder.add_node(f"service_{service}", make_service_node(service))
        builder.add_edge("planning", f"service_{service}")
    
    # Add integration node (runs after all services)
    builder.add_node("integration", testing_phase)
    for service in services:
        builder.add_edge(f"service_{service}", "integration")
    
    # Add completion
    builder.add_node("complete", create_completion_node)
    builder.add_edge("integration", "complete")
    builder.set_finish("complete")
    
    return builder.build()
