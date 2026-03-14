"""
Phase Executor for AURORA-DEV.

Maps workflow phases to appropriate agent execution.
"""
import asyncio
import logging
from typing import Any, Callable, Optional

from aurora_dev.agents.specialized.maestro import MaestroAgent
from aurora_dev.agents.specialized.product_analyst import ProductAnalystAgent
from aurora_dev.agents.specialized.architect import ArchitectAgent
from aurora_dev.agents.specialized.research import ResearchAgent
from aurora_dev.agents.specialized.developers import (
    BackendAgent,
    FrontendAgent,
    DatabaseAgent,
)
from aurora_dev.agents.specialized.integration import IntegrationAgent
from aurora_dev.agents.specialized.quality import (
    TestEngineerAgent,
    SecurityAuditorAgent,
    CodeReviewerAgent,
)
from aurora_dev.agents.specialized.validator import ValidatorAgent
from aurora_dev.agents.specialized.devops import DevOpsAgent
from aurora_dev.agents.specialized.documentation import DocumentationAgent
from aurora_dev.agents.specialized.monitoring import MonitoringAgent
from aurora_dev.core.state_machine.states import WorkflowPhase
from aurora_dev.core.logging import get_logger
from aurora_dev.core.reflexion import (
    ReflexionEngine,
    ReflexionTrigger,
    TaskContext,
    AttemptResult,
)
from aurora_dev.core.enterprise.audit_log import AuditLogger, AuditLevel
from aurora_dev.core.enterprise.cost_tracker import CostTracker
from aurora_dev.core.enterprise.compliance import ComplianceManager, ComplianceCheck

logger = get_logger(__name__)


class PhaseExecutor:
    """Executes workflow phases by delegating to appropriate agents."""

    def __init__(
        self,
        project_id: str,
        session_id: Optional[str] = None,
        enable_reflexion: bool = True,
        max_reflexion_attempts: int = 3,
    ) -> None:
        """Initialize phase executor.

        Args:
            project_id: The project ID for agent context.
            session_id: Optional session ID for tracking.
            enable_reflexion: Whether to enable reflexion loops.
            max_reflexion_attempts: Maximum number of reflexion attempts.
        """
        self.project_id = project_id
        self.session_id = session_id or f"session-{asyncio.get_event_loop().time()}"
        self.enable_reflexion = enable_reflexion
        self.max_reflexion_attempts = max_reflexion_attempts

        # Initialize reflexion engine
        self.reflexion_engine = ReflexionEngine(
            project_id=project_id,
            max_attempts=max_reflexion_attempts,
        )

        # Initialize enterprise features
        self.audit_logger = AuditLogger(project_id=project_id)
        self.cost_tracker = CostTracker(project_id=project_id)
        self.compliance_manager = ComplianceManager(project_id=project_id)

        # Initialize agents
        self.maestro = MaestroAgent(
            project_id=project_id,
            session_id=self.session_id,
        )
        self.product_analyst = ProductAnalystAgent(
            project_id=project_id,
            session_id=self.session_id,
        )
        self.architect = ArchitectAgent(
            project_id=project_id,
            session_id=self.session_id,
        )
        self.research = ResearchAgent(
            project_id=project_id,
            session_id=self.session_id,
        )
        self.backend = BackendAgent(
            project_id=project_id,
            session_id=self.session_id,
        )
        self.frontend = FrontendAgent(
            project_id=project_id,
            session_id=self.session_id,
        )
        self.database = DatabaseAgent(
            project_id=project_id,
            session_id=self.session_id,
        )
        self.integration = IntegrationAgent(
            project_id=project_id,
            session_id=self.session_id,
        )
        self.test_engineer = TestEngineerAgent(
            project_id=project_id,
            session_id=self.session_id,
        )
        self.security_auditor = SecurityAuditorAgent(
            project_id=project_id,
            session_id=self.session_id,
        )
        self.code_reviewer = CodeReviewerAgent(
            project_id=project_id,
            session_id=self.session_id,
        )
        self.validator = ValidatorAgent(
            project_id=project_id,
            session_id=self.session_id,
        )
        self.devops = DevOpsAgent(
            project_id=project_id,
            session_id=self.session_id,
        )
        self.documentation = DocumentationAgent(
            project_id=project_id,
            session_id=self.session_id,
        )
        self.monitoring = MonitoringAgent(
            project_id=project_id,
            session_id=self.session_id,
        )

        logger.info(f"PhaseExecutor initialized for project {project_id}")

    async def execute_phase(
        self,
        phase: WorkflowPhase,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a workflow phase.

        Args:
            phase: The workflow phase to execute.
            context: Current workflow context/data.

        Returns:
            Phase execution results.
        """
        logger.info(f"Executing phase: {phase.value}")

        # Log audit event
        self.audit_logger.log(
            event_type="phase_execution",
            resource_id=phase.value,
            action="execute",
            details={"context": context},
        )

        # Execute with reflexion support if enabled
        if self.enable_reflexion:
            return await self._execute_with_reflexion(phase, context)
        else:
            return await self._execute_single_attempt(phase, context)

    async def _execute_with_reflexion(
        self,
        phase: WorkflowPhase,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute phase with reflexion loop support.

        Args:
            phase: The workflow phase to execute.
            context: Current workflow context/data.

        Returns:
            Phase execution results with reflexion if needed.
        """
        max_attempts = self.max_reflexion_attempts
        previous_reflections = []

        for attempt_num in range(1, max_attempts + 1):
            logger.info(f"Attempt {attempt_num}/{max_attempts} for phase {phase.value}")

            try:
                # Execute the phase
                result = await self._execute_single_attempt(phase, context)

                # If successful, return immediately
                if result.get("status") == "completed":
                    return result

                # If this is the last attempt, return the error
                if attempt_num == max_attempts:
                    logger.warning(
                        f"Phase {phase.value} failed after {max_attempts} attempts"
                    )
                    return result

                # Generate reflection on failure
                if result.get("status") == "error":
                    reflection = await self._generate_reflection(
                        phase=phase,
                        context=context,
                        attempt_num=attempt_num,
                        error=result.get("error"),
                        previous_reflections=previous_reflections,
                    )

                    if reflection:
                        previous_reflections.append(reflection)
                        logger.info(
                            f"Generated reflection for phase {phase.value}: "
                            f"{reflection.root_cause.technical}"
                        )

                        # Update context with improved strategy
                        context = self._update_context_with_reflection(
                            context, reflection
                        )

                # Wait before retry
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error in attempt {attempt_num}: {e}")
                if attempt_num == max_attempts:
                    return {
                        "status": "error",
                        "phase": phase.value,
                        "error": str(e),
                    }
                await asyncio.sleep(1)

        return {
            "status": "error",
            "phase": phase.value,
            "error": "Max reflexion attempts exceeded",
        }

    async def _generate_reflection(
        self,
        phase: WorkflowPhase,
        context: dict[str, Any],
        attempt_num: int,
        error: Optional[str],
        previous_reflections: list,
    ) -> Optional[Any]:
        """Generate a reflection for a failed attempt.

        Args:
            phase: The phase that failed.
            context: Current context.
            attempt_num: Attempt number.
            error: Error message.
            previous_reflections: Previous reflections.

        Returns:
            Generated reflection or None if failed.
        """
        try:
            # Determine trigger based on phase and error
            if "test" in phase.value.lower() or "test" in str(error).lower():
                trigger = ReflexionTrigger.TEST_FAILURE
            elif "security" in phase.value.lower():
                trigger = ReflexionTrigger.SECURITY_VULNERABILITY
            elif "validation" in str(error).lower():
                trigger = ReflexionTrigger.VALIDATION_ERROR
            else:
                trigger = ReflexionTrigger.API_ERROR

            # Create task context
            task_context = TaskContext(
                task_id=f"{phase.value}-{attempt_num}",
                description=f"Execute {phase.value} phase",
                requirements=context.get("requirements", []),
                constraints=context.get("constraints", {}),
            )

            # Create attempt result
            attempt_result = AttemptResult(
                success=False,
                output=None,
                error=error,
            )

            # Generate reflection using LLM
            reflection = await self.reflexion_engine.generate_reflection(
                task=task_context,
                attempt=attempt_result,
                agent_id=f"phase-executor-{phase.value}",
                attempt_number=attempt_num,
                trigger=trigger,
                previous_reflections=previous_reflections,
            )

            return reflection

        except Exception as e:
            logger.warning(f"Failed to generate reflection: {e}")
            return None

    def _update_context_with_reflection(
        self,
        context: dict[str, Any],
        reflection: Any,
    ) -> dict[str, Any]:
        """Update context with insights from reflection.

        Args:
            context: Current context.
            reflection: Generated reflection.

        Returns:
            Updated context.
        """
        updated_context = context.copy()

        # Add improved strategy to context
        if hasattr(reflection, "improved_strategy"):
            updated_context[
                "improved_strategy"
            ] = reflection.improved_strategy.to_dict()

        # Add lessons learned
        if hasattr(reflection, "lessons_learned"):
            updated_context["lessons_learned"] = [
                lesson.to_dict() for lesson in reflection.lessons_learned
            ]

        return updated_context

    async def _execute_single_attempt(
        self,
        phase: WorkflowPhase,
        context: dict[str, Any],
    ) -> dict[str, Any]:
        """Execute a single attempt of a phase without reflexion.

        Args:
            phase: The workflow phase to execute.
            context: Current workflow context/data.

        Returns:
            Phase execution results.
        """
        try:
            if phase == WorkflowPhase.REQUIREMENTS:
                return await self._execute_requirements_phase(context)
            elif phase == WorkflowPhase.DESIGN:
                return await self._execute_design_phase(context)
            elif phase == WorkflowPhase.IMPLEMENTATION:
                return await self._execute_implementation_phase(context)
            elif phase == WorkflowPhase.TESTING:
                return await self._execute_testing_phase(context)
            elif phase == WorkflowPhase.CODE_REVIEW:
                return await self._execute_code_review_phase(context)
            elif phase == WorkflowPhase.SECURITY_AUDIT:
                return await self._execute_security_audit_phase(context)
            elif phase == WorkflowPhase.DOCUMENTATION:
                return await self._execute_documentation_phase(context)
            elif phase == WorkflowPhase.DEPLOYMENT:
                return await self._execute_deployment_phase(context)
            elif phase == WorkflowPhase.MONITORING:
                return await self._execute_monitoring_phase(context)
            else:
                logger.warning(f"Unknown phase: {phase.value}")
                return {"status": "skipped", "phase": phase.value}
        except Exception as e:
            logger.error(f"Error executing phase {phase.value}: {e}")
            return {"status": "error", "phase": phase.value, "error": str(e)}

    async def _execute_requirements_phase(
        self, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute requirements phase."""
        # Use ProductAnalyst to analyze requirements
        requirement_text = context.get("requirements", "")
        if not requirement_text:
            requirement_text = context.get("goal", "")

        # Run sync method in thread pool
        result = await asyncio.to_thread(
            self.product_analyst.analyze_requirements,
            raw_requirements=requirement_text,
            context=context,
        )

        return {
            "status": "completed",
            "phase": "requirements",
            "requirements": result.get("functional_requirements", []),
            "user_stories": result.get("user_stories", []),
            "acceptance_criteria": result.get("acceptance_criteria", []),
            "raw_result": result,
        }

    async def _execute_design_phase(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute design phase."""
        # Use Architect to create system design
        requirements = context.get("requirements", [])
        requirements_text = "\n".join([str(r) for r in requirements])

        # Run sync method in thread pool
        result = await asyncio.to_thread(
            self.architect.design_architecture,
            requirements=requirements_text,
            constraints=context.get("constraints", {}),
        )

        return {
            "status": "completed",
            "phase": "design",
            "raw_result": result,
        }

    async def _execute_implementation_phase(
        self, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute implementation phase."""
        # For now, implementation is a placeholder that would delegate to developers
        # In a full implementation, this would coordinate multiple agents
        architecture = context.get("architecture", {})

        logger.info(f"Implementation phase started for architecture: {architecture}")

        return {
            "status": "completed",
            "phase": "implementation",
            "note": "Implementation phase would coordinate multiple developer agents",
            "architecture": architecture,
        }

    async def _execute_testing_phase(self, context: dict[str, Any]) -> dict[str, Any]:
        """Execute testing phase."""
        implementation = context.get("implementation", {})

        logger.info(f"Testing phase started for implementation: {implementation}")

        return {
            "status": "completed",
            "phase": "testing",
            "note": "Testing phase would be implemented with test generation and execution",
            "implementation": implementation,
        }

    async def _execute_code_review_phase(
        self, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute code review phase."""
        implementation = context.get("implementation", {})

        logger.info(f"Code review phase started for implementation: {implementation}")

        return {
            "status": "completed",
            "phase": "code_review",
            "note": "Code review phase would be implemented with code review agents",
            "implementation": implementation,
        }

    async def _execute_security_audit_phase(
        self, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute security audit phase."""
        implementation = context.get("implementation", {})

        logger.info(
            f"Security audit phase started for implementation: {implementation}"
        )

        return {
            "status": "completed",
            "phase": "security_audit",
            "note": "Security audit phase would be implemented with security auditing agents",
            "implementation": implementation,
        }

    async def _execute_documentation_phase(
        self, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute documentation phase."""
        architecture = context.get("architecture", {})
        implementation = context.get("implementation", {})

        logger.info(f"Documentation phase started")

        return {
            "status": "completed",
            "phase": "documentation",
            "note": "Documentation phase would generate API docs and architecture docs",
            "architecture": architecture,
            "implementation": implementation,
        }

    async def _execute_deployment_phase(
        self, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute deployment phase."""
        implementation = context.get("implementation", {})

        logger.info(f"Deployment phase started for implementation: {implementation}")

        return {
            "status": "completed",
            "phase": "deployment",
            "note": "Deployment phase would deploy to target environment",
            "implementation": implementation,
        }

    async def _execute_monitoring_phase(
        self, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute monitoring phase."""
        deployment = context.get("deployment_info", {})

        logger.info(f"Monitoring phase started for deployment: {deployment}")

        return {
            "status": "completed",
            "phase": "monitoring",
            "note": "Monitoring phase would set up monitoring and alerting",
            "deployment": deployment,
        }
