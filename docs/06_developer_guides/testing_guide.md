# Testing Guide

Trust, but verify.

**Last Updated:** February 8, 2026
**Audience:** Developers, QA

> **Before Reading This**
>
> You should understand:
> - [Test Engineer](../03_agent_specifications/10_test_engineer.md)
> - [Quality Gates](../04_core_concepts/quality_gates.md)

## The Test Pyramid

1. **Unit Tests (Fast):** Test one function. Mock everything else.
2. **Integration Tests (Medium):** Test the API + DB. Mock external vendors.
3. **E2E Tests (Slow):** Test the Browser. Mock nothing.

## Running Tests

```bash
# Run everything
make test

# Run specific file
pytest tests/core/test_agent.py

# Run with coverage
make coverage
```

## Writing Mocks

We use `unittest.mock` and `pytest-mock`.

```python
def test_payment(mocker):
    mock_stripe = mocker.patch("aurora.core.payment.stripe")
    mock_stripe.Charge.create.return_value = {"status": "succeeded"}
    
    result = process_payment(100)
    assert result == True
```

## Fixtures

Use `conftest.py` to define shared resources like database connections.
```python
@pytest.fixture
def db():
    database = connect_test_db()
    yield database
    database.teardown()
```

## Continuous Integration

Tests run on every Push via GitHub Actions. If tests fail, the PR cannot be merged.

## Related Reading

- [Test Template](../22_templates/test_template.md)
- [Quality Gates](../04_core_concepts/quality_gates.md)
