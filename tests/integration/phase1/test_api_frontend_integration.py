import pytest
import requests
import asyncio
import websockets
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class TestAPIFrontendIntegration:
    """Test suite for API-Frontend integration."""
    
    @pytest.fixture(scope="class")
    def api_base_url(self):
        return "http://localhost:8000"
    
    @pytest.fixture(scope="class")
    def frontend_url(self):
        return "http://localhost:3000"
    
    @pytest.fixture(scope="class")
    def websocket_url(self):
        return "ws://localhost:8000"
    
    def test_api_health_check(self, api_base_url):
        """Test that the API health check endpoint is accessible."""
        response = requests.get(f"{api_base_url}/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "service" in data
        assert "environment" in data
        assert "version" in data
        assert "timestamp" in data
    
    def test_api_root_endpoint(self, api_base_url):
        """Test that the API root endpoint returns correct information."""
        response = requests.get(f"{api_base_url}/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "health" in data
    
    def test_cors_configuration(self, api_base_url):
        """Test CORS configuration allows frontend requests."""
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "Content-Type"
        }
        
        response = requests.options(f"{api_base_url}/api/v1/tasks", headers=headers)
        assert response.status_code in [200, 204]
        
        assert "Access-Control-Allow-Origin" in response.headers
        assert "Access-Control-Allow-Methods" in response.headers
    
    def test_api_tasks_endpoint(self, api_base_url):
        """Test that the analysis API endpoint is accessible."""
        response = requests.get(f"{api_base_url}/api/v1/analysis/tasks")
        assert response.status_code == 200
        
        data = response.json()
        assert "success" in data
        assert "data" in data
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, websocket_url):
        """Test WebSocket connection establishment."""
        test_task_id = "test-task-123"
        uri = f"{websocket_url}/ws/{test_task_id}"
        
        try:
            async with websockets.connect(uri) as websocket:
                test_message = {"type": "ping", "data": "test"}
                await websocket.send(json.dumps(test_message))
                
                assert websocket is not None
                
        except Exception as e:
            pytest.fail(f"WebSocket connection failed: {str(e)}")
    
    def test_frontend_loads(self, frontend_url):
        """Test that the frontend application loads successfully."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            driver.get(frontend_url)
            
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            assert "YouTube Analyzer" in driver.title or "YouTube" in driver.page_source
            
        finally:
            driver.quit()
    
    def test_frontend_api_integration(self, frontend_url, api_base_url):
        """Test that frontend can communicate with backend API."""
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(options=chrome_options)
        
        try:
            driver.get(frontend_url)
            
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            logs = driver.get_log('browser')
            api_errors = [log for log in logs if 'error' in log['message'].lower() and 'api' in log['message'].lower()]
            
            assert len(api_errors) == 0, f"Found API connection errors: {api_errors}"
            
        finally:
            driver.quit()
    
    def test_api_response_time(self, api_base_url):
        """Test that API response time meets performance requirements."""
        import time
        
        start_time = time.time()
        response = requests.get(f"{api_base_url}/health")
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        assert response.status_code == 200
        assert response_time < 200, f"API response time {response_time}ms exceeds 200ms requirement"
    
    def test_api_error_handling(self, api_base_url):
        """Test API error handling and response format."""
        response = requests.get(f"{api_base_url}/api/v1/invalid-endpoint")
        assert response.status_code == 404
        
        response = requests.post(f"{api_base_url}/api/v1/analysis/tasks", json={})
        assert response.status_code in [400, 422]  # Bad request or validation error
        
        if response.status_code == 400:
            data = response.json()
            assert "success" in data
            assert data["success"] is False
            assert "error" in data
