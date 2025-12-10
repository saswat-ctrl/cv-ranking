from typing import Optional
from pydantic import BaseModel, EmailStr, UUID4, Field
from datetime import datetime

# Shared properties
class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None

# Properties to receive via API on creation
class UserCreate(UserBase):
    password: Optional[str] = None

# Properties to receive via API on password set
class UserSetPassword(BaseModel):
    user_id: UUID4
    password: str

# Properties to receive via API on login
class UserLogin(BaseModel):
    email: EmailStr
    password: str

# Properties to return to client
class UserResponse(UserBase):
    id: UUID4
    is_verified: bool
    created_at: datetime

    @classmethod
    def model_validate(cls, obj, **kwargs):
        # Map 'name' from database model to 'full_name' for API response
        if hasattr(obj, 'name') and not hasattr(obj, 'full_name'):
            obj_dict = {
                'id': obj.id,
                'email': obj.email,
                'full_name': obj.name,  # Map name to full_name
                'is_verified': obj.is_verified,
                'created_at': obj.created_at
            }
            return super().model_validate(obj_dict, **kwargs)
        return super().model_validate(obj, **kwargs)

    class Config:
        from_attributes = True
        populate_by_name = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None
