from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class ChatRequest(BaseModel):
    message: str

class ImageLogBase(BaseModel):
    filename: str
    classification: str

class ImageLog(ImageLogBase):
    id: int
    timestamp: datetime
    user_id: int

    class Config:
        from_attributes = True