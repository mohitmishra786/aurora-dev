"""
Specialized agents package for AURORA-DEV.

Exports all specialized agent classes organized by tier:
- Tier 1: Orchestration (Maestro, MemoryCoordinator)
- Tier 2: Planning (Architect, Research, ProductAnalyst)
- Tier 3: Implementation (Backend, Frontend, Database, Integration)
- Tier 4: Quality (TestEngineer, SecurityAuditor, CodeReviewer, Validator)
- Tier 5: DevOps & Operations (DevOps, Documentation, Monitoring)
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
from aurora_dev.agents.specialized.research import ResearchAgent
from aurora_dev.agents.specialized.product_analyst import ProductAnalystAgent
from aurora_dev.agents.specialized.developers import (
    BackendAgent,
    DatabaseAgent,
    FrontendAgent,
)
from aurora_dev.agents.specialized.integration import IntegrationAgent
from aurora_dev.agents.specialized.quality import (
    CodeReviewerAgent,
    SecurityAuditorAgent,
    TestEngineerAgent,
)
from aurora_dev.agents.specialized.validator import ValidatorAgent
from aurora_dev.agents.specialized.devops import DevOpsAgent
from aurora_dev.agents.specialized.documentation import DocumentationAgent
from aurora_dev.agents.specialized.monitoring import MonitoringAgent
from aurora_dev.agents.specialized.impl import (
    EnhancedArchitectAgent,
    EnhancedDeveloperAgent,
    EnhancedProductAnalystAgent,
    DeveloperType,
    SystemDesign,
    ToolError,
    UserStory,
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
    "ProductAnalystAgent",
    # Tier 3: Implementation
    "BackendAgent",
    "FrontendAgent",
    "DatabaseAgent",
    "IntegrationAgent",
    # Tier 4: Quality
    "TestEngineerAgent",
    "SecurityAuditorAgent",
    "CodeReviewerAgent",
    "ValidatorAgent",
    # Tier 5: DevOps & Operations
    "DevOpsAgent",
    "DocumentationAgent",
    "MonitoringAgent",
    # Enhanced Agents (with self-correction)
    "EnhancedArchitectAgent",
    "EnhancedDeveloperAgent",
    "EnhancedProductAnalystAgent",
    "DeveloperType",
    "SystemDesign",
    "ToolError",
    "UserStory",
]

