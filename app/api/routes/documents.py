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