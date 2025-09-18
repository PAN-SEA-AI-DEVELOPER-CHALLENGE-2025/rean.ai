from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import json
from datetime import datetime
from typing import Optional

from app.core.websocket import manager
from app.services.auth_service import auth_service

router = APIRouter()


@router.websocket("/ws/class/{class_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    class_id: str,
    token: Optional[str] = Query(None)
):
    """WebSocket endpoint for real-time class communication"""
    
    # Authenticate user via token
    if token:
        user_data = await auth_service.verify_token(token)
        if not user_data:
            await websocket.close(code=1008, reason="Invalid token")
            return
        user_id = user_data["id"]
        username = user_data.get("username", user_data.get("email", "Unknown"))
    else:
        await websocket.close(code=1008, reason="Token required")
        return
    
    await manager.connect(websocket, class_id, user_id)
    
    try:
        # Send welcome message
        await manager.send_personal_message(
            json.dumps({
                "type": "connected",
                "message": f"Connected to class {class_id}",
                "user_id": user_id,
                "username": username,
                "timestamp": datetime.utcnow().isoformat()
            }),
            websocket
        )
        
        # Notify others about new user
        await manager.broadcast_to_class(
            json.dumps({
                "type": "user_joined",
                "user_id": user_id,
                "username": username,
                "timestamp": datetime.utcnow().isoformat()
            }),
            class_id,
            exclude_websocket=websocket
        )
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Add metadata to message
            message_data.update({
                "user_id": user_id,
                "username": username,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Handle different message types
            message_type = message_data.get("type", "message")
            
            if message_type == "chat_message":
                # Broadcast chat message to all class participants
                await manager.broadcast_to_class(
                    json.dumps(message_data),
                    class_id
                )
            
            elif message_type == "audio_start":
                # Notify others that user started speaking
                await manager.broadcast_to_class(
                    json.dumps({
                        "type": "audio_start",
                        "user_id": user_id,
                        "username": username,
                        "timestamp": datetime.utcnow().isoformat()
                    }),
                    class_id,
                    exclude_websocket=websocket
                )
            
            elif message_type == "audio_end":
                # Notify others that user stopped speaking
                await manager.broadcast_to_class(
                    json.dumps({
                        "type": "audio_end",
                        "user_id": user_id,
                        "username": username,
                        "timestamp": datetime.utcnow().isoformat()
                    }),
                    class_id,
                    exclude_websocket=websocket
                )
            
            elif message_type == "screen_share_start":
                # Notify others about screen sharing
                await manager.broadcast_to_class(
                    json.dumps({
                        "type": "screen_share_start",
                        "user_id": user_id,
                        "username": username,
                        "timestamp": datetime.utcnow().isoformat()
                    }),
                    class_id,
                    exclude_websocket=websocket
                )
            
            elif message_type == "screen_share_end":
                # Notify others about screen sharing end
                await manager.broadcast_to_class(
                    json.dumps({
                        "type": "screen_share_end",
                        "user_id": user_id,
                        "username": username,
                        "timestamp": datetime.utcnow().isoformat()
                    }),
                    class_id,
                    exclude_websocket=websocket
                )
            
            elif message_type == "raise_hand":
                # Notify teacher about raised hand
                await manager.broadcast_to_class(
                    json.dumps({
                        "type": "raise_hand",
                        "user_id": user_id,
                        "username": username,
                        "timestamp": datetime.utcnow().isoformat()
                    }),
                    class_id
                )
            
            elif message_type == "lower_hand":
                # Notify about lowered hand
                await manager.broadcast_to_class(
                    json.dumps({
                        "type": "lower_hand",
                        "user_id": user_id,
                        "username": username,
                        "timestamp": datetime.utcnow().isoformat()
                    }),
                    class_id
                )
            
            else:
                # Broadcast any other message type
                await manager.broadcast_to_class(
                    json.dumps(message_data),
                    class_id
                )
                
    except WebSocketDisconnect:
        # Remove connection and notify others
        manager.disconnect(websocket, class_id, user_id)
        await manager.broadcast_to_class(
            json.dumps({
                "type": "user_left",
                "user_id": user_id,
                "username": username,
                "timestamp": datetime.utcnow().isoformat()
            }),
            class_id
        )
    except Exception as e:
        # Handle other exceptions
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, class_id, user_id)


@router.get("/class/{class_id}/participants")
async def get_class_participants(class_id: str):
    """Get current participants in a class"""
    participants = manager.get_class_participants(class_id)
    return {"class_id": class_id, "participants": participants}
