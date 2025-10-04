"""
Authentication and authorization dependencies for FastAPI endpoints.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.services.auth_service import auth_service
from app.schemas.user_schemas import UserRole
from app.core.exceptions import AuthenticationError

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """Get current user from JWT token"""
    try:
        token = credentials.credentials
        user_data = await auth_service.verify_token(token)
        if not user_data:
            raise AuthenticationError("Invalid or expired token")
        return user_data
    except AuthenticationError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[dict]:
    """Get current user from JWT token (optional - returns None if no token)"""
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        user_data = await auth_service.verify_token(token)
        return user_data
    except Exception:
        return None


def require_role(required_role: UserRole):
    """Dependency factory that creates a role-checking dependency"""
    async def check_role(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role")
        if user_role != required_role.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {required_role.value}, current role: {user_role}"
            )
        return current_user
    return check_role


def require_any_role(*required_roles: UserRole):
    """Dependency factory that creates a multi-role checking dependency"""
    async def check_roles(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role")
        allowed_roles = [role.value for role in required_roles]
        
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {allowed_roles}, current role: {user_role}"
            )
        return current_user
    return check_roles


# Specific role dependencies for common use cases
require_teacher = require_role(UserRole.TEACHER)
require_admin = require_role(UserRole.ADMIN)
require_student = require_role(UserRole.STUDENT)

# Combined role dependencies
require_teacher_or_admin = require_any_role(UserRole.TEACHER, UserRole.ADMIN)
require_any_authenticated = get_current_user
require_student_or_teacher = require_any_role(UserRole.STUDENT, UserRole.TEACHER)


async def get_current_teacher(current_user: dict = Depends(require_teacher)) -> dict:
    """Get current user ensuring they are a teacher"""
    return current_user


async def get_current_admin(current_user: dict = Depends(require_admin)) -> dict:
    """Get current user ensuring they are an admin"""
    return current_user


async def get_current_teacher_or_admin(
    current_user: dict = Depends(require_teacher_or_admin)
) -> dict:
    """Get current user ensuring they are either a teacher or admin"""
    return current_user


def verify_class_ownership(teacher_id_field: str = "teacher_id"):
    """
    Dependency factory to verify that a teacher owns/created a specific class.
    Used for operations where teachers should only modify their own classes.
    """
    async def check_ownership(
        class_id: str,
        current_teacher: dict = Depends(get_current_teacher)
    ) -> dict:
        # This would need to be implemented with actual class ownership checking
        # For now, we'll just return the teacher data
        # In a real implementation, you'd query the database to verify ownership
        teacher_user_id = current_teacher.get("id")
        
        # TODO: Implement actual class ownership verification
        # Example:
        # class_data = await class_service.get_class(class_id)
        # if class_data.get(teacher_id_field) != teacher_user_id:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="You can only modify classes you created"
        #     )
        
        return current_teacher
    
    return check_ownership
