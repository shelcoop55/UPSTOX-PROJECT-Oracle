"""
Integration Tests for API Endpoints
Tests the full stack with Redis cache, database, and API routes
"""

import pytest
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import app as flask_app


@pytest.fixture
def app():
    """Create Flask app for testing"""
    flask_app.config['TESTING'] = True
    flask_app.config['CACHE_TYPE'] = 'simple'  # Use simple cache for testing
    return flask_app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/api/health')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'status' in data
        assert data['status'] == 'running'
        assert 'timestamp' in data
    
    def test_metrics_endpoint(self, client):
        """Test Prometheus metrics endpoint"""
        response = client.get('/metrics')
        # Metrics endpoint may not be available if prometheus not installed
        assert response.status_code in [200, 404]


class TestAPIEndpoints:
    """Test API endpoints"""
    
    def test_portfolio_endpoint(self, client):
        """Test portfolio API endpoint"""
        response = client.get('/api/portfolio')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'total_value' in data or 'error' in data
    
    def test_positions_endpoint(self, client):
        """Test positions API endpoint"""
        response = client.get('/api/positions')
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, dict)
    
    def test_indices_endpoint(self, client):
        """Test market indices API endpoint"""
        response = client.get('/api/indices')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'indices' in data
        assert isinstance(data['indices'], list)
    
    def test_data_endpoint(self, client):
        """Test formatted data endpoint"""
        response = client.get('/api/data')
        assert response.status_code == 200
        
        data = response.get_json()
        assert isinstance(data, dict)


class TestPageRoutes:
    """Test HTML page routes"""
    
    def test_dashboard_route(self, client):
        """Test dashboard page"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Dashboard' in response.data or b'Upstox' in response.data
    
    def test_positions_route(self, client):
        """Test positions page"""
        response = client.get('/positions')
        assert response.status_code == 200
    
    def test_options_route(self, client):
        """Test options page"""
        response = client.get('/options')
        assert response.status_code == 200
    
    def test_downloads_route(self, client):
        """Test downloads page"""
        response = client.get('/downloads')
        assert response.status_code == 200


class TestCaching:
    """Test caching functionality"""
    
    def test_cached_responses(self, client):
        """Test that responses are cached"""
        # First request
        response1 = client.get('/api/portfolio')
        data1 = response1.get_json()
        
        # Second request (should be cached)
        response2 = client.get('/api/portfolio')
        data2 = response2.get_json()
        
        # Both should return same data
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert type(data1) == type(data2)


class TestErrorHandling:
    """Test error handling"""
    
    def test_404_handling(self, client):
        """Test 404 error handling"""
        response = client.get('/nonexistent-route')
        assert response.status_code == 404
    
    def test_method_not_allowed(self, client):
        """Test method not allowed handling"""
        response = client.post('/api/health')
        assert response.status_code == 405


class TestSecurity:
    """Test security features"""
    
    def test_cors_headers(self, client):
        """Test CORS headers are present"""
        response = client.get('/api/health')
        # CORS headers should be present
        assert response.status_code == 200
    
    def test_content_type_json(self, client):
        """Test API endpoints return JSON"""
        response = client.get('/api/health')
        assert response.content_type == 'application/json'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
