"""
Maestro Agent - Main Orchestrator for AURORA-DEV.

The Maestro Agent is the primary orchestrator that:
- Decomposes high-level goals into tasks
- Assigns tasks to specialized agents
- Monitors progress and handles failures
- Coordinates multi-agent workflows
- Makes strategic decisions about execution
"""
import json
from datetime import datetime, timezone
from typing import Any, Optional

from aurora_dev.agents.base_agent import (
    AgentResponse,
    AgentRole,
    AgentStatus,
    BaseAgent,
    TokenUsage,
)
from aurora_dev.agents.communication import (
    AgentMessage,
    MessagePriority,
    MessageType,
    get_broker,
)
from aurora_dev.agents.registry import get_registry
from aurora_dev.agents.task import (
    TaskComplexity,
    TaskDefinition,
    TaskDependencyGraph,
    TaskPriority,
    TaskResult,
    TaskStatus,
    TaskType,
)
from aurora_dev.core.logging import get_agent_logger


MAESTRO_SYSTEM_PROMPT = """You are the Maestro Agent, the main orchestrator of the AURORA-DEV multi-agent software development system.

Your responsibilities:
1. **Task Decomposition**: Break down high-level goals into specific, actionable tasks
2. **Task Assignment**: Assign tasks to appropriate specialized agents based on their capabilities
3. **Progress Monitoring**: Track task completion and handle failures
4. **Coordination**: Orchestrate multi-agent workflows and manage dependencies
5. **Decision Making**: Make strategic decisions about execution order and resource allocation

Available Agent Types:
- ARCHITECT: System design, architecture decisions, technical specifications
- BACKEND: Backend implementation, APIs, services
- FRONTEND: UI/UX implementation, frontend code
- DATABASE: Database design, queries, migrations
- TEST_ENGINEER: Testing strategies, test implementation
- SECURITY_AUDITOR: Security reviews, vulnerability assessment
- CODE_REVIEWER: Code quality reviews, best practices
- DEVOPS: Deployment, CI/CD, infrastructure
- DOCUMENTATION: Documentation, guides, API docs
- RESEARCH: Technical research, technology evaluation

When decomposing tasks, output JSON in this format:
{
    "tasks": [
        {
            "name": "Task name",
            "description": "Detailed description",
            "type": "WRITE_CODE|FIX_BUG|DESIGN_ARCHITECTURE|etc",
            "target_agent": "BACKEND|FRONTEND|etc",
            "priority": "LOW|NORMAL|HIGH|CRITICAL",
            "complexity": "TRIVIAL|LOW|MEDIUM|HIGH|VERY_HIGH",
            "dependencies": ["task-id-1", "task-id-2"],
            "requirements": ["requirement 1", "requirement 2"]
        }
    ],
    "execution_order": ["task-1", "task-2"],
    "notes": "Any additional coordination notes"
}

Always prioritize:
- Clear task boundaries
- Proper dependency ordering
- Balanced workload distribution
- Quality over speed
"""


class MaestroAgent(BaseAgent):
    """
    Main orchestrator agent that coordinates all other agents.
    
    Responsibilities:
    - Task decomposition and planning
    - Agent coordination and assignment
    - Progress monitoring and failure handling
    - Strategic decision making
    """
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        session_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> None:
        """
        Initialize the Maestro Agent.
        
        Args:
            project_id: The project this agent is working on.
            session_id: Session identifier for tracking.
            name: Optional custom name.
        """
        super().__init__(
            name=name or "Maestro",
            project_id=project_id,
            session_id=session_id,
            enable_cache=True,
        )
        
        # Task management
        self._task_graph = TaskDependencyGraph()
        self._completed_tasks: set[str] = set()
        self._failed_tasks: dict[str, str] = {}  # task_id -> error
        
        # Agent management
        self._assigned_agents: dict[str, str] = {}  # task_id -> agent_id
        self._agent_metrics: dict[str, dict[str, int]] = {}  # agent_id -> metrics
        
        # Register with broker
        broker = get_broker()
        self._queue = broker.register_agent(self._agent_id, self.role)
        
        self._logger.info(
            "Maestro Agent initialized",
            extra={"project_id": project_id},
        )
    
    @property
    def role(self) -> AgentRole:
        """Return the agent's role."""
        return AgentRole.MAESTRO
    
    @property
    def system_prompt(self) -> str:
        """Return the agent's system prompt."""
        return MAESTRO_SYSTEM_PROMPT
    
    def decompose_goal(self, goal: str, context: Optional[dict] = None) -> list[TaskDefinition]:
        """
        Decompose a high-level goal into actionable tasks.
        
        Args:
            goal: The high-level goal to decompose.
            context: Optional context information.
            
        Returns:
            List of task definitions.
        """
        self._set_status(AgentStatus.WORKING)
        
        prompt = f"""Decompose the following goal into specific, actionable tasks:

GOAL: {goal}

CONTEXT:
{json.dumps(context or {}, indent=2)}

Analyze the goal and create a comprehensive task breakdown.
Consider dependencies between tasks and proper execution order.
Output valid JSON with the task list.
"""
        
        response = self._call_api(
            messages=[{"role": "user", "content": prompt}],
            max_tokens=4096,
            temperature=0.3,  # Lower temperature for structured output
        )
        
        if not response.success:
            self._logger.error(f"Failed to decompose goal: {response.error}")
            self._set_status(AgentStatus.IDLE)
            return []
        
        tasks = self._parse_task_response(response.content, context)
        
        # Add tasks to dependency graph
        for task in tasks:
            try:
                self._task_graph.add_task(task)
            except ValueError as e:
                self._logger.warning(f"Failed to add task: {e}")
        
        self._set_status(AgentStatus.IDLE)
        return tasks
    
    def _parse_task_response(
        self, content: str, context: Optional[dict] = None
    ) -> list[TaskDefinition]:
        """Parse the LLM response into task definitions."""
        tasks = []
        
        try:
            # Extract JSON from response
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
                data = json.loads(json_str)
                
                task_list = data.get("tasks", [])
                for i, task_data in enumerate(task_list):
                    task = TaskDefinition(
                        id=f"task-{i+1}",
                        name=task_data.get("name", f"Task {i+1}"),
                        description=task_data.get("description", ""),
                        type=self._parse_task_type(task_data.get("type", "WRITE_CODE")),
                        target_agent_role=task_data.get("target_agent"),
                        priority=self._parse_priority(task_data.get("priority", "NORMAL")),
                        complexity=self._parse_complexity(task_data.get("complexity", "MEDIUM")),
                        dependencies=task_data.get("dependencies", []),
                        requirements=task_data.get("requirements", []),
                        project_id=context.get("project_id") if context else None,
                        context=context or {},
                    )
                    tasks.append(task)
                    
        except json.JSONDecodeError as e:
            self._logger.warning(f"Failed to parse task JSON: {e}")
        except Exception as e:
            self._logger.error(f"Error parsing tasks: {e}")
        
        return tasks
    
    def _parse_task_type(self, type_str: str) -> TaskType:
        """Parse task type string to enum."""
        type_map = {
            "WRITE_CODE": TaskType.WRITE_CODE,
            "IMPLEMENT_FEATURE": TaskType.IMPLEMENT_FEATURE,
            "FIX_BUG": TaskType.FIX_BUG,
            "REFACTOR": TaskType.REFACTOR,
            "DESIGN_ARCHITECTURE": TaskType.DESIGN_ARCHITECTURE,
            "ANALYZE_REQUIREMENTS": TaskType.ANALYZE_REQUIREMENTS,
            "CREATE_PLAN": TaskType.CREATE_PLAN,
            "RESEARCH": TaskType.RESEARCH,
            "WRITE_TESTS": TaskType.WRITE_TESTS,
            "RUN_TESTS": TaskType.RUN_TESTS,
            "CODE_REVIEW": TaskType.CODE_REVIEW,
            "SECURITY_AUDIT": TaskType.SECURITY_AUDIT,
            "DEPLOY": TaskType.DEPLOY,
            "DOCUMENT": TaskType.DOCUMENT,
        }
        return type_map.get(type_str.upper(), TaskType.WRITE_CODE)
    
    def _parse_priority(self, priority_str: str) -> TaskPriority:
        """Parse priority string to enum."""
        priority_map = {
            "LOW": TaskPriority.LOW,
            "NORMAL": TaskPriority.NORMAL,
            "HIGH": TaskPriority.HIGH,
            "CRITICAL": TaskPriority.CRITICAL,
        }
        return priority_map.get(priority_str.upper(), TaskPriority.NORMAL)
    
    def _parse_complexity(self, complexity_str: str) -> TaskComplexity:
        """Parse complexity string to enum."""
        complexity_map = {
            "TRIVIAL": TaskComplexity.TRIVIAL,
            "LOW": TaskComplexity.LOW,
            "MEDIUM": TaskComplexity.MEDIUM,
            "HIGH": TaskComplexity.HIGH,
            "VERY_HIGH": TaskComplexity.VERY_HIGH,
        }
        return complexity_map.get(complexity_str.upper(), TaskComplexity.MEDIUM)
    
    def assign_task(self, task: TaskDefinition) -> Optional[str]:
        """
        Assign a task to the best available agent using weighted scoring.
        
        Scoring weights:
        - Specialization match: 35%
        - Workload balance: 25%
        - Success rate: 20%
        - Recency fairness: 10%
        - Round-robin rotation: 10%
        
        Args:
            task: The task to assign.
            
        Returns:
            The assigned agent's ID, or None if no agent available.
        """
        registry = get_registry()
        
        # Find target role
        target_role = self._get_target_role(task)
        
        # Find available agents with the target role
        available = registry.get_available(target_role)
        
        if not available:
            self._logger.warning(
                f"No available agents for role {target_role.value}",
                extra={"task_id": task.id},
            )
            return None
        
        # Score each agent
        best_agent = None
        best_score = -1.0
        
        for agent in available:
            score = self._score_agent(agent, task, target_role)
            if score > best_score:
                best_score = score
                best_agent = agent
        
        if best_agent is None:
            best_agent = available[0]
        
        # Update metrics
        agent_id = best_agent.agent_id
        if agent_id not in self._agent_metrics:
            self._agent_metrics[agent_id] = {
                "tasks_assigned": 0,
                "tasks_completed": 0,
                "tasks_failed": 0,
                "cycle_assigned": 0,
            }
        self._agent_metrics[agent_id]["tasks_assigned"] += 1
        self._agent_metrics[agent_id]["cycle_assigned"] = (
            self._agent_metrics[agent_id].get("cycle_assigned", 0) + 1
        )
        
        # Advance round-robin index (B4)
        if not hasattr(self, "_round_robin_index"):
            self._round_robin_index = 0
        self._round_robin_index += 1
        
        # Send task assignment message
        broker = get_broker()
        message = AgentMessage(
            type=MessageType.TASK_ASSIGN,
            sender_id=self._agent_id,
            sender_role=self.role,
            recipient_id=best_agent.agent_id,
            content={
                "task": task.to_agent_dict(),
            },
            priority=self._map_priority(task.priority),
        )
        
        delivered = broker.send(message)
        
        if delivered > 0:
            self._assigned_agents[task.id] = best_agent.agent_id
            task.assigned_agent_id = best_agent.agent_id
            task.status = TaskStatus.ASSIGNED
            
            self._logger.info(
                f"Task assigned to {best_agent.name} (score={best_score:.2f})",
                extra={
                    "task_id": task.id,
                    "agent_id": best_agent.agent_id,
                    "role": best_agent.role.value,
                    "score": best_score,
                },
            )
            return best_agent.agent_id
        
        return None
    
    def _score_agent(self, agent: Any, task: TaskDefinition, target_role: AgentRole) -> float:
        """Calculate weighted score for an agent-task pair.
        
        Uses round-robin rotation to ensure fair distribution
        across agents of the same role.
        
        Args:
            agent: Candidate agent.
            task: Task to assign.
            target_role: Target role for the task.
            
        Returns:
            Composite score between 0 and 1.
        """
        # Weight constants (B4: added rotation weight)
        W_SPECIALIZATION = 0.35
        W_WORKLOAD = 0.25
        W_SUCCESS = 0.20
        W_RECENCY = 0.10
        W_ROTATION = 0.10
        
        # 1. Specialization match (0 or 1)
        specialization_score = 1.0 if agent.role == target_role else 0.3
        
        # 2. Workload balance (inverse of current task count)
        metrics = self._agent_metrics.get(agent.agent_id, {})
        active_tasks = metrics.get("tasks_assigned", 0) - metrics.get("tasks_completed", 0) - metrics.get("tasks_failed", 0)
        active_tasks = max(0, active_tasks)
        
        # Per-cycle cap enforcement (B4)
        max_per_cycle = getattr(self, "_max_tasks_per_cycle", 5)
        cycle_assigned = metrics.get("cycle_assigned", 0)
        if cycle_assigned >= max_per_cycle:
            return 0.0
        
        workload_score = 1.0 / (1.0 + active_tasks)
        
        # 3. Success rate
        total_completed = metrics.get("tasks_completed", 0) + metrics.get("tasks_failed", 0)
        if total_completed > 0:
            success_score = metrics.get("tasks_completed", 0) / total_completed
        else:
            success_score = 0.5
        
        # 4. Recency fairness
        total_assigned = metrics.get("tasks_assigned", 0)
        max_assigned = max(
            (m.get("tasks_assigned", 0) for m in self._agent_metrics.values()),
            default=1,
        )
        recency_score = 1.0 - (total_assigned / max(max_assigned, 1))
        
        # 5. Round-robin rotation bonus (B4)
        rr_index = getattr(self, "_round_robin_index", 0)
        registry = get_registry()
        agents_for_role = registry.get_available(target_role)
        if agents_for_role:
            expected_idx = rr_index % len(agents_for_role)
            try:
                agent_idx = [a.agent_id for a in agents_for_role].index(agent.agent_id)
                rotation_score = 1.0 if agent_idx == expected_idx else 0.3
            except ValueError:
                rotation_score = 0.5
        else:
            rotation_score = 0.5
        
        # Composite score
        score = (
            W_SPECIALIZATION * specialization_score
            + W_WORKLOAD * workload_score
            + W_SUCCESS * success_score
            + W_RECENCY * recency_score
            + W_ROTATION * rotation_score
        )
        
        return score
    
    def _get_target_role(self, task: TaskDefinition) -> AgentRole:
        """Determine the target agent role for a task."""
        if task.target_agent_role:
            role_map = {
                "ARCHITECT": AgentRole.ARCHITECT,
                "BACKEND": AgentRole.BACKEND,
                "FRONTEND": AgentRole.FRONTEND,
                "DATABASE": AgentRole.DATABASE,
                "TEST_ENGINEER": AgentRole.TEST_ENGINEER,
                "SECURITY_AUDITOR": AgentRole.SECURITY_AUDITOR,
                "CODE_REVIEWER": AgentRole.CODE_REVIEWER,
                "DEVOPS": AgentRole.DEVOPS,
                "DOCUMENTATION": AgentRole.DOCUMENTATION,
                "RESEARCH": AgentRole.RESEARCH,
            }
            return role_map.get(task.target_agent_role.upper(), AgentRole.BACKEND)
        
        # Infer from task type
        type_role_map = {
            TaskType.DESIGN_ARCHITECTURE: AgentRole.ARCHITECT,
            TaskType.ANALYZE_REQUIREMENTS: AgentRole.PRODUCT_ANALYST,
            TaskType.RESEARCH: AgentRole.RESEARCH,
            TaskType.WRITE_CODE: AgentRole.BACKEND,
            TaskType.IMPLEMENT_FEATURE: AgentRole.BACKEND,
            TaskType.FIX_BUG: AgentRole.BACKEND,
            TaskType.WRITE_TESTS: AgentRole.TEST_ENGINEER,
            TaskType.RUN_TESTS: AgentRole.TEST_ENGINEER,
            TaskType.CODE_REVIEW: AgentRole.CODE_REVIEWER,
            TaskType.SECURITY_AUDIT: AgentRole.SECURITY_AUDITOR,
            TaskType.DEPLOY: AgentRole.DEVOPS,
            TaskType.DOCUMENT: AgentRole.DOCUMENTATION,
        }
        return type_role_map.get(task.type, AgentRole.BACKEND)
    
    def _map_priority(self, priority: TaskPriority) -> MessagePriority:
        """Map task priority to message priority."""
        priority_map = {
            TaskPriority.LOW: MessagePriority.LOW,
            TaskPriority.NORMAL: MessagePriority.NORMAL,
            TaskPriority.HIGH: MessagePriority.HIGH,
            TaskPriority.CRITICAL: MessagePriority.CRITICAL,
        }
        return priority_map.get(priority, MessagePriority.NORMAL)
    
    def get_next_tasks(self) -> list[TaskDefinition]:
        """
        Get the next tasks ready for execution.
        
        Returns:
            List of tasks with satisfied dependencies.
        """
        return self._task_graph.get_ready_tasks(self._completed_tasks)
    
    def mark_task_complete(self, task_id: str, result: TaskResult) -> None:
        """
        Mark a task as completed.
        
        Args:
            task_id: The completed task ID.
            result: The task result.
        """
        task = self._task_graph.get_task(task_id)
        if task:
            task.mark_completed(result)
            self._completed_tasks.add(task_id)
            
            if not result.success:
                self._failed_tasks[task_id] = result.error or "Unknown error"
            
            # Update metrics for scoring
            agent_id = self._assigned_agents.get(task_id)
            if agent_id and agent_id in self._agent_metrics:
                if result.success:
                    self._agent_metrics[agent_id]["tasks_completed"] += 1
                else:
                    self._agent_metrics[agent_id]["tasks_failed"] += 1
            
            self._logger.info(
                f"Task completed",
                extra={
                    "task_id": task_id,
                    "success": result.success,
                },
            )
    
    async def _coordinate_merge(
        self,
        source_branch: str,
        target_branch: str = "main",
        repo_path: str = ".",
    ) -> dict[str, Any]:
        """
        Coordinate merging an agent's work branch back to main.
        
        Uses MergeConflictResolver to handle conflicts automatically
        when multiple agents work on overlapping files.
        
        Args:
            source_branch: Branch to merge from.
            target_branch: Branch to merge into.
            repo_path: Path to the Git repository.
            
        Returns:
            Merge result with conflict resolution status.
        """
        try:
            from aurora_dev.tools.merge_resolver import MergeConflictResolver
            
            resolver = MergeConflictResolver(repo_path=repo_path)
            result = await resolver.merge_worktree(
                source_branch=source_branch,
                target_branch=target_branch,
            )
            
            if result.conflicts:
                resolved = 0
                for conflict_file in result.conflicts:
                    success = await resolver.auto_resolve(conflict_file)
                    if success:
                        resolved += 1
                
                self._logger.info(
                    f"Merge coordination: {resolved}/{len(result.conflicts)} "
                    f"conflicts auto-resolved",
                )
            
            return {
                "success": result.success,
                "conflicts_found": len(result.conflicts),
                "source": source_branch,
                "target": target_branch,
            }
            
        except Exception as e:
            self._logger.error(f"Merge coordination failed: {e}")
            return {"success": False, "error": str(e)}
    
    def get_project_status(self) -> dict[str, Any]:
        """
        Get the current project status.
        
        Returns:
            Dictionary with project status information.
        """
        all_tasks = self._task_graph.get_all_tasks()
        
        status_counts = {}
        for task in all_tasks:
            status = task.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_tasks": len(all_tasks),
            "completed": len(self._completed_tasks),
            "failed": len(self._failed_tasks),
            "pending": status_counts.get("pending", 0),
            "running": status_counts.get("running", 0),
            "status_breakdown": status_counts,
            "assigned_agents": len(self._assigned_agents),
            "token_usage": self._total_usage.to_dict(),
        }
    
    def execute(self, task: dict[str, Any]) -> AgentResponse:
        """
        Execute the Maestro's main task.
        
        For the Maestro, this typically means orchestrating a project.
        
        Args:
            task: Task definition containing the goal.
            
        Returns:
            AgentResponse with execution results.
        """
        self._set_status(AgentStatus.WORKING)
        
        goal = task.get("goal", "")
        context = task.get("context", {})
        
        # Decompose the goal
        tasks = self.decompose_goal(goal, context)
        
        if not tasks:
            return AgentResponse(
                content="Failed to decompose goal into tasks",
                token_usage=self._total_usage,
                model=self._model,
                stop_reason="error",
                execution_time_ms=0,
                error="Task decomposition failed",
            )
        
        # Get execution plan
        sorted_tasks = self._task_graph.topological_sort()
        
        result = {
            "tasks_created": len(tasks),
            "execution_order": [t.id for t in sorted_tasks],
            "status": self.get_project_status(),
        }
        
        self._set_status(AgentStatus.IDLE)
        
        return AgentResponse(
            content=json.dumps(result, indent=2),
            token_usage=self._total_usage,
            model=self._model,
            stop_reason="end_turn",
            execution_time_ms=0,
        )
    
    def process_messages(self) -> int:
        """
        Process pending messages from the queue.
        
        Returns:
            Number of messages processed.
        """
        processed = 0
        
        while True:
            message = self._queue.pop()
            if not message:
                break
            
            self._handle_message(message)
            processed += 1
        
        return processed
    
    def _handle_message(self, message: AgentMessage) -> None:
        """Handle an incoming message."""
        if message.type == MessageType.TASK_COMPLETE:
            task_id = message.content.get("task_id")
            result_data = message.content.get("result", {})
            result = TaskResult(
                success=result_data.get("success", False),
                output=result_data.get("output"),
                artifacts=result_data.get("artifacts", []),
                error=result_data.get("error"),
            )
            self.mark_task_complete(task_id, result)
            
        elif message.type == MessageType.TASK_FAILED:
            task_id = message.content.get("task_id")
            error = message.content.get("error", "Unknown error")
            result = TaskResult(success=False, error=error)
            self.mark_task_complete(task_id, result)
            
        elif message.type == MessageType.TASK_PROGRESS:
            task_id = message.content.get("task_id")
            progress = message.content.get("progress", 0)
            self._logger.info(
                f"Task progress update",
                extra={"task_id": task_id, "progress": progress},
            )
