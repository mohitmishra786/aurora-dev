"""
Specialized agents package for AURORA-DEV.

Exports all specialized agent classes organized by tier:
- Tier 1: Orchestration (Maestro, MemoryCoordinator)
- Tier 2: Planning (Architect, Research)
- Tier 3: Implementation (Backend, Frontend, Database, Integration)
- Tier 4: Quality (TestEngineer, SecurityAuditor, CodeReviewer)
- Tier 5: DevOps (DevOps, Documentation)
"""
from aurora_dev.agents.specialized.maestro import MaestroAgent
from aurora_dev.agents.specialized.memory_coordinator import (
    ArchitectureDecision,
    MemoryCoordinator,
    MemoryItem,
    MemoryType,
    Reflection,
)
from aurora_dev.agents.specialized.architect import ArchitectAgent
from aurora_dev.agents.specialized.developers import (
    BackendAgent,
    DatabaseAgent,
    FrontendAgent,
    IntegrationAgent,
)
from aurora_dev.agents.specialized.quality import (
    CodeReviewerAgent,
    SecurityAuditorAgent,
    TestEngineerAgent,
)
from aurora_dev.agents.specialized.devops import (
    DevOpsAgent,
    DocumentationAgent,
    ResearchAgent,
)


__all__ = [
    # Tier 1: Orchestration
    "MaestroAgent",
    "MemoryCoordinator",
    "MemoryItem",
    "MemoryType",
    "ArchitectureDecision",
    "Reflection",
    # Tier 2: Planning
    "ArchitectAgent",
    "ResearchAgent",
    # Tier 3: Implementation
    "BackendAgent",
    "FrontendAgent",
    "DatabaseAgent",
    "IntegrationAgent",
    # Tier 4: Quality
    "TestEngineerAgent",
    "SecurityAuditorAgent",
    "CodeReviewerAgent",
    # Tier 5: DevOps
    "DevOpsAgent",
    "DocumentationAgent",
]
