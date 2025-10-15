# 🧪 Testing Guide for SKU Cleanup Tool

## Overview

This project implements comprehensive unit testing to ensure reliability and maintainability. Our testing strategy focuses on:

- **Unit Tests**: Testing individual functions and classes in isolation
- **Integration Tests**: Testing interactions between components
- **Mocking**: Extensive use of mocks for external dependencies
- **Coverage**: Aim for >80% code coverage
- **CI/CD Ready**: Tests designed to run in automated environments

## Test Structure

```
tests/
├── __init__.py
├── test_resilience.py      # Already exists - resilience patterns
├── test_config.py          # Configuration management
├── test_data_processor.py  # Core business logic
├── test_amazon_api.py      # External API integration
└── test_*.py              # Additional test modules as needed
```

## Running Tests

### Quick Start

```bash
# Run all tests with coverage
python run_tests.py --coverage

# Run only unit tests (faster)
python run_tests.py --unit --fast

# Run integration tests only
python run_tests.py --integration

# Verbose output
python run_tests.py --verbose
```

### Direct pytest usage

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=. --cov-report=html tests/

# Run specific test file
pytest tests/test_data_processor.py -v

# Run specific test class or method
pytest tests/test_data_processor.py::TestDataProcessor::test_process_valid_sku_basic -v
```

## Testing Best Practices

### 1. **Mock External Dependencies**

Always mock external APIs, file systems, and network calls:

```python
from unittest.mock import Mock, patch

def test_external_api_call():
    with patch('module.api_call') as mock_api:
        mock_api.return_value = {'result': 'success'}

        # Test your code
        result = your_function()

        # Verify API was called correctly
        mock_api.assert_called_once_with(expected_params)
```

### 2. **Test Edge Cases**

Cover boundary conditions and error scenarios:

```python
def test_empty_input():
    result = process_data([])
    assert result == []

def test_invalid_input():
    with pytest.raises(ValueError):
        process_data("invalid")
```

### 3. **Use Descriptive Test Names**

```python
def test_process_sku_with_fba_inventory():  # Good
def test_inventory():                       # Too vague
```

### 4. **Arrange-Act-Assert Pattern**

```python
def test_user_creation():
    # Arrange
    user_data = {'name': 'John', 'email': 'john@example.com'}

    # Act
    user = create_user(user_data)

    # Assert
    assert user.name == 'John'
    assert user.email == 'john@example.com'
```

### 5. **Test Error Conditions**

```python
def test_api_failure_handling():
    with patch('module.api_call', side_effect=ConnectionError("Network error")):
        result = your_function()

        # Should handle error gracefully
        assert result['error'] is not None
        assert result['fallback_used'] is True
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)

- Test individual functions and methods
- Mock all external dependencies
- Fast execution
- High coverage

### Integration Tests (`@pytest.mark.integration`)

- Test component interactions
- May use real external services (with caution)
- Slower execution
- Test end-to-end workflows

### API Tests (`@pytest.mark.api`)

- Test external API integrations
- Use recorded responses or sandbox environments
- Mark as slow if they hit real APIs

## Common Testing Patterns

### Testing Amazon API Integration

```python
@patch('amazon_api.AmazonAPI._make_sp_api_request')
def test_fba_inventory_check(mock_request):
    # Arrange
    mock_response = {
        'payload': {
            'InventorySummaries': [
                {'sellerSku': 'TEST-SKU', 'inventoryDetails': {'sellableQuantity': 5}}
            ]
        }
    }
    mock_request.return_value = mock_response

    # Act
    result = api.check_fba_inventory(['TEST-SKU'])

    # Assert
    assert len(result['inventory']) == 1
    assert result['inventory'][0]['sku'] == 'TEST-SKU'
    assert result['inventory'][0]['quantity'] == 5
```

### Testing Data Processing Logic

```python
def test_sku_age_calculation():
    # Arrange
    thirty_days_ago = datetime.now() - timedelta(days=30)
    sku_data = [{
        'sku': 'OLD-SKU',
        'created_date': thirty_days_ago.strftime('%m/%d/%Y'),
        'fulfillment_channel': 'AMAZON'
    }]

    # Act
    result = processor.process_sku_data(sku_data)

    # Assert
    assert result[0]['is_eligible_for_deletion'] is True
    assert result[0]['age_days'] >= 30
```

### Testing Configuration

```python
def test_configuration_defaults():
    # Arrange & Act
    settings = CleanupSettings()

    # Assert
    assert settings.dry_run is True
    assert settings.age_threshold_days == 30
    assert settings.batch_size == 100
```

## Coverage Goals

- **Overall Coverage**: >80%
- **Critical Path Functions**: >90%
- **Error Handling**: >85%
- **Configuration**: >90%

## Continuous Integration

Tests are designed to run in CI/CD environments:

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
python run_tests.py --coverage

# Generate coverage badge (for README)
coverage-badge -o coverage.svg
```

## Debugging Tests

### When Tests Fail

1. **Check the error message** - Read carefully what failed
2. **Run with verbose output** - `pytest -v` for more details
3. **Use print statements** - Temporarily add debug output
4. **Isolate the issue** - Run individual tests to narrow down

### Common Issues

1. **Mock not working**: Ensure correct import path in patch decorator
2. **Assertion errors**: Check expected vs actual values
3. **Import errors**: Verify all dependencies are installed
4. **Async issues**: Use `pytest-asyncio` for async tests

## Adding New Tests

1. Create test file in `tests/` directory
2. Follow naming convention: `test_<module_name>.py`
3. Group tests in classes by functionality
4. Use descriptive method names starting with `test_`
5. Add proper docstrings
6. Mock external dependencies
7. Test both success and failure scenarios

## Maintenance

- **Regular Updates**: Keep tests in sync with code changes
- **Refactoring**: Update tests when refactoring code
- **Performance**: Monitor test execution time
- **Coverage**: Maintain high coverage standards

## Resources

- [pytest Documentation](https://docs.pytest.org/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py Documentation](https://coverage.readthedocs.io/)

---

**Remember**: Tests are your safety net. Write them as if the next developer (or future you) will thank you for catching their bugs! 🛡️
