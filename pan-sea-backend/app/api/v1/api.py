from fastapi import APIRouter
from app.api.v1.endpoints import users, auth, audio_transcribe, websocket, rag, classes, execution, teacher_dashboard, performance, student, summaries

api_v1_router = APIRouter()

# Include all endpoint routers
api_v1_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_v1_router.include_router(users.router, prefix="/users", tags=["users"])
api_v1_router.include_router(classes.router, prefix="/classes", tags=["classes"])
api_v1_router.include_router(audio_transcribe.router, prefix="/audio", tags=["audio"])
api_v1_router.include_router(execution.router, prefix="/execution", tags=["execution"])
api_v1_router.include_router(teacher_dashboard.router, prefix="/teacher", tags=["teacher"])
# api_v1_router.include_router(s3.router, prefix="/s3", tags=["s3"])
api_v1_router.include_router(rag.router, prefix="/rag", tags=["rag"])
api_v1_router.include_router(websocket.router, tags=["websocket"])
api_v1_router.include_router(performance.router, prefix="/performance", tags=["performance"])
api_v1_router.include_router(student.router, prefix="/student", tags=["student"])
api_v1_router.include_router(summaries.router, prefix="/summaries", tags=["summaries"])
