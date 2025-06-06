import json
import logging
from typing import Dict, List

from fastapi import WebSocket


class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, task_id: str):
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = []
        self.active_connections[task_id].append(websocket)
        logging.info(f"WebSocket connected for task {task_id}")

    def disconnect(self, task_id: str, websocket: WebSocket = None):
        if task_id in self.active_connections:
            if websocket:
                try:
                    self.active_connections[task_id].remove(websocket)
                except ValueError:
                    pass
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
        logging.info(f"WebSocket disconnected for task {task_id}")

    async def send_message(self, task_id: str, message: dict):
        if task_id in self.active_connections:
            disconnected = []
            for connection in self.active_connections[task_id]:
                try:
                    await connection.send_text(json.dumps(message))
                except Exception as e:
                    logging.error(f"Failed to send message: {e}")
                    disconnected.append(connection)

            for connection in disconnected:
                self.active_connections[task_id].remove(connection)


websocket_manager = WebSocketManager()


async def send_progress_update(
    task_id: str, progress: int, message: str, current_step: str = None
):
    await websocket_manager.send_message(
        task_id,
        {
            "type": "progress_update",
            "progress": progress,
            "message": message,
            "current_step": current_step,
        },
    )


async def send_task_completed(task_id: str, result: dict):
    await websocket_manager.send_message(
        task_id, {"type": "task_completed", "result": result}
    )


async def send_task_failed(task_id: str, error: dict):
    await websocket_manager.send_message(
        task_id, {"type": "task_failed", "error": error}
    )
