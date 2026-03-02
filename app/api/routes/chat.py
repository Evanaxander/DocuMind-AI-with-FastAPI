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