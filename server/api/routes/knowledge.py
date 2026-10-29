import os
import json
import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select
from pydantic import BaseModel
import requests

from models.database import (
    get_session,
    KnowledgeBase,
    KnowledgeDocument
)

logger = logging.getLogger("KnowledgeRoute")
router = APIRouter(prefix="/knowledge", tags=["knowledge"])

RAG_SERVICE_URL = os.getenv("RAG_SERVICE_URL", "http://localhost:8002")

class KBCreateReq(BaseModel):
    name: str
    tenant_id: Optional[str] = "default"
    description: Optional[str] = None
    chunk_size: Optional[int] = 512
    chunk_overlap: Optional[int] = 64

class DocumentCreateReq(BaseModel):
    title: str
    doc_id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class KBSearchReq(BaseModel):
    query: str
    top_k: Optional[int] = 3
    min_score: Optional[float] = 0.0

@router.get("", response_model=List[KnowledgeBase])
def list_knowledge_bases(
    tenant_id: Optional[str] = Query("default"),
    session: Session = Depends(get_session)
):
    query = select(KnowledgeBase).where(KnowledgeBase.tenant_id == tenant_id)
    return session.exec(query).all()

@router.post("", response_model=KnowledgeBase, status_code=status.HTTP_201_CREATED)
def create_knowledge_base(
    req: KBCreateReq,
    session: Session = Depends(get_session)
):
    kb = KnowledgeBase(
        name=req.name,
        tenant_id=req.tenant_id or "default",
        description=req.description,
        chunk_size=req.chunk_size or 512,
        chunk_overlap=req.chunk_overlap or 64,
        status="active"
    )
    session.add(kb)
    session.commit()
    session.refresh(kb)
    return kb

@router.get("/{kb_id}/documents", response_model=List[KnowledgeDocument])
def list_documents(
    kb_id: int,
    session: Session = Depends(get_session)
):
    query = select(KnowledgeDocument).where(KnowledgeDocument.kb_id == kb_id)
    return session.exec(query).all()

@router.post("/{kb_id}/documents", response_model=KnowledgeDocument, status_code=status.HTTP_201_CREATED)
def add_document(
    kb_id: int,
    req: DocumentCreateReq,
    session: Session = Depends(get_session)
):
    kb = session.get(KnowledgeBase, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail=f"Knowledge base {kb_id} not found")

    meta_json = json.dumps(req.metadata or {}, ensure_ascii=False)
    doc = KnowledgeDocument(
        kb_id=kb.id,
        tenant_id=kb.tenant_id,
        doc_id=req.doc_id,
        title=req.title,
        content=req.content,
        metadata_json=meta_json
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)

    # 同步索引到 RAG 微服务
    try:
        payload = {
            "kb_id": f"kb_{kb.id}",
            "tenant_id": kb.tenant_id,
            "documents": [
                {
                    "doc_id": req.doc_id,
                    "title": req.title,
                    "content": req.content,
                    "metadata": req.metadata or {}
                }
            ],
            "chunk_size": kb.chunk_size,
            "chunk_overlap": kb.chunk_overlap
        }
        requests.post(f"{RAG_SERVICE_URL}/index", json=payload, timeout=5.0)
    except Exception as e:
        logger.warning(f"Failed to sync document to RAG microservice: {e}")

    return doc

@router.post("/{kb_id}/search")
def search_knowledge_base(
    kb_id: int,
    req: KBSearchReq,
    session: Session = Depends(get_session)
):
    kb = session.get(KnowledgeBase, kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail=f"Knowledge base {kb_id} not found")

    try:
        payload = {
            "kb_id": f"kb_{kb.id}",
            "tenant_id": kb.tenant_id,
            "query": req.query,
            "top_k": req.top_k or 3,
            "min_score": req.min_score or 0.0
        }
        resp = requests.post(f"{RAG_SERVICE_URL}/search", json=payload, timeout=5.0)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.warning(f"RAG search error: {e}")

    # Fallback to local db match if microservice is offline
    docs = session.exec(select(KnowledgeDocument).where(KnowledgeDocument.kb_id == kb_id)).all()
    try:
        import jieba
        terms = [w.strip() for w in jieba.lcut(req.query) if len(w.strip()) > 1]
    except Exception:
        terms = [t for t in req.query.split() if t]

    matched = [d for d in docs if any(term in d.content or term in (d.title or "") for term in terms)]
    if not matched:
        matched = list(docs)

    return {
        "kb_id": f"kb_{kb.id}",
        "query": req.query,
        "total_chunks": len(docs),
        "results": [
            {
                "chunk_id": f"{d.doc_id}_c0",
                "doc_id": d.doc_id,
                "title": d.title,
                "content": d.content[:200],
                "score": 0.6,
                "metadata": {}
            } for d in matched[:req.top_k or 3]
        ]
    }
