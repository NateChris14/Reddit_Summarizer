# API Testing Guide

## Test Structure

```
api/
├── test_api/
│   ├── __init__.py
│   ├── test_unit.py          # Unit tests with mocked dependencies
│   ├── test_integration.py    # Integration tests with real database
│   ├── test_database.py      # Database connection and query tests
│   └── test_settings.py      # Configuration tests
├── test-requirements.txt     # Test dependencies
└── pyproject.toml          # Pytest configuration
```

## Running Tests

### Install Test Dependencies
```bash
pip install -r test-requirements.txt
```

### Run All Tests
```bash
pytest
```

### Run Only Unit Tests (Fast, no database required)
```bash
pytest -m unit
```

### Run Only Integration Tests (Requires database)
```bash
pytest -m integration
```

### Run with Coverage
```bash
pytest --cov=app --cov-report=html
```

### Run Specific Test File
```bash
pytest test_api/test_unit.py
```

### Run Specific Test Class
```bash
pytest test_api/test_unit.py::TestHealthEndpoints
```

## Test Categories

### Unit Tests (`test_unit.py`)
- **Purpose**: Test individual functions and endpoints in isolation
- **Dependencies**: Mocked database connections
- **Speed**: Fast
- **Coverage**: All API endpoints with various scenarios

### Integration Tests (`test_integration.py`)
- **Purpose**: Test complete API with real database
- **Dependencies**: Requires PostgreSQL running
- **Speed**: Slower
- **Coverage**: End-to-end API functionality

### Database Tests (`test_database.py`)
- **Purpose**: Test database connection and query logic
- **Dependencies**: Mocked psycopg2
- **Speed**: Fast
- **Coverage**: Connection pooling and query execution

### Settings Tests (`test_settings.py`)
- **Purpose**: Test configuration loading
- **Dependencies**: None
- **Speed**: Fast
- **Coverage**: Environment variable handling

## Environment Setup for Integration Tests

Set these environment variables before running integration tests:
```bash
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=test_reddit
export PGUSER=test_user
export PGPASSWORD=test_password
```

Or create a `.env` file in the `api/` directory:
```
PGHOST=localhost
PGPORT=5432
PGDATABASE=test_reddit
PGUSER=test_user
PGPASSWORD=test_password
```

## Test Database Setup

For integration tests, you'll need a test database:

```sql
-- Create test database
CREATE DATABASE test_reddit;

-- Create test user (optional)
CREATE USER test_user WITH PASSWORD 'test_password';
GRANT ALL PRIVILEGES ON DATABASE test_reddit TO test_user;
```

## Continuous Integration

Add to your CI pipeline:

```yaml
# Example GitHub Actions
- name: Run Unit Tests
  run: pytest -m unit

- name: Run Integration Tests
  run: |
    docker run -d --name postgres-test -e POSTGRES_DB=test_reddit -e POSTGRES_USER=test_user -e POSTGRES_PASSWORD=test_password -p 5432:5432 postgres:13
    sleep 10
    pytest -m integration
    docker stop postgres-test
```

## Writing New Tests

### Unit Test Pattern
```python
@patch('app.main.get_conn')
def test_endpoint_success(self, mock_get_conn):
    # Setup mocks
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_get_conn.return_value = mock_conn
    
    # Mock return data
    mock_cursor.fetchall.return_value = [{"field": "value"}]
    
    # Test endpoint
    response = client.get("/endpoint")
    
    # Assertions
    assert response.status_code == 200
    assert response.json() == {"expected": "response"}
```

### Integration Test Pattern
```python
@pytest.mark.integration
def test_endpoint_integration(self):
    response = client.get("/endpoint")
    
    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data
```
