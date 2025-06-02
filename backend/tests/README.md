# LMA API Testing Suite

This directory contains the comprehensive testing suite for the Lead Management Automation (LMA) FastAPI backend.

## 📁 Test Structure

```
tests/
├── conftest.py                  # Test configuration and fixtures
├── fixtures/
│   └── factories.py            # Factory Boy factories for test data
├── unit/                       # Unit tests
│   ├── test_models.py          # Database model tests
│   ├── test_auth.py            # Authentication utility tests
│   └── test_schemas.py         # Pydantic schema tests
├── integration/                # Integration tests
│   ├── test_auth_endpoints.py  # Authentication API tests
│   ├── test_leads_endpoints.py # Leads API tests
│   └── test_organizations_endpoints.py # Organizations API tests
└── run_tests.py                # Test runner script
```

## 🧪 Test Types

### Unit Tests (`tests/unit/`)
- **Models**: Test database model creation, validation, and relationships
- **Authentication**: Test password hashing, JWT tokens, and validation
- **Schemas**: Test Pydantic schema validation and serialization

### Integration Tests (`tests/integration/`)
- **Authentication Endpoints**: Test registration, login, logout, token refresh
- **Leads Endpoints**: Test CRUD operations, filtering, pagination, search
- **Organizations Endpoints**: Test role-based access control and CRUD operations

## 🚀 Running Tests

### Prerequisites
1. Install test dependencies:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

### Quick Start
```bash
# Run all tests
python tests/run_tests.py

# Run specific test types
python tests/run_tests.py unit
python tests/run_tests.py integration

# Run with verbose output
python tests/run_tests.py all --verbose

# Generate HTML coverage report
python tests/run_tests.py all --html-report
```

### Using pytest directly
```bash
# Run all tests
pytest tests/

# Run unit tests only
pytest tests/unit/ -m unit

# Run integration tests only
pytest tests/integration/ -m integration

# Run with coverage
pytest tests/ --cov=. --cov-report=term-missing

# Run specific test file
pytest tests/unit/test_models.py

# Run specific test class
pytest tests/unit/test_models.py::TestUser

# Run specific test method
pytest tests/unit/test_models.py::TestUser::test_create_user
```

## 📊 Coverage Requirements

The test suite enforces a minimum coverage threshold of **80%**. Coverage reports include:

- **Terminal output**: Shows missing lines during test runs
- **HTML report**: Generated in `htmlcov/` directory when using `--html-report`

## 🔧 Test Configuration

### pytest.ini
Key configuration settings:
- Test discovery patterns
- Coverage settings and thresholds
- Test markers (unit, integration, slow, database)
- Warning filters

### conftest.py
Provides shared fixtures:
- **Database session**: Isolated test database with rollback
- **Test client**: FastAPI TestClient with dependency overrides
- **Authentication fixtures**: Pre-configured users with different roles
- **Test data fixtures**: Organizations, users, leads for testing

## 🏭 Test Data Factories

Using Factory Boy for consistent test data generation:

```python
from tests.fixtures.factories import create_test_user, create_test_lead

# Create test data in your tests
def test_something(db_session):
    user = create_test_user(db_session, email="custom@test.com")
    lead = create_test_lead(db_session, organization=user.organization)
```

## 🔐 Authentication in Tests

Authentication fixtures provide ready-to-use headers:

```python
def test_protected_endpoint(client, auth_headers):
    response = client.get("/api/protected", headers=auth_headers)
    assert response.status_code == 200

def test_admin_endpoint(client, admin_auth_headers):
    response = client.post("/api/admin-only", headers=admin_auth_headers)
    assert response.status_code == 201
```

## 📝 Writing New Tests

### Unit Test Example
```python
@pytest.mark.unit
class TestNewFeature:
    """Test new feature functionality."""
    
    def test_feature_works(self):
        """Test that the feature works as expected."""
        # Test implementation
        assert True
```

### Integration Test Example
```python
@pytest.mark.integration
class TestNewEndpoint:
    """Test new API endpoint."""
    
    def test_endpoint_success(self, client, auth_headers):
        """Test successful endpoint call."""
        response = client.get("/api/new-endpoint", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
```

## 🏷️ Test Markers

Use markers to categorize and run specific test types:

- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests  
- `@pytest.mark.slow` - Slow tests (may be skipped in quick runs)
- `@pytest.mark.database` - Tests requiring database access

## 🎯 Best Practices

### Test Naming
- Test files: `test_*.py`
- Test classes: `TestFeatureName`
- Test methods: `test_specific_behavior`

### Test Structure
1. **Arrange**: Set up test data and conditions
2. **Act**: Execute the code being tested
3. **Assert**: Verify the results

### Assertions
- Use descriptive assertion messages
- Test both success and failure cases
- Verify response structure and content
- Check status codes for API tests

### Test Data
- Use factories for consistent data generation
- Isolate tests with database rollbacks
- Don't rely on external services
- Mock external dependencies when needed

## 🔍 Debugging Tests

### Running with debugging
```bash
# Run with pdb on failure
pytest tests/ --pdb

# Run with verbose output
pytest tests/ -v -s

# Run single test with full output
pytest tests/unit/test_models.py::TestUser::test_create_user -v -s
```

### Common Issues
1. **Import errors**: Ensure PYTHONPATH includes backend directory
2. **Database conflicts**: Tests use SQLite in-memory by default
3. **Authentication failures**: Check token generation in fixtures
4. **Dependency issues**: Run `pip install -r requirements.txt`

## 📈 Continuous Integration

The test suite is designed to run in CI/CD pipelines:

```bash
# Install dependencies and run tests
pip install -r requirements.txt
python tests/run_tests.py all --no-coverage

# Or with coverage for reporting
python tests/run_tests.py all --html-report
```

## 🤝 Contributing

When adding new features:

1. **Write tests first** (TDD approach recommended)
2. **Maintain or improve coverage** (minimum 80%)
3. **Use appropriate test markers** (`@pytest.mark.unit`, etc.)
4. **Follow naming conventions** for consistency
5. **Document complex test scenarios** with clear docstrings
6. **Update this README** if adding new test patterns or requirements

## 📚 Resources

- [pytest Documentation](https://docs.pytest.org/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Factory Boy Documentation](https://factoryboy.readthedocs.io/)
- [SQLAlchemy Testing](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites) 