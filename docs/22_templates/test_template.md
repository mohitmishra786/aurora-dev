# Test Template

Standardized testing patterns for robust AURORA-DEV applications.

**Last Updated:** February 8, 2026
**Audience:** Developers, QA Engineers

> **Before Reading This**
>
> You should understand:
> - [Testing Guide](../06_developer_guides/testing_guide.md)
> - [Quality Gates](../04_core_concepts/quality_gates.md)

## The Testing Contract

In AURORA-DEV, tests are not just for finding bugs. They are the primary way we communicate specs to the AI agents. When the `Product Analyst` writes a requirement, the `Test Engineer` translates it into a failing test case *before* the `Backend Agent` writes a single line of code.

This template ensures that all tests—whether written by humans or AI—follow a consistent structure. This consistency allows our automated tooling to parse test results, categorize failures, and feed them into the Reflexion Loop.

## The Test Pyramid Visualization

We don't just talk about the pyramid; we enforce it in the directory structure and execution pipeline.

```mermaid
graph BT
    E2E[E2E Tests\n(Selenium/Playwright)\nSlow, Expensive, Critical]
    INT[Integration Tests\n(API/Database)\nMedium Speed, Connection Check]
    UNIT[Unit Tests\n(Pytest/Jest)\nFast, Isolated, Logic Check]

    UNIT --> INT
    INT --> E2E

    style UNIT fill:#bbf7d0,stroke:#22c55e,color:black
    style INT fill:#fde047,stroke:#eab308,color:black
    style E2E fill:#fca5a5,stroke:#ef4444,color:black
```

## Unit Test Template (Python/Pytest)

For business logic and utility functions. Isolated from the database and network.

```python
import pytest
from aurora_dev.core.calculator import RiskCalculator
from aurora_dev.exceptions import CalculationError

# 1. Group tests by class/module
class TestRiskCalculator:
    
    # 2. Use fixtures for setup
    @pytest.fixture
    def calculator(self):
        return RiskCalculator(default_margin=0.05)

    # 3. Naming: test_[method]_[scenario]_[expected_result]
    def test_calculate_risk_high_volatility_returns_high_score(self, calculator):
        # Arrange
        data = {"volatility": 0.9, "volume": 1000}
        
        # Act
        score = calculator.compute(data)
        
        # Assert
        assert score > 0.8
        assert isinstance(score, float)

    def test_calculate_risk_invalid_input_raises_error(self, calculator):
        # Arrange
        data = {}
        
        # Act & Assert
        with pytest.raises(CalculationError) as exc:
            calculator.compute(data)
        
        assert "Missing required keys" in str(exc.value)
```

## Integration Test Template (API)

For endpoints and database interactions. Here, we actually spin up the Docker containers.

```python
import pytest
from httpx import AsyncClient

# Mark as integration to allow separate execution
@pytest.mark.integration
async def test_create_project_flow(async_client: AsyncClient, db_session):
    # 1. Setup Data
    payload = {
        "name": "Death Star v2",
        "type": "military_infrastructure"
    }

    # 2. Execute Request
    response = await async_client.post("/api/v1/projects", json=payload)

    # 3. Verify Response
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert "id" in data

    # 4. Verify Side Effects (Database)
    # The agent must check that data actually hit the disk
    # NOT just that the API said 200 OK.
    from aurora_dev.models import Project
    project = db_session.query(Project).filter_by(id=data["id"]).first()
    assert project is not None
```

## E2E Test Template (Playwright)

For user flows. These are fragile, so we keep them focused on critical paths (Login, Checkout, Critical Settings).

```typescript
import { test, expect } from '@playwright/test';

test.describe('Project Management Flow', () => {
  
  test('User can create and delete a project', async ({ page }) => {
    // 1. Arrange: Login
    await page.goto('/login');
    await page.fill('[data-testid=email]', 'admin@aurora.dev');
    await page.fill('[data-testid=password]', 'secure123');
    await page.click('button[type=submit]');

    // 2. Act: Create Project
    await page.click('text=New Project');
    await page.fill('input[name=name]', 'E2E Test Project');
    await page.click('button:has-text("Create")');

    // 3. Assert: Project appears
    await expect(page.locator('.project-list')).toContainText('E2E Test Project');

    // 4. Cleanup (Critical for E2E!)
    // We prefer doing this via API if possible to be faster/reliable
    await page.request.delete(`/api/v1/projects/${projectId}`);
  });
});
```

## Test Data Management

"Garbage in, garbage out" applies doubly to tests. We do not use hardcoded strings like "test" or "asdf". We use factories (like `factory_boy` or `Faker`).

Why? Because when an agent reads a test failure that says `Expected 'John Doe', got 'test user'`, it provides no semantic value. If it says `Expected 'Active', got 'Archived'`, the agent understands state transitions.

## Related Reading

- [Testing Guide](../06_developer_guides/testing_guide.md) - The strategy
- [Test Engineer Agent](../03_agent_specifications/10_test_engineer.md) - The entity running these
- [CI/CD Pipelines](../08_deployment/ci_cd_pipelines.md) - Where these run

## What's Next

- [ADR Template](./adr_template.md)
