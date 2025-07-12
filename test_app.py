import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_home_endpoint(client):
    """Test the home endpoint returns correct JSON response"""
    response = client.get('/')
    assert response.status_code == 200
    data = response.get_json()
    assert data['message'] == 'Alexandria API is running'
    assert data['status'] == 'success'

def test_health_check_endpoint(client):
    """Test the health check endpoint returns correct JSON response"""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'
    assert data['service'] == 'alexandria-backend'

def test_health_check_content_type(client):
    """Test that health check endpoint returns JSON content type"""
    response = client.get('/api/health')
    assert response.content_type == 'application/json'

def test_home_content_type(client):
    """Test that home endpoint returns JSON content type"""
    response = client.get('/')
    assert response.content_type == 'application/json'

def test_404_error(client):
    """Test that non-existent endpoints return 404"""
    response = client.get('/nonexistent')
    assert response.status_code == 404 