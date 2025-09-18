from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any
from pydantic import BaseModel

from app.schemas.user_schemas import UserCreate, Token, RefreshTokenRequest, LoginRequest
from app.services.auth_service import auth_service

router = APIRouter()
security = HTTPBearer()


@router.post("/register", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate) -> Dict[str, Any]:
    """Register a new user"""
    result = await auth_service.register_user(user_data)
    return result


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest) -> Token:
    """Login user with email and password"""
    result = await auth_service.login_user(login_data.email, login_data.password)
    return Token(
        access_token=result["access_token"],
        refresh_token=result["refresh_token"],
        token_type="bearer"
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(token_data: RefreshTokenRequest) -> Token:
    """Refresh access token"""
    result = await auth_service.refresh_access_token(token_data.refresh_token)
    return Token(
        access_token=result["access_token"],
        refresh_token=result.get("refresh_token", ""),  # Refresh endpoint might not return new refresh token
        token_type="bearer"
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
class LogoutRequest(BaseModel):
    refresh_token: str


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(payload: LogoutRequest) -> Dict[str, Any]:
    """Logout user by revoking refresh token"""
    try:
        success = await auth_service.logout_user(payload.refresh_token)
        if success:
            return {"message": "Successfully logged out"}
        return {"message": "Logout completed"}
    except Exception:
        return {"message": "Logout completed"}


@router.get("/me", response_model=Dict[str, Any])
async def get_current_user_info(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict[str, Any]:
    """Get current user information from Bearer token"""
    try:
        token = credentials.credentials
        user = await auth_service.verify_token(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        # Sanitize sensitive fields
        sanitized = {k: v for k, v in user.items() if k not in {"hashed_password"}}
        return {"user": sanitized}
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
