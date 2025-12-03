from typing import Generator, Optional
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import TokenPayload
from app.core.config import settings
from app.core import security

logger = logging.getLogger(__name__)

reusable_oauth2 = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2)
) -> TokenPayload:
    # DEBUG: Log raw header if possible, but Depends(reusable_oauth2) extracts it.
    # We will print the token received by the dependency.
    print(f"DEBUG: deps.get_current_user received token: {token[:10]}... (len={len(token)})")
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        token_data = TokenPayload(**payload)
        # Debug minimal payload
        try:
            logger.debug("Decoded token", extra={"sub": token_data.sub, "exp": payload.get("exp")})
        except Exception:
            pass
    except (JWTError, ValidationError) as exc:
        # Use 401 Unauthorized for invalid/expired tokens to align with frontend handling
        # Log specific reason for token validation failure
        try:
            masked = f"{token[:8]}...{token[-8:]}" if isinstance(token, str) and len(token) > 16 else "<invalid>"
            logger.warning("Token validation failed: %s", str(exc), extra={"token": masked})
            print(f"TOKEN VALIDATION FAILED: {exc}") # Direct print for debugging
            print(f"Token: {token}")
        except Exception:
            logger.warning("Token validation failed: %s", str(exc))
            print(f"TOKEN VALIDATION FAILED (Exception): {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    
    if not token_data.sub:
        logger.warning("Token missing subject (sub)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing subject",
        )

    result = await db.execute(select(User).where(User.id == token_data.sub))
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
