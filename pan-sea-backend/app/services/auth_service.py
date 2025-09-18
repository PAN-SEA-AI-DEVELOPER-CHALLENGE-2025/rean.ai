"""
Authentication service with comprehensive error handling and type hints.
"""
from typing import Optional, Dict, Any, Union
import logging
import secrets
from jose import jwt
from datetime import datetime, timedelta
from uuid import UUID
from passlib.context import CryptContext

from app.database.database import db_manager
from app.schemas.user_schemas import UserCreate
from app.config import settings
from app.core.cache import cache_service, CacheKeys
from app.core.exceptions import (
    AuthenticationError,
    ConflictError,
    ValidationError,
    DatabaseError
)

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations using PostgreSQL"""
    
    def __init__(self) -> None:
        self.secret_key: str = settings.secret_key
        self.algorithm: str = getattr(settings, 'algorithm', 'HS256')
        self.access_token_expire_minutes: int = getattr(settings, 'access_token_expire_minutes', 30)
        # Initialize secure password hashing context
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt (secure)"""
        if not password:
            raise ValidationError("Password cannot be empty")
        return self.pwd_context.hash(password)
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against bcrypt hash with SHA-256 fallback for legacy passwords"""
        try:
            # Check if this is a legacy SHA-256 hash first
            if self._is_legacy_password(hashed_password):
                # This is a legacy SHA-256 hash, verify it
                import hashlib
                sha256_hash = hashlib.sha256(plain_password.encode()).hexdigest()
                if sha256_hash == hashed_password:
                    logger.info("Legacy password verified, should be rehashed with bcrypt")
                    return True
                return False
            
            # Try bcrypt for new passwords
            try:
                return self.pwd_context.verify(plain_password, hashed_password)
            except Exception:
                # If bcrypt verification fails, it might be an invalid hash
                return False
            
        except Exception as e:
            logger.error(f"Password verification error: {str(e)}")
            return False
    
    def _create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        try:
            import time
            to_encode = data.copy()
            if expires_delta:
                expire_timestamp = int(time.time() + expires_delta.total_seconds())
            else:
                expire_timestamp = int(time.time() + (self.access_token_expire_minutes * 60))
            
            to_encode.update({"exp": expire_timestamp})
            encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
            return encoded_jwt
        except Exception as e:
            logger.error(f"Token creation error: {str(e)}")
            raise AuthenticationError("Failed to create access token")
    
    def _create_refresh_token(self) -> str:
        """Create a refresh token"""
        return secrets.token_urlsafe(32)
    
    async def register_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """Register a new user"""
        try:
            # Validate input
            if not user_data.email or not user_data.username or not user_data.password:
                raise ValidationError("Email, username, and password are required")
            
            # Check if user already exists
            existing_user = await self.get_user_by_email(user_data.email)
            if existing_user:
                raise ConflictError("User with this email already exists")
            
            existing_username = await self.get_user_by_username(user_data.username)
            if existing_username:
                raise ConflictError("Username already taken")
            
            # Hash password
            hashed_password = self._hash_password(user_data.password)
            
            # Generate UUID for the user
            import uuid
            user_id = str(uuid.uuid4())
            
            # Insert user into users table
            query = """
                INSERT INTO users (id, email, username, full_name, hashed_password, role, phone_number, bio)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                RETURNING id, email, username, full_name, role, is_active, is_verified, created_at
            """
            
            result = await db_manager.execute_insert_with_returning(
                query,
                user_id,
                user_data.email,
                user_data.username,
                user_data.full_name,
                hashed_password,
                user_data.role,
                user_data.phone_number,
                user_data.bio
            )
            
            if not result:
                raise DatabaseError("Failed to create user")
            
            user = dict(result[0])
            
            # Create tokens
            access_token = self._create_access_token(
                data={"sub": str(user["id"]), "email": user["email"]}
            )
            
            refresh_token = self._create_refresh_token()
            expires_at = datetime.utcnow() + timedelta(days=30)
            
            # Store refresh token
            await self._store_refresh_token(user["id"], refresh_token, expires_at)
            
            return {
                "user": user,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
            
        except (ConflictError, ValidationError, AuthenticationError) as e:
            raise e
        except Exception as e:
            logger.error(f"User registration error: {str(e)}", exc_info=True)
            raise DatabaseError("Failed to register user")
    
    async def login_user(self, email_or_username: str, password: str) -> Dict[str, Any]:
        """Login user with email/username and password"""
        try:
            if not email_or_username or not password:
                raise ValidationError("Email/username and password are required")
            
            # Try to get user by email or username in a single query
            user = await self.get_user_by_email_or_username(email_or_username)
            
            if not user:
                raise AuthenticationError("Invalid credentials")
            
            # Verify password
            if not self._verify_password(password, user["hashed_password"]):
                raise AuthenticationError("Invalid credentials")
            
            # Check if we need to upgrade legacy password to bcrypt
            if self._is_legacy_password(user["hashed_password"]):
                await self._upgrade_legacy_password(user["id"], password)
            
            # Check if user is active
            if not user.get("is_active", False):
                raise AuthenticationError("Account is deactivated")
            
            # Create access token
            access_token = self._create_access_token(
                data={"sub": str(user["id"]), "email": user["email"]}
            )
            
            # Create refresh token
            refresh_token = self._create_refresh_token()
            expires_at = datetime.utcnow() + timedelta(days=30)
            
            # Store refresh token
            await self._store_refresh_token(user["id"], refresh_token, expires_at)
            
            # Update last login
            await self._update_last_login(user["id"])
            
            # Remove sensitive data
            user_response = {k: v for k, v in user.items() if k != "hashed_password"}
            
            return {
                "user": user_response,
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
            
        except (AuthenticationError, ValidationError) as e:
            raise e
        except Exception as e:
            logger.error(f"User login error: {str(e)}", exc_info=True)
            raise AuthenticationError("Login failed")
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            if not email:
                return None
                
            query = "SELECT * FROM users WHERE email = $1"
            result = await db_manager.execute_query(query, email)
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None
    
    async def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""
        try:
            if not username:
                return None
                
            query = "SELECT * FROM users WHERE username = $1"
            result = await db_manager.execute_query(query, username)
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting user by username: {str(e)}")
            return None
    
    async def get_user_by_email_or_username(self, email_or_username: str) -> Optional[Dict[str, Any]]:
        """Get user by email or username in a single optimized query with caching"""
        try:
            if not email_or_username:
                return None
            
            # Try cache first
            cache_key = cache_service.generate_key(CacheKeys.USER_BY_EMAIL, email_or_username)
            cached_user = await cache_service.get(cache_key)
            if cached_user:
                return cached_user
                
            query = "SELECT * FROM users WHERE email = $1 OR username = $1 LIMIT 1"
            result = await db_manager.execute_query(query, email_or_username)
            user = result[0] if result else None
            
            # Cache the result for 5 minutes
            if user:
                await cache_service.set(cache_key, user, 300)
            
            return user
        except Exception as e:
            logger.error(f"Error getting user by email or username: {str(e)}")
            return None
    
    async def get_user_by_id(self, user_id: Union[str, UUID]) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            if not user_id:
                return None
                
            query = "SELECT * FROM users WHERE id = $1"
            result = await db_manager.execute_query(query, str(user_id))
            return result[0] if result else None
        except Exception as e:
            logger.error(f"Error getting user by ID: {str(e)}")
            return None
    
    async def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return user data"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            if not user_id:
                return None
            
            user = await self.get_user_by_id(user_id)
            return user
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.JWTError:
            raise AuthenticationError("Invalid token")
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            raise AuthenticationError("Token verification failed")
    
    async def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            if not refresh_token:
                raise ValidationError("Refresh token is required")
            
            # Get refresh token from database
            query = """
                SELECT rt.*, u.id, u.email 
                FROM refresh_tokens rt 
                JOIN users u ON rt.user_id = u.id 
                WHERE rt.token = $1 AND rt.expires_at > NOW() AND rt.is_revoked = false
            """
            result = await db_manager.execute_query(query, refresh_token)
            
            if not result:
                raise AuthenticationError("Invalid or expired refresh token")
            
            token_data = result[0]
            
            # Create new access token
            access_token = self._create_access_token(
                data={"sub": str(token_data["id"]), "email": token_data["email"]}
            )
            
            return {
                "access_token": access_token,
                "token_type": "bearer"
            }
            
        except (AuthenticationError, ValidationError) as e:
            raise e
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}", exc_info=True)
            raise AuthenticationError("Failed to refresh token")
    
    async def logout_user(self, refresh_token: str) -> bool:
        """Logout user by revoking refresh token"""
        try:
            if not refresh_token:
                return False
            
            query = "UPDATE refresh_tokens SET is_revoked = true WHERE token = $1"
            await db_manager.execute_command(query, refresh_token)
            return True
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return False
    
    async def _store_refresh_token(
        self, 
        user_id: Union[str, UUID], 
        token: str, 
        expires_at: datetime
    ) -> None:
        """Store refresh token in database"""
        try:
            import uuid
            token_id = str(uuid.uuid4())
            
            query = """
                INSERT INTO refresh_tokens (id, user_id, token, expires_at)
                VALUES ($1, $2, $3, $4)
            """
            await db_manager.execute_command(query, token_id, str(user_id), token, expires_at)
        except Exception as e:
            logger.error(f"Error storing refresh token: {str(e)}")
            raise DatabaseError("Failed to store refresh token")
    
    async def _update_last_login(self, user_id: Union[str, UUID]) -> None:
        """Update user's last login timestamp"""
        try:
            query = "UPDATE users SET last_login = NOW() WHERE id = $1"
            await db_manager.execute_command(query, str(user_id))
        except Exception as e:
            logger.error(f"Error updating last login: {str(e)}")
            # Non-critical error, don't raise
    
    def _is_legacy_password(self, hashed_password: str) -> bool:
        """Check if password is using legacy SHA-256 hashing"""
        return len(hashed_password) == 64 and hashed_password.isalnum()
    
    async def _upgrade_legacy_password(self, user_id: Union[str, UUID], plain_password: str) -> None:
        """Upgrade legacy SHA-256 password to bcrypt"""
        try:
            new_hash = self._hash_password(plain_password)
            query = "UPDATE users SET hashed_password = $1 WHERE id = $2"
            await db_manager.execute_command(query, new_hash, str(user_id))
            logger.info(f"Upgraded legacy password for user {user_id} to bcrypt")
        except Exception as e:
            logger.error(f"Error upgrading legacy password for user {user_id}: {str(e)}")
            # Non-critical error, don't raise


# Global auth service instance
auth_service = AuthService()