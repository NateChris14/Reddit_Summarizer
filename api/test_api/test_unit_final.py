import pytest
from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, MagicMock
import os

# Mock the database pool for all tests
@pytest.fixture(autouse=True)
def mock_db_pool():
    """Mock database pool for all tests"""
    with patch('app.main.open_pool'), \
         patch('app.main.close_pool'), \
         patch('app.db.open_pool'), \
         patch('app.db.close_pool'), \
         patch('app.db.pool', MagicMock()):
        yield

client = TestClient(app)

@pytest.mark.unit
class TestHealthEndpoints:
    """Test health and root endpoints"""
    
    def test_root_endpoint(self):
        """Test root endpoint returns correct response"""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"service": "reddit-summarizer-api", "status": "ok"}
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "service": "reddit-summarizer-api"}

@pytest.mark.unit
class TestTrendsEndpoint:
    """Test trends endpoint"""
    
    def test_trends_validation(self):
        """Test trends endpoint validation"""
        # Test invalid days (negative)
        response = client.get("/trends?days=-1")
        assert response.status_code == 422
        
        # Test invalid limit (too high)
        response = client.get("/trends?limit=200")
        assert response.status_code == 422
        
        # Test invalid limit (negative)
        response = client.get("/trends?limit=-1")
        assert response.status_code == 422

@pytest.mark.unit
class TestSearchEndpoint:
    """Test search endpoint"""
    
    def test_search_validation(self):
        """Test search endpoint validation"""
        # Test missing query parameter
        response = client.get("/search")
        assert response.status_code == 422
        
        # Test empty query
        response = client.get("/search?query=")
        assert response.status_code == 422
        
        # Test too short query
        response = client.get("/search?query=a")
        assert response.status_code == 422

@pytest.mark.unit
class TestSummariesEndpoint:
    """Test summaries endpoint"""
    
    def test_summaries_validation(self):
        """Test summaries endpoint validation"""
        # Test missing topic
        response = client.get("/summaries")
        assert response.status_code == 422
        
        # Test too short topic
        response = client.get("/summaries?topic=a")
        assert response.status_code == 422

@pytest.mark.unit
class TestBeginnerInsights:
    """Test beginner insights endpoint"""
    
    def test_beginner_insights_validation(self):
        """Test beginner insights endpoint validation"""
        # Test invalid days (negative)
        response = client.get("/beginner/insights?days=-1")
        assert response.status_code == 422
        
        # Test invalid days (too high)
        response = client.get("/beginner/insights?days=400")
        assert response.status_code == 422

@pytest.mark.unit
class TestMonitoringEndpoint:
    """Test monitoring endpoint"""
    
    def test_monitoring_endpoint_skip(self):
        """Skip monitoring endpoint test due to database complexity"""
        pytest.skip("Monitoring endpoint requires complex database mocking - covered in integration tests")

@pytest.mark.unit
class TestSettings:
    """Test settings configuration"""
    
    def test_settings_import(self):
        """Test that settings can be imported"""
        from app.settings import settings
        assert settings is not None
        assert hasattr(settings, 'pg_host')
        assert hasattr(settings, 'pg_port')
        assert hasattr(settings, 'pg_db')
        assert hasattr(settings, 'pg_user')
        assert hasattr(settings, 'pg_password')
    
    def test_settings_defaults(self):
        """Test settings have default values"""
        from app.settings import Settings
        settings = Settings()
        assert settings.pg_host == "localhost"
        assert settings.pg_port == 5432
        assert settings.pg_db == "postgres"
        assert settings.pg_user == "postgres"
        assert settings.pg_password == "postgres"
    
    def test_settings_port_type(self):
        """Test that port is always an integer"""
        from app.settings import Settings
        settings = Settings()
        assert isinstance(settings.pg_port, int)
        assert settings.pg_port > 0

@pytest.mark.unit
class TestDatabaseConnection:
    """Test database connection functionality"""
    
    def test_database_import(self):
        """Test that database module can be imported"""
        from app import db
        assert db is not None
        assert hasattr(db, 'open_pool')
        assert hasattr(db, 'close_pool')
        assert hasattr(db, 'get_conn')
    
    def test_pool_mocking(self):
        """Test that pool mocking works correctly"""
        from app.db import pool
        # Pool should be mocked as MagicMock
        assert pool is not None
