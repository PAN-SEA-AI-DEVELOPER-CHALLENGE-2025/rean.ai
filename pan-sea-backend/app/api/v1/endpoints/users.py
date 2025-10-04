from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.schemas.user_schemas import UserUpdate
from app.services.auth_service import auth_service
from app.services.class_service import class_service

router = APIRouter()
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Get current user from JWT token"""
    token = credentials.credentials
    user_data = await auth_service.verify_token(token)
    if not user_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    return user_data


@router.get("/me", response_model=dict)
async def get_current_user_profile(
    current_user: dict = Depends(get_current_user)
):
    """Get current user profile"""
    return current_user


@router.get("/me/profile", response_model=dict)
async def get_my_profile(
    limit: int = Query(50, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """Get profile info plus classes (teacher: teaches, student: enrolled)."""
    user_id = current_user.get("id")
    role = current_user.get("role")

    classes = []
    try:
        if role == "teacher":
            classes = await class_service.get_classes_by_teacher(user_id, limit)
        elif role == "student":
            classes = await class_service.get_classes_for_student(user_id, limit, 0)
        else:
            classes = []
    except Exception:
        classes = []

    return {
        "user": {
            "id": user_id,
            "full_name": current_user.get("full_name", ""),
            "email": current_user.get("email", ""),
            "role": role,
        },
        "classes": classes,
    }


@router.put("/me", response_model=dict)
async def update_current_user_profile(
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update current user profile"""
    updated_user = await auth_service.update_user_profile(
        current_user["id"], 
        user_data.dict(exclude_unset=True)
    )
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update user profile"
        )
    return updated_user


@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get user by ID (admin only or own profile)"""
    # Allow users to get their own profile or admin users to get any profile
    if user_id != current_user["id"] and current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_current_user_account(
    current_user: dict = Depends(get_current_user)
):
    """Delete current user account"""
    success = await auth_service.delete_user(current_user["id"])
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete user account"
        )


@router.post("/change-password", response_model=dict)
async def change_password(
    new_password: str,
    current_user: dict = Depends(get_current_user)
):
    """Change user password"""
    success = await auth_service.change_user_password(
        current_user["id"], 
        new_password
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to change password"
        )
    return {"message": "Password changed successfully"}
