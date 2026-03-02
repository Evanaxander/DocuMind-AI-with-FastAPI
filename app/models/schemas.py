from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List

# Auth
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: str
    created_at: datetime
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# Documents
class DocumentOut(BaseModel):
    id: int
    original_name: str
    page_count: int
    chunk_count: int
    created_at: datetime
    class Config:
        from_attributes = True

# Chat
class ChatRequest(BaseModel):
    question: str
    document_id: int

class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    tokens_used: int
    document_id: int

class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    tokens_used: int
    created_at: datetime
    class Config:
        from_attributes = True