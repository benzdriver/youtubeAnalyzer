import pytest
from fastapi.testclient import TestClient
from app.main import app
import json

def test_websocket_connection():
    client = TestClient(app)
    with client.websocket_connect("/ws/test-task-id") as websocket:
        assert websocket is not None

def test_websocket_message_handling():
    client = TestClient(app)
    with client.websocket_connect("/ws/test-task-id") as websocket:
        websocket.send_text("test message")
        
def test_websocket_multiple_connections():
    client = TestClient(app)
    with client.websocket_connect("/ws/task-1") as ws1:
        with client.websocket_connect("/ws/task-2") as ws2:
            assert ws1 is not None
            assert ws2 is not None

@pytest.mark.asyncio
async def test_websocket_manager():
    from app.api.v1.websocket import websocket_manager, send_progress_update
    
    test_task_id = "test-task-123"
    test_message = {
        "type": "progress_update",
        "progress": 50,
        "message": "Test progress",
        "current_step": "testing"
    }
    
    await websocket_manager.send_message(test_task_id, test_message)

@pytest.mark.asyncio
async def test_progress_update_function():
    from app.api.v1.websocket import send_progress_update
    
    await send_progress_update("test-task", 75, "Test message", "test_step")

@pytest.mark.asyncio
async def test_task_completed_function():
    from app.api.v1.websocket import send_task_completed
    
    test_result = {"summary": "Test completed", "data": [1, 2, 3]}
    await send_task_completed("test-task", test_result)

@pytest.mark.asyncio
async def test_task_failed_function():
    from app.api.v1.websocket import send_task_failed
    
    test_error = {"message": "Test error", "code": "TEST_ERROR"}
    await send_task_failed("test-task", test_error)
