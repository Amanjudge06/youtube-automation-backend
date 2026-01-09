"""
Authentication and Authorization Module
Handles JWT token validation and user context extraction
"""

from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)

security = HTTPBearer()

# Get Supabase JWT secret from environment
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
if not SUPABASE_JWT_SECRET:
    logger.warning("⚠️  SUPABASE_JWT_SECRET not set - authentication will fail")

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> str:
    """
    Validate JWT token and extract user ID.
    
    Args:
        credentials: JWT token from Authorization header
        
    Returns:
        str: User ID (UUID) from token
        
    Raises:
        HTTPException: If token is invalid or missing
    """
    token = credentials.credentials
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False}  # Supabase tokens don't always have aud
        )
        
        # Extract user ID from 'sub' claim
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials - no user ID in token"
            )
        
        logger.debug(f"Authenticated user: {user_id}")
        return user_id
        
    except JWTError as e:
        logger.error(f"JWT validation failed: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail=f"Could not validate credentials: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Authentication failed"
        )


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security)
) -> Optional[str]:
    """
    Optional authentication - returns user ID if valid token provided, None otherwise.
    Useful for endpoints that work with or without authentication.
    
    Args:
        credentials: Optional JWT token from Authorization header
        
    Returns:
        Optional[str]: User ID if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        return get_current_user(credentials)
    except HTTPException:
        return None


# Dependency for protected routes
async def require_auth(user_id: str = Depends(get_current_user)) -> str:
    """
    Dependency that requires authentication.
    Use in FastAPI route definitions: user_id: str = Depends(require_auth)
    """
    return user_id


# For backwards compatibility during migration
DEMO_USER_ID = "demo_user"

def get_user_or_demo(user_id: Optional[str] = Depends(get_optional_user)) -> str:
    """
    Temporary helper for gradual migration to full authentication.
    Returns authenticated user ID or falls back to demo_user.
    
    TODO: Remove this once all clients are using authentication
    """
    return user_id if user_id else DEMO_USER_ID
