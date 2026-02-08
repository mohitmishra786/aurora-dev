"""
Cross-project learning module for AURORA-DEV.

Enables pattern transfer and learning across projects
to improve performance on similar tasks.

Example usage:
    >>> learning = CrossProjectLearning()
    >>> patterns = await learning.find_similar_patterns(
    ...     current_task="Build REST API with FastAPI",
    ...     project_type="python",
    ... )
"""
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from aurora_dev.core.logging import get_logger


logger = get_logger(__name__)


class PatternCategory(Enum):
    """Categories of learned patterns."""
    
    ARCHITECTURE = "architecture"
    CODE_STRUCTURE = "code_structure"
    ERROR_HANDLING = "error_handling"
    TESTING = "testing"
    SECURITY = "security"
    PERFORMANCE = "performance"
    DEPLOYMENT = "deployment"
    WORKFLOW = "workflow"


@dataclass
class ProjectPattern:
    """A learned pattern from a project."""
    
    id: str
    category: PatternCategory
    name: str
    description: str
    
    # Pattern details
    problem_context: str
    solution_approach: str
    implementation_notes: str
    
    # Success metrics
    success_count: int = 0
    failure_count: int = 0
    avg_quality_score: float = 0.0
    
    # Applicability
    languages: list[str] = field(default_factory=list)
    frameworks: list[str] = field(default_factory=list)
    project_types: list[str] = field(default_factory=list)
    
    # Metadata
    source_project_id: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)
    
    def success_rate(self) -> float:
        """Calculate success rate."""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.5
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "category": self.category.value,
            "name": self.name,
            "description": self.description,
            "problem_context": self.problem_context,
            "solution_approach": self.solution_approach,
            "implementation_notes": self.implementation_notes,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "avg_quality_score": self.avg_quality_score,
            "languages": self.languages,
            "frameworks": self.frameworks,
            "project_types": self.project_types,
            "source_project_id": self.source_project_id,
            "success_rate": self.success_rate(),
        }


@dataclass
class ProjectSimilarity:
    """Similarity assessment between projects."""
    
    project_id: str
    similarity_score: float
    matching_factors: list[str]
    relevant_patterns: list[ProjectPattern]


@dataclass
class LearningOutcome:
    """Outcome of applying learned patterns."""
    
    pattern_id: str
    task_id: str
    project_id: str
    success: bool
    quality_score: float
    notes: str
    timestamp: datetime = field(default_factory=datetime.now)


class CrossProjectLearning:
    """
    Enables learning transfer across projects.
    
    Stores successful patterns and applies them
    to similar tasks in new projects.
    """
    
    def __init__(self):
        """Initialize cross-project learning."""
        self._patterns: dict[str, ProjectPattern] = {}
        self._project_profiles: dict[str, dict[str, Any]] = {}
        self._outcomes: list[LearningOutcome] = []
        self._logger = get_logger(__name__)
    
    async def register_pattern(
        self,
        pattern: ProjectPattern,
    ) -> str:
        """
        Register a new pattern from a project.
        
        Args:
            pattern: The pattern to register.
            
        Returns:
            Pattern ID.
        """
        if not pattern.id:
            pattern.id = self._generate_pattern_id(pattern)
        
        self._patterns[pattern.id] = pattern
        
        self._logger.info(
            f"Registered pattern: {pattern.name} ({pattern.category.value})"
        )
        
        return pattern.id
    
    async def find_similar_patterns(
        self,
        current_task: str,
        project_type: Optional[str] = None,
        language: Optional[str] = None,
        framework: Optional[str] = None,
        category: Optional[PatternCategory] = None,
        min_success_rate: float = 0.6,
        limit: int = 5,
    ) -> list[ProjectPattern]:
        """
        Find patterns relevant to the current task.
        
        Args:
            current_task: Description of current task.
            project_type: Type of project.
            language: Programming language.
            framework: Framework used.
            category: Filter by pattern category.
            min_success_rate: Minimum success rate filter.
            limit: Maximum patterns to return.
            
        Returns:
            List of relevant patterns.
        """
        candidates = []
        task_terms = set(current_task.lower().split())
        
        for pattern in self._patterns.values():
            # Check category filter
            if category and pattern.category != category:
                continue
            
            # Check success rate
            if pattern.success_rate() < min_success_rate:
                continue
            
            # Check language match
            if language and pattern.languages and language not in pattern.languages:
                continue
            
            # Check framework match
            if framework and pattern.frameworks and framework not in pattern.frameworks:
                continue
            
            # Compute relevance score
            score = self._compute_relevance(
                pattern, task_terms, project_type, language, framework
            )
            
            if score > 0:
                candidates.append((score, pattern))
        
        # Sort by score and return top matches
        candidates.sort(reverse=True, key=lambda x: x[0])
        
        return [pattern for _, pattern in candidates[:limit]]
    
    async def find_similar_projects(
        self,
        current_project: dict[str, Any],
        min_similarity: float = 0.5,
        limit: int = 3,
    ) -> list[ProjectSimilarity]:
        """
        Find projects similar to the current one.
        
        Args:
            current_project: Current project characteristics.
            min_similarity: Minimum similarity threshold.
            limit: Maximum projects to return.
            
        Returns:
            List of similar projects with their patterns.
        """
        similarities = []
        
        current_language = current_project.get("language", "")
        current_framework = current_project.get("framework", "")
        current_type = current_project.get("type", "")
        
        for project_id, profile in self._project_profiles.items():
            matching_factors = []
            score = 0.0
            
            # Language match
            if profile.get("language") == current_language:
                score += 0.4
                matching_factors.append("language")
            
            # Framework match
            if profile.get("framework") == current_framework and current_framework:
                score += 0.3
                matching_factors.append("framework")
            
            # Project type match
            if profile.get("type") == current_type and current_type:
                score += 0.2
                matching_factors.append("project_type")
            
            # Domain overlap
            current_domains = set(current_project.get("domains", []))
            profile_domains = set(profile.get("domains", []))
            domain_overlap = len(current_domains & profile_domains)
            if domain_overlap:
                score += 0.1 * min(domain_overlap, 3)
                matching_factors.append("domain")
            
            if score >= min_similarity:
                # Find patterns from this project
                patterns = [
                    p for p in self._patterns.values()
                    if p.source_project_id == project_id
                ]
                
                similarities.append(ProjectSimilarity(
                    project_id=project_id,
                    similarity_score=score,
                    matching_factors=matching_factors,
                    relevant_patterns=patterns,
                ))
        
        # Sort by similarity
        similarities.sort(reverse=True, key=lambda x: x.similarity_score)
        
        return similarities[:limit]
    
    async def record_outcome(
        self,
        pattern_id: str,
        task_id: str,
        project_id: str,
        success: bool,
        quality_score: float = 0.0,
        notes: str = "",
    ) -> None:
        """
        Record the outcome of applying a pattern.
        
        Updates the pattern's success metrics.
        """
        outcome = LearningOutcome(
            pattern_id=pattern_id,
            task_id=task_id,
            project_id=project_id,
            success=success,
            quality_score=quality_score,
            notes=notes,
        )
        
        self._outcomes.append(outcome)
        
        # Update pattern metrics
        if pattern_id in self._patterns:
            pattern = self._patterns[pattern_id]
            if success:
                pattern.success_count += 1
            else:
                pattern.failure_count += 1
            
            # Update average quality
            total = pattern.success_count + pattern.failure_count
            pattern.avg_quality_score = (
                (pattern.avg_quality_score * (total - 1) + quality_score) / total
            )
            pattern.last_used = datetime.now()
            
            self._logger.info(
                f"Recorded outcome for pattern {pattern.name}: "
                f"{'success' if success else 'failure'}"
            )
    
    async def register_project_profile(
        self,
        project_id: str,
        profile: dict[str, Any],
    ) -> None:
        """
        Register a project's profile for similarity matching.
        
        Args:
            project_id: Project identifier.
            profile: Project characteristics.
        """
        self._project_profiles[project_id] = {
            **profile,
            "registered_at": datetime.now().isoformat(),
        }
        
        self._logger.debug(f"Registered project profile: {project_id}")
    
    async def get_best_practices(
        self,
        category: PatternCategory,
        language: Optional[str] = None,
        limit: int = 10,
    ) -> list[ProjectPattern]:
        """
        Get best practices for a category.
        
        Returns patterns sorted by success rate and usage.
        """
        patterns = [
            p for p in self._patterns.values()
            if p.category == category
            and p.success_rate() >= 0.7
            and (not language or language in p.languages or not p.languages)
        ]
        
        # Score by success rate and usage
        patterns.sort(
            key=lambda p: (p.success_rate(), p.success_count),
            reverse=True,
        )
        
        return patterns[:limit]
    
    async def extract_patterns_from_project(
        self,
        project_id: str,
        project_data: dict[str, Any],
    ) -> list[ProjectPattern]:
        """
        Extract learnable patterns from a completed project.
        
        Analyzes project outcomes to identify reusable patterns.
        """
        extracted = []
        
        # Extract from architecture decisions
        decisions = project_data.get("architecture_decisions", [])
        for decision in decisions:
            if decision.get("outcome") == "success":
                pattern = ProjectPattern(
                    id="",
                    category=PatternCategory.ARCHITECTURE,
                    name=f"Architecture: {decision.get('title', 'Unknown')}",
                    description=decision.get("description", ""),
                    problem_context=decision.get("context", ""),
                    solution_approach=decision.get("decision", ""),
                    implementation_notes=decision.get("consequences", ""),
                    languages=[project_data.get("language", "")],
                    frameworks=[project_data.get("framework", "")] if project_data.get("framework") else [],
                    source_project_id=project_id,
                    success_count=1,
                )
                await self.register_pattern(pattern)
                extracted.append(pattern)
        
        # Extract from successful test patterns
        test_patterns = project_data.get("test_patterns", [])
        for test_pattern in test_patterns:
            pattern = ProjectPattern(
                id="",
                category=PatternCategory.TESTING,
                name=f"Testing: {test_pattern.get('name', 'Unknown')}",
                description=test_pattern.get("description", ""),
                problem_context="Testing coverage and quality",
                solution_approach=test_pattern.get("approach", ""),
                implementation_notes=test_pattern.get("implementation", ""),
                languages=[project_data.get("language", "")],
                source_project_id=project_id,
                success_count=1,
            )
            await self.register_pattern(pattern)
            extracted.append(pattern)
        
        self._logger.info(
            f"Extracted {len(extracted)} patterns from project {project_id}"
        )
        
        return extracted
    
    def _compute_relevance(
        self,
        pattern: ProjectPattern,
        task_terms: set[str],
        project_type: Optional[str],
        language: Optional[str],
        framework: Optional[str],
    ) -> float:
        """Compute relevance score for a pattern."""
        score = 0.0
        
        # Text overlap with pattern description
        pattern_terms = set(pattern.description.lower().split())
        pattern_terms.update(pattern.problem_context.lower().split())
        
        overlap = task_terms & pattern_terms
        if overlap:
            score += 0.3 * min(len(overlap) / 5, 1.0)
        
        # Direct matches
        if language and language in pattern.languages:
            score += 0.25
        
        if framework and framework in pattern.frameworks:
            score += 0.25
        
        if project_type and project_type in pattern.project_types:
            score += 0.2
        
        # Boost by success rate
        score *= (0.5 + pattern.success_rate() * 0.5)
        
        return score
    
    def _generate_pattern_id(self, pattern: ProjectPattern) -> str:
        """Generate unique pattern ID."""
        content = f"{pattern.name}:{pattern.category.value}:{pattern.problem_context}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]
    
    def get_pattern_count(self) -> int:
        """Get total number of registered patterns."""
        return len(self._patterns)
    
    def get_patterns_by_category(
        self,
        category: PatternCategory,
    ) -> list[ProjectPattern]:
        """Get all patterns in a category."""
        return [
            p for p in self._patterns.values()
            if p.category == category
        ]
