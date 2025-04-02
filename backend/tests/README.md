# Backend Tests

This directory contains tests for the Gift Card Wallet backend API.

## Test Structure

- **Unit Tests:** These test individual components in isolation
- **Integration Tests:** These test the interaction between components
- **Conftest:** Contains test fixtures and configuration

## Running Tests

### Running all tests

```bash
cd backend
pytest
```

### Running a specific test file

```bash
cd backend
pytest tests/unit/test_auth.py
```

### Running a specific test

```bash
cd backend
pytest tests/unit/test_auth.py::test_register_user
```

### Running tests with coverage report

```bash
cd backend
pytest --cov=app tests/
```

## Test Dependencies

Make sure you have installed the test dependencies:

```bash
pip install pytest pytest-cov
```

## Writing New Tests

1. Choose the appropriate directory (unit or integration)
2. Follow the existing naming conventions: `test_*.py` for files and `test_*` for functions
3. Use the fixtures defined in `conftest.py` where appropriate
4. Make tests independent and idempotent so they can run in any order