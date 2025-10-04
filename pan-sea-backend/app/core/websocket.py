from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, List, Optional
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections for real-time class sessions"""
    
    def __init__(self):
        # Store active connections by class_id -> list of (websocket, user_id) tuples
        self.active_connections: Dict[str, List[tuple]] = {}
        # Store user info for each connection
        self.user_info: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, class_id: str, user_id: Optional[str] = None):
        """Accept a websocket connection and add to class room"""
        await websocket.accept()
        
        if class_id not in self.active_connections:
            self.active_connections[class_id] = []
        
        self.active_connections[class_id].append((websocket, user_id))
        if user_id:
            self.user_info[websocket] = {"user_id": user_id, "class_id": class_id}
        
        logger.info(f"Client {user_id} connected to class {class_id}")
    
    def disconnect(self, websocket: WebSocket, class_id: str, user_id: Optional[str] = None):
        """Remove websocket connection from class room"""
        if class_id in self.active_connections:
            # Remove the connection tuple
            connection_to_remove = None
            for connection in self.active_connections[class_id]:
                if connection[0] == websocket:
                    connection_to_remove = connection
                    break
            
            if connection_to_remove:
                self.active_connections[class_id].remove(connection_to_remove)
                logger.info(f"Client {user_id} disconnected from class {class_id}")
            
            # Remove empty class rooms
            if not self.active_connections[class_id]:
                del self.active_connections[class_id]
        
        # Clean up user info
        if websocket in self.user_info:
            del self.user_info[websocket]
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Send a message to a specific websocket"""
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {str(e)}")
    
    async def broadcast_to_class(self, message: str, class_id: str, exclude_websocket: Optional[WebSocket] = None):
        """Broadcast a message to all connections in a class"""
        if class_id not in self.active_connections:
            return
        
        disconnected = []
        for websocket, user_id in self.active_connections[class_id]:
            if exclude_websocket and websocket == exclude_websocket:
                continue
                
            try:
                await websocket.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to class {class_id}: {str(e)}")
                disconnected.append((websocket, user_id))
        
        # Remove disconnected connections
        for websocket, user_id in disconnected:
            self.disconnect(websocket, class_id, user_id)
    
    def get_class_participants(self, class_id: str) -> List[str]:
        """Get list of user IDs currently in a class"""
        if class_id not in self.active_connections:
            return []
        
        participants = []
        for websocket, user_id in self.active_connections[class_id]:
            if user_id:
                participants.append(user_id)
        
        return participants
    
    async def send_class_update(self, class_id: str, update_type: str, data: dict):
        """Send a structured update to all class participants"""
        message = {
            "type": update_type,
            "class_id": class_id,
            "data": data,
            "timestamp": data.get("timestamp", "")
        }
        await self.broadcast_to_class(json.dumps(message), class_id)
    
    def get_class_connection_count(self, class_id: str) -> int:
        """Get number of active connections for a class"""
        return len(self.active_connections.get(class_id, []))
    
    def get_all_active_classes(self) -> List[str]:
        """Get list of all active class IDs"""
        return list(self.active_connections.keys())


# Global connection manager instance
manager = ConnectionManager()
