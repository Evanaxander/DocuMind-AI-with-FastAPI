# 🧠 DocuMind AI — Full Stack AI Document Intelligence Platform
### A CV-Worthy FastAPI + LLM Project

---

## 🎯 What You're Building

**DocuMind AI** — A production-grade platform where users can:
- Upload PDF/text documents
- Ask questions about them (RAG — Retrieval Augmented Generation)
- Get AI-powered summaries
- Chat with document history
- See token usage and response metadata

**Tech Stack:**
| Layer | Technology |
|---|---|
| Backend API | FastAPI (Python) |
| LLM | Anthropic Claude API (or OpenAI) |
| Vector Store | ChromaDB (local) |
| Embeddings | sentence-transformers |
| PDF Parsing | PyMuPDF (fitz) |
| Frontend | HTML + JS (or React) |
| Auth | JWT via python-jose |
| DB | SQLite via SQLAlchemy |
| Testing | pytest + httpx |
| Deployment | Docker + Railway/Render |

---

## 📁 Project Structure

```
documind-ai/
│
├── app/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app entry point
│   ├── config.py                # Settings / env vars
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── __init__.py
│   │   │   ├── documents.py     # Upload, list, delete docs
│   │   │   ├── chat.py          # Chat with documents
│   │   │   ├── auth.py          # Register, login, JWT
│   │   │   └── health.py        # Health check
│   │   └── deps.py              # Shared dependencies (auth, db)
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py          # JWT logic
│   │   └── exceptions.py        # Custom exceptions
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm_service.py       # Anthropic/OpenAI calls
│   │   ├── embedding_service.py # Text → vectors
│   │   ├── vector_store.py      # ChromaDB operations
│   │   └── document_parser.py   # PDF/text extraction
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py          # SQLAlchemy models
│   │   └── schemas.py           # Pydantic schemas
│   │
│   └── db/
│       ├── __init__.py
│       └── session.py           # DB session management
│
├── tests/
│   ├── __init__.py
│   ├── test_documents.py
│   ├── test_chat.py
│   └── test_auth.py
│
├── frontend/
│   └── index.html               # The UI
│
├── uploads/                     # Uploaded files (gitignored)
├── chroma_db/                   # Vector DB (gitignored)
│
├── .env                         # Secrets (gitignored)
├── .env.example                 # Template for .env
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

## ⚙️ Step 1 — Environment Setup

### Create project and virtual environment
```bash
mkdir documind-ai
cd documind-ai
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate
```

### Install dependencies
```bash
pip install fastapi uvicorn[standard] python-multipart \
  anthropic openai \
  chromadb sentence-transformers \
  pymupdf sqlalchemy aiosqlite \
  python-jose[cryptography] passlib[bcrypt] \
  python-dotenv pydantic-settings \
  httpx pytest pytest-asyncio
```

### Create requirements.txt
```bash
pip freeze > requirements.txt
```

---

## 🔐 Step 2 — Configuration

### `.env` file
```env
# API Keys
ANTHROPIC_API_KEY=your_anthropic_key_here

# JWT
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# App
APP_NAME=DocuMind AI
DEBUG=True
UPLOAD_DIR=uploads
CHROMA_DIR=chroma_db
```

### `app/config.py`
```python
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    APP_NAME: str = "DocuMind AI"
    DEBUG: bool = False
    
    ANTHROPIC_API_KEY: str
    
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    UPLOAD_DIR: str = "uploads"
    CHROMA_DIR: str = "chroma_db"
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./documind.db"
    
    class Config:
        env_file = ".env"

settings = Settings()

# Ensure directories exist
Path(settings.UPLOAD_DIR).mkdir(exist_ok=True)
Path(settings.CHROMA_DIR).mkdir(exist_ok=True)
```

---

## 🗄️ Step 3 — Database Models

### `app/models/database.py`
```python
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    documents = relationship("Document", back_populates="owner")

class Document(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    page_count = Column(Integer, default=0)
    chunk_count = Column(Integer, default=0)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    owner = relationship("User", back_populates="documents")
    chats = relationship("ChatMessage", back_populates="document")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"))
    role = Column(String, nullable=False)   # "user" or "assistant"
    content = Column(Text, nullable=False)
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    document = relationship("Document", back_populates="chats")
```

### `app/models/schemas.py`
```python
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
```

### `app/db/session.py`
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models.database import Base

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

---

## 🔑 Step 4 — Auth & Security

### `app/core/security.py`
```python
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
```

### `app/api/deps.py`
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError
from app.core.security import decode_token
from app.models.database import User
from app.db.session import get_db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user
```

---

## 📄 Step 5 — Document Parser Service

### `app/services/document_parser.py`
```python
import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Tuple

def extract_text_from_pdf(file_path: str) -> Tuple[str, int]:
    """Extract all text from PDF. Returns (text, page_count)."""
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text, len(doc)

def extract_text_from_txt(file_path: str) -> Tuple[str, int]:
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()
    return text, 1

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks for better retrieval."""
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks

def parse_document(file_path: str) -> Tuple[List[str], int]:
    """Parse document and return (chunks, page_count)."""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        text, pages = extract_text_from_pdf(file_path)
    elif ext in [".txt", ".md"]:
        text, pages = extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")
    
    chunks = chunk_text(text)
    return chunks, pages
```

---

## 🔢 Step 6 — Vector Store Service

### `app/services/vector_store.py`
```python
import chromadb
from sentence_transformers import SentenceTransformer
from app.config import settings
from typing import List

# Initialize once
_client = chromadb.PersistentClient(path=settings.CHROMA_DIR)
_encoder = SentenceTransformer("all-MiniLM-L6-v2")

def get_collection(doc_id: int):
    return _client.get_or_create_collection(f"doc_{doc_id}")

def add_chunks(doc_id: int, chunks: List[str]):
    """Embed and store chunks for a document."""
    collection = get_collection(doc_id)
    embeddings = _encoder.encode(chunks).tolist()
    ids = [f"chunk_{i}" for i in range(len(chunks))]
    collection.add(documents=chunks, embeddings=embeddings, ids=ids)

def search_chunks(doc_id: int, query: str, n_results: int = 5) -> List[str]:
    """Find the most relevant chunks for a query."""
    collection = get_collection(doc_id)
    query_embedding = _encoder.encode([query]).tolist()
    results = collection.query(query_embeddings=query_embedding, n_results=n_results)
    return results["documents"][0] if results["documents"] else []

def delete_document_vectors(doc_id: int):
    try:
        _client.delete_collection(f"doc_{doc_id}")
    except Exception:
        pass
```

---

## 🤖 Step 7 — LLM Service

### `app/services/llm_service.py`
```python
import anthropic
from app.config import settings
from typing import List, Tuple

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

SYSTEM_PROMPT = """You are DocuMind AI, an expert document analyst.
Answer questions based ONLY on the provided document context.
If the answer is not in the context, say "I couldn't find that in the document."
Be concise, accurate, and cite relevant parts of the context."""

def ask_question(question: str, context_chunks: List[str]) -> Tuple[str, int]:
    """Send question + context to Claude and return (answer, tokens_used)."""
    context = "\n\n---\n\n".join(context_chunks)
    
    user_message = f"""Here is the relevant document context:

{context}

---

Question: {question}

Please answer based on the context above."""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}]
    )
    
    answer = response.content[0].text
    tokens = response.usage.input_tokens + response.usage.output_tokens
    return answer, tokens

async def generate_summary(text_sample: str) -> str:
    """Generate a brief document summary."""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": f"Summarize this document in 3 sentences:\n\n{text_sample[:3000]}"
        }]
    )
    return response.content[0].text
```

---

## 🛣️ Step 8 — API Routes

### `app/api/routes/auth.py`
```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models.database import User
from app.models.schemas import UserCreate, UserOut, Token
from app.core.security import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserOut, status_code=201)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(email=user_data.email, hashed_password=hash_password(user_data.password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}
```

### `app/api/routes/documents.py`
```python
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import shutil, uuid
from pathlib import Path
from app.db.session import get_db
from app.models.database import User, Document
from app.models.schemas import DocumentOut
from app.api.deps import get_current_user
from app.services.document_parser import parse_document
from app.services.vector_store import add_chunks, delete_document_vectors
from app.config import settings

router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_TYPES = {".pdf", ".txt", ".md"}

@router.post("/upload", response_model=DocumentOut, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"File type {ext} not supported")
    
    # Save file
    unique_name = f"{uuid.uuid4()}{ext}"
    file_path = Path(settings.UPLOAD_DIR) / unique_name
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Parse and embed
    try:
        chunks, pages = parse_document(str(file_path))
    except Exception as e:
        file_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=str(e))
    
    # Save to DB
    doc = Document(
        filename=unique_name,
        original_name=file.filename,
        file_path=str(file_path),
        page_count=pages,
        chunk_count=len(chunks),
        owner_id=current_user.id
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    
    # Store vectors (doc.id now available)
    add_chunks(doc.id, chunks)
    
    return doc

@router.get("/", response_model=List[DocumentOut])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Document).where(Document.owner_id == current_user.id)
    )
    return result.scalars().all()

@router.delete("/{doc_id}", status_code=204)
async def delete_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(Document).where(Document.id == doc_id, Document.owner_id == current_user.id)
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    Path(doc.file_path).unlink(missing_ok=True)
    delete_document_vectors(doc_id)
    await db.delete(doc)
    await db.commit()
```

### `app/api/routes/chat.py`
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.db.session import get_db
from app.models.database import User, Document, ChatMessage
from app.models.schemas import ChatRequest, ChatResponse, ChatMessageOut
from app.api.deps import get_current_user
from app.services.vector_store import search_chunks
from app.services.llm_service import ask_question

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/", response_model=ChatResponse)
async def chat_with_document(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Verify document ownership
    result = await db.execute(
        select(Document).where(
            Document.id == request.document_id,
            Document.owner_id == current_user.id
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Retrieve relevant chunks
    relevant_chunks = search_chunks(request.document_id, request.question)
    if not relevant_chunks:
        raise HTTPException(status_code=422, detail="No relevant content found")
    
    # Get AI answer
    answer, tokens = ask_question(request.question, relevant_chunks)
    
    # Save to DB
    user_msg = ChatMessage(document_id=doc.id, role="user", content=request.question)
    ai_msg = ChatMessage(document_id=doc.id, role="assistant", content=answer, tokens_used=tokens)
    db.add_all([user_msg, ai_msg])
    await db.commit()
    
    return ChatResponse(
        answer=answer,
        sources=relevant_chunks[:3],
        tokens_used=tokens,
        document_id=doc.id
    )

@router.get("/{doc_id}/history", response_model=List[ChatMessageOut])
async def get_chat_history(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(
        select(ChatMessage)
        .join(Document)
        .where(Document.id == doc_id, Document.owner_id == current_user.id)
        .order_by(ChatMessage.created_at)
    )
    return result.scalars().all()
```

### `app/api/routes/health.py`
```python
from fastapi import APIRouter
router = APIRouter(tags=["Health"])

@router.get("/health")
async def health():
    return {"status": "ok", "service": "DocuMind AI"}
```

---

## 🚀 Step 9 — Main App Entry Point

### `app/main.py`
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.config import settings
from app.db.session import init_db
from app.api.routes import auth, documents, chat, health

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()  # Create tables on startup
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered document intelligence platform",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(documents.router, prefix="/api")
app.include_router(chat.router, prefix="/api")

# Serve frontend
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
```

---

## 🧪 Step 10 — Tests

### `tests/test_auth.py`
```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_register_and_login():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register
        res = await client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "securepass123"
        })
        assert res.status_code == 201
        
        # Login
        res = await client.post("/api/auth/login", data={
            "username": "test@example.com",
            "password": "securepass123"
        })
        assert res.status_code == 200
        assert "access_token" in res.json()
```

---

## 🐳 Step 11 — Docker

### `Dockerfile`
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p uploads chroma_db

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `docker-compose.yml`
```yaml
version: "3.9"
services:
  api:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./uploads:/app/uploads
      - ./chroma_db:/app/chroma_db
```

---

## ▶️ Running the App

```bash
# Development
uvicorn app.main:app --reload

# Visit:
# API docs:  http://localhost:8000/docs
# Frontend:  http://localhost:8000
# Health:    http://localhost:8000/api/health
```

---

## 📊 API Endpoints Summary

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| GET | `/api/health` | ❌ | Health check |
| POST | `/api/auth/register` | ❌ | Register user |
| POST | `/api/auth/login` | ❌ | Get JWT token |
| POST | `/api/documents/upload` | ✅ | Upload a document |
| GET | `/api/documents/` | ✅ | List your documents |
| DELETE | `/api/documents/{id}` | ✅ | Delete a document |
| POST | `/api/chat/` | ✅ | Chat with a document |
| GET | `/api/chat/{id}/history` | ✅ | Get chat history |

---

## 🎓 CV Skills This Project Demonstrates

- ✅ **FastAPI** — async REST APIs, Pydantic validation, OpenAPI docs
- ✅ **RAG Architecture** — Retrieval Augmented Generation from scratch
- ✅ **Vector Databases** — ChromaDB, semantic search, embeddings
- ✅ **LLM Integration** — Anthropic Claude API
- ✅ **JWT Authentication** — secure endpoints, OAuth2 flow
- ✅ **SQLAlchemy (Async)** — ORM, migrations, relationships
- ✅ **File Handling** — upload, parse, process PDFs
- ✅ **NLP / Embeddings** — sentence-transformers, chunking strategies
- ✅ **Docker** — containerized deployment
- ✅ **Testing** — pytest async tests with httpx
- ✅ **Software Architecture** — layered services, dependency injection

---

## 🚀 Deployment (Free Tiers)

1. **Railway** — `railway up` (supports Docker, free tier available)
2. **Render** — Connect GitHub repo, auto-deploy on push
3. **Fly.io** — `fly deploy` with the Dockerfile

---

## 💡 Extensions to Impress Further

- Add **streaming responses** with `StreamingResponse`  
- Add **multi-document** cross-search  
- Add **Redis caching** for frequent queries  
- Build a **React frontend** with Tailwind  
- Add **rate limiting** with slowapi  
- Add **Celery + background tasks** for async processing  
