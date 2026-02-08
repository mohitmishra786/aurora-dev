"""
Agent Self-Correction Module for AURORA-DEV.

Implements a Generate → Write → Test → Fix loop for autonomous code validation.
Agents generate code, write to filesystem, run tests in Docker, and iterate
based on results.
"""
import asyncio
import json
import logging
import os
import tempfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from aurora_dev.core.logging import get_logger
from aurora_dev.core.reflexion import (
    AttemptResult,
    Reflection,
    ReflexionEngine,
    ReflexionTrigger,
    TaskContext,
)
from aurora_dev.tools.security_sandbox import SandboxConfig, SecureSandbox


logger = get_logger(__name__)


class CorrectionPhase(Enum):
    """Phases in the self-correction loop."""
    
    GENERATE = "generate"          # Generate initial code
    WRITE = "write"                # Write code to filesystem
    SYNTAX_CHECK = "syntax_check"  # Validate syntax
    TEST = "test"                  # Run tests in sandbox
    ANALYZE = "analyze"            # Analyze results
    FIX = "fix"                    # Generate fixes
    COMPLETE = "complete"          # Success or max attempts
    FAILED = "failed"              # Permanent failure


@dataclass
class ValidationResult:
    """Result from code validation."""
    
    success: bool
    phase: CorrectionPhase
    output: str = ""
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    test_results: Optional[dict] = None
    execution_time_ms: float = 0.0
    
    @property
    def has_errors(self) -> bool:
        """Check if validation had errors."""
        return len(self.errors) > 0
    
    @property
    def quality_score(self) -> float:
        """Calculate quality score (0.0 to 1.0)."""
        if not self.success:
            return 0.0
        
        # Start at 1.0, subtract for issues
        score = 1.0
        score -= len(self.errors) * 0.2
        score -= len(self.warnings) * 0.05
        
        return max(0.0, min(1.0, score))


@dataclass
class CorrectionAttempt:
    """Single attempt in the correction loop."""
    
    attempt_number: int
    code: str
    validation: ValidationResult
    reflection: Optional[Reflection] = None
    phase_history: list[CorrectionPhase] = field(default_factory=list)


class SelfCorrectionLoop:
    """
    Self-correction loop for agent code generation.
    
    Implements: Generate → Write → Syntax Check → Test → Fix
    
    Attributes:
        task_context: Context for the code generation task.
        max_attempts: Maximum correction attempts.
        quality_threshold: Minimum quality score to accept.
        sandbox: Secure sandbox for code execution.
        reflexion_engine: Engine for learning from failures.
        attempts: History of all attempts.
    """
    
    def __init__(
        self,
        task_context: TaskContext,
        max_attempts: int = 5,
        quality_threshold: float = 0.8,
        sandbox_config: Optional[SandboxConfig] = None,
        reflexion_engine: Optional[ReflexionEngine] = None,
    ) -> None:
        """
        Initialize the self-correction loop.
        
        Args:
            task_context: Task context for generation.
            max_attempts: Maximum retry attempts.
            quality_threshold: Minimum acceptable quality.
            sandbox_config: Optional sandbox configuration.
            reflexion_engine: Optional reflexion engine.
        """
        self.task_context = task_context
        self.max_attempts = max_attempts
        self.quality_threshold = quality_threshold
        
        self.sandbox = SecureSandbox(sandbox_config or SandboxConfig())
        self.reflexion_engine = reflexion_engine or ReflexionEngine()
        
        self.attempts: list[CorrectionAttempt] = []
        self._workspace_dir: Optional[str] = None
    
    async def run(
        self,
        generator_func,
        language: str = "python",
        test_command: Optional[str] = None,
    ) -> CorrectionAttempt:
        """
        Run the self-correction loop.
        
        Args:
            generator_func: Function to generate code (takes attempt context).
            language: Programming language.
            test_command: Optional test command to run.
            
        Returns:
            Final successful or failed attempt.
        """
        logger.info(f"Starting self-correction loop for {self.task_context.task_id}")
        
        # Create temporary workspace
        self._workspace_dir = tempfile.mkdtemp(prefix="aurora_correction_")
        
        try:
            for attempt_num in range(1, self.max_attempts + 1):
                logger.info(f"Attempt {attempt_num}/{self.max_attempts}")
                
                # Generate code
                code = await self._generate_code(
                    generator_func,
                    attempt_num,
                    language,
                )
                
                # Write to filesystem
                file_path = await self._write_code(code, language)
                
                # Syntax check
                syntax_result = await self._check_syntax(file_path, language)
                if not syntax_result.success:
                    await self._handle_failure(
                        attempt_num,
                        code,
                        syntax_result,
                        ReflexionTrigger.VALIDATION_ERROR,
                    )
                    continue
                
                # Run tests
                if test_command:
                    test_result = await self._run_tests(
                        file_path,
                        test_command,
                        language,
                    )
                else:
                    # No tests, just check syntax passed
                    test_result = syntax_result
                
                # Analyze results
                if test_result.success and test_result.quality_score >= self.quality_threshold:
                    # Success!
                    attempt = CorrectionAttempt(
                        attempt_number=attempt_num,
                        code=code,
                        validation=test_result,
                        phase_history=[
                            CorrectionPhase.GENERATE,
                            CorrectionPhase.WRITE,
                            CorrectionPhase.SYNTAX_CHECK,
                            CorrectionPhase.TEST,
                            CorrectionPhase.COMPLETE,
                        ],
                    )
                    self.attempts.append(attempt)
                    
                    logger.info(
                        f"Self-correction succeeded in {attempt_num} attempts "
                        f"(quality: {test_result.quality_score:.2f})"
                    )
                    return attempt
                
                # Handle failure and loop
                await self._handle_failure(
                    attempt_num,
                    code,
                    test_result,
                    ReflexionTrigger.TEST_FAILURE,
                )
            
            # Max attempts reached
            logger.warning(
                f"Self-correction failed after {self.max_attempts} attempts"
            )
            
            last_attempt = self.attempts[-1] if self.attempts else None
            if last_attempt:
                last_attempt.validation.phase = CorrectionPhase.FAILED
                return last_attempt
            
            # No attempts recorded (shouldn't happen)
            return CorrectionAttempt(
                attempt_number=self.max_attempts,
                code="",
                validation=ValidationResult(
                    success=False,
                    phase=CorrectionPhase.FAILED,
                    errors=["No attempts recorded"],
                ),
            )
            
        finally:
            # Cleanup workspace
            if self._workspace_dir and os.path.exists(self._workspace_dir):
                import shutil
                shutil.rmtree(self._workspace_dir)
    
    async def _generate_code(
        self,
        generator_func,
        attempt_num: int,
        language: str,
    ) -> str:
        """Generate code using the provided generator function."""
        # Build context with previous attempts
        context = {
            "task": self.task_context,
            "attempt_number": attempt_num,
            "language": language,
        }
        
        if self.attempts:
            # Add retry context with reflections
            reflections = [a.reflection for a in self.attempts if a.reflection]
            retry_ctx = self.reflexion_engine.get_retry_context(
                self.task_context,
                reflections,
            )
            context["retry_context"] = retry_ctx
            context["previous_attempts"] = [
                {
                    "code": a.code,
                    "errors": a.validation.errors,
                    "quality": a.validation.quality_score,
                }
                for a in self.attempts[-3:]  # Last 3 attempts
            ]
        
        # Call generator
        if asyncio.iscoroutinefunction(generator_func):
            code = await generator_func(context)
        else:
            code = generator_func(context)
        
        return code
    
    async def _write_code(self, code: str, language: str) -> str:
        """Write code to filesystem."""
        ext_map = {
            "python": ".py",
            "javascript": ".js",
            "typescript": ".ts",
            "go": ".go",
            "rust": ".rs",
        }
        
        ext = ext_map.get(language.lower(), ".txt")
        file_path = os.path.join(self._workspace_dir, f"generated{ext}")
        
        with open(file_path, "w") as f:
            f.write(code)
        
        logger.debug(f"Wrote code to {file_path}")
        return file_path
    
    async def _check_syntax(
        self,
        file_path: str,
        language: str,
    ) -> ValidationResult:
        """Check code syntax."""
        import time
        start = time.time()
        
        if language == "python":
            # Use Python's ast module
            try:
                import ast
                with open(file_path, "r") as f:
                    code = f.read()
                ast.parse(code)
                
                return ValidationResult(
                    success=True,
                    phase=CorrectionPhase.SYNTAX_CHECK,
                    output="Syntax valid",
                    execution_time_ms=(time.time() - start) * 1000,
                )
            except SyntaxError as e:
                return ValidationResult(
                    success=False,
                    phase=CorrectionPhase.SYNTAX_CHECK,
                    errors=[f"Line {e.lineno}: {e.msg}"],
                    execution_time_ms=(time.time() - start) * 1000,
                )
        
        # For other languages, run in container
        validators = {
            "javascript": ["node", "--check"],
            "typescript": ["tsc", "--noEmit"],
            "go": ["go", "build", "-o", "/dev/null"],
            "rust": ["rustc", "--crate-type", "lib", "-"],
        }
        
        if language.lower() in validators:
            cmd = validators[language.lower()] + [file_path]
            exit_code, stdout, stderr = await self.sandbox.run(
                image=f"{language}:latest",
                command=cmd,
                volumes={self._workspace_dir: "/workspace"},
            )
            
            return ValidationResult(
                success=exit_code == 0,
                phase=CorrectionPhase.SYNTAX_CHECK,
                output=stdout,
                errors=[stderr] if stderr and exit_code != 0 else [],
                execution_time_ms=(time.time() - start) * 1000,
            )
        
        # Unknown language, skip syntax check
        return ValidationResult(
            success=True,
            phase=CorrectionPhase.SYNTAX_CHECK,
            output=f"Syntax check skipped for {language}",
            warnings=[f"No syntax validator for {language}"],
        )
    
    async def _run_tests(
        self,
        file_path: str,
        test_command: str,
        language: str,
    ) -> ValidationResult:
        """Run tests in sandbox."""
        import time
        start = time.time()
        
        # Docker image selection
        images = {
            "python": "python:3.11-slim",
            "javascript": "node:18-slim",
            "typescript": "node:18-slim",
            "go": "golang:1.21",
            "rust": "rust:latest",
        }
        
        image = images.get(language.lower(), "python:3.11-slim")
        
        # Run in sandbox
        exit_code, stdout, stderr = await self.sandbox.run(
            image=image,
            command=["sh", "-c", test_command],
            volumes={self._workspace_dir: "/workspace"},
            env={"WORKSPACE": "/workspace"},
        )
        
        return ValidationResult(
            success=exit_code == 0,
            phase=CorrectionPhase.TEST,
            output=stdout,
            errors=[stderr] if stderr and exit_code != 0 else [],
            test_results={"exit_code": exit_code},
            execution_time_ms=(time.time() - start) * 1000,
        )
    
    async def _handle_failure(
        self,
        attempt_num: int,
        code: str,
        validation: ValidationResult,
        trigger: ReflexionTrigger,
    ) -> None:
        """Handle failed attempt and generate reflection."""
        # Create attempt result for reflexion
        attempt_result = AttemptResult(
            success=False,
            output=code,
            error="; ".join(validation.errors),
            test_results=validation.output,
            code_produced=code,
        )
        
        # Generate reflection
        reflection = self.reflexion_engine.generate_reflection(
            task=self.task_context,
            attempt=attempt_result,
            agent_id="self_correction",
            attempt_number=attempt_num,
            trigger=trigger,
            previous_reflections=[a.reflection for a in self.attempts if a.reflection],
        )
        
        # Store reflection (synchronous)
        self.reflexion_engine.store_reflection(reflection)
        
        # Record attempt
        attempt = CorrectionAttempt(
            attempt_number=attempt_num,
            code=code,
            validation=validation,
            reflection=reflection,
            phase_history=[
                CorrectionPhase.GENERATE,
                CorrectionPhase.WRITE,
                CorrectionPhase.SYNTAX_CHECK if validation.phase != CorrectionPhase.SYNTAX_CHECK
                else CorrectionPhase.FIX,
                validation.phase,
            ],
        )
        self.attempts.append(attempt)
        
        logger.info(
            f"Attempt {attempt_num} failed at {validation.phase.value}: "
            f"{'; '.join(validation.errors[:2])}"
        )


if __name__ == "__main__":
    # Demo self-correction loop
    import asyncio
    
    def simple_generator(context):
        """Simple code generator for demonstration."""
        attempt = context["attempt_number"]
        
        if attempt == 1:
            # First attempt with syntax error
            return "def hello(\n    print('Hello')"
        elif attempt == 2:
            # Fix syntax, but logic error
            return "def hello():\n    return 'Hello' + 5"  # TypeError
        else:
            # Correct version
            return "def hello():\n    return 'Hello, World!'\n\nif __name__ == '__main__':\n    print(hello())"
    
    async def main():
        task_ctx = TaskContext(
            task_id="demo-task",
            description="Generate a hello world function",
            requirements=["Function should return greeting string"],
        )
        
        loop = SelfCorrectionLoop(task_ctx, max_attempts=3)
        
        result = await loop.run(
            simple_generator,
            language="python",
            test_command="cd /workspace && python generated.py",
        )
        
        print(f"\nResult: {'SUCCESS' if result.validation.success else 'FAILED'}")
        print(f"Attempts: {result.attempt_number}")
        print(f"Quality: {result.validation.quality_score:.2f}")
        print(f"\nFinal code:\n{result.code}")
    
    asyncio.run(main())
