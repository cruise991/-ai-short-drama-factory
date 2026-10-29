import os
import json
import re
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query, Body, status
from pydantic import BaseModel, Field
import jieba
from rank_bm25 import BM25Plus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [RAG] %(message)s"
)
logger = logging.getLogger("rag-service")

default_storage = "/data/rag_storage" if os.path.exists("/data") else os.path.join(os.path.dirname(__file__), "storage")
STORAGE_DIR = Path(os.getenv("RAG_STORAGE_DIR", default_storage))
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

CHUNK_SIZE = int(os.getenv("RAG_CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("RAG_CHUNK_OVERLAP", "64"))

app = FastAPI(
    title="LingCast RAG Knowledge Service",
    version="1.0.0",
    description="High-performance lightweight BM25 & text-chunking retrieval service for live-streaming e-commerce & FAQ."
)

class DocumentItem(BaseModel):
    doc_id: Optional[str] = None
    title: Optional[str] = None
    content: str = Field(..., min_length=1, description="Raw document content")
    metadata: Optional[Dict[str, Any]] = None

class IndexRequest(BaseModel):
    kb_id: str = Field(..., min_length=1, description="Knowledge Base unique identifier")
    tenant_id: Optional[str] = Field(default="default", description="Multi-tenant tenant ID")
    documents: List[DocumentItem] = Field(..., min_length=1)
    chunk_size: Optional[int] = Field(default=CHUNK_SIZE)
    chunk_overlap: Optional[int] = Field(default=CHUNK_OVERLAP)

class SearchRequest(BaseModel):
    kb_id: str = Field(..., min_length=1)
    tenant_id: Optional[str] = Field(default="default")
    query: str = Field(..., min_length=1)
    top_k: int = Field(default=3, ge=1, le=20)
    min_score: Optional[float] = Field(default=0.0)

class ChunkResult(BaseModel):
    chunk_id: str
    doc_id: Optional[str]
    title: Optional[str]
    content: str
    score: float
    metadata: Dict[str, Any]

class SearchResponse(BaseModel):
    kb_id: str
    query: str
    total_chunks: int
    results: List[ChunkResult]

class KBStore:
    def __init__(self, kb_id: str, tenant_id: str = "default"):
        self.kb_id = kb_id
        self.tenant_id = tenant_id
        self.file_path = STORAGE_DIR / f"{tenant_id}_{kb_id}.json"
        self.chunks: List[Dict[str, Any]] = []
        self.corpus_tokens: List[List[str]] = []
        self.bm25: Optional[BM25Plus] = None
        self._load()

    def _tokenize(self, text: str) -> List[str]:
        cleaned = re.sub(r"[\r\n\t]+", " ", text).strip()
        if not cleaned:
            return []
        # Jieba tokenize handles both Chinese and English characters cleanly
        words = jieba.lcut(cleaned)
        return [w.strip().lower() for w in words if w.strip()]

    def _chunk_text(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        if len(text) <= chunk_size:
            return [text.strip()]
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= len(text):
                break
            start += (chunk_size - chunk_overlap)
        return chunks

    def add_documents(self, documents: List[DocumentItem], chunk_size: int, chunk_overlap: int):
        for doc_idx, doc in enumerate(documents):
            raw_chunks = self._chunk_text(doc.content, chunk_size, chunk_overlap)
            doc_id = doc.doc_id or f"doc_{doc_idx}"
            for c_idx, c_text in enumerate(raw_chunks):
                chunk_id = f"{doc_id}_c{c_idx}"
                self.chunks.append({
                    "chunk_id": chunk_id,
                    "doc_id": doc_id,
                    "title": doc.title or "",
                    "content": c_text,
                    "metadata": doc.metadata or {}
                })
        self._rebuild_index()
        self._save()

    def _rebuild_index(self):
        self.corpus_tokens = [self._tokenize(c["content"]) for c in self.chunks]
        if self.corpus_tokens:
            self.bm25 = BM25Plus(self.corpus_tokens)
        else:
            self.bm25 = None

    def search(self, query: str, top_k: int = 3, min_score: float = 0.0) -> List[ChunkResult]:
        if not self.bm25 or not self.chunks:
            return []
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
        scores = self.bm25.get_scores(query_tokens)
        
        # Rank by score
        scored_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        results = []
        for idx in scored_indices[:top_k]:
            score = float(scores[idx])
            if score < min_score:
                continue
            chunk = self.chunks[idx]
            results.append(ChunkResult(
                chunk_id=chunk["chunk_id"],
                doc_id=chunk.get("doc_id"),
                title=chunk.get("title"),
                content=chunk["content"],
                score=round(score, 4),
                metadata=chunk.get("metadata", {})
            ))
        return results

    def _save(self):
        data = {
            "kb_id": self.kb_id,
            "tenant_id": self.tenant_id,
            "chunks": self.chunks
        }
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _load(self):
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.chunks = data.get("chunks", [])
                self._rebuild_index()
                logger.info(f"Loaded KB [{self.tenant_id}:{self.kb_id}] with {len(self.chunks)} chunks")
            except Exception as e:
                logger.error(f"Failed to load existing KB {self.file_path}: {e}")
                self.chunks = []
                self.bm25 = None

    def delete(self):
        self.chunks = []
        self.corpus_tokens = []
        self.bm25 = None
        if self.file_path.exists():
            self.file_path.unlink()

# Cache active stores
_STORES: Dict[str, KBStore] = {}

def get_store(kb_id: str, tenant_id: str = "default") -> KBStore:
    key = f"{tenant_id}:{kb_id}"
    if key not in _STORES:
        _STORES[key] = KBStore(kb_id, tenant_id)
    return _STORES[key]

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "rag",
        "storage_dir": str(STORAGE_DIR),
        "cached_kbs": len(_STORES)
    }

@app.post("/index", status_code=status.HTTP_201_CREATED)
async def index_documents(req: IndexRequest):
    try:
        store = get_store(req.kb_id, req.tenant_id)
        store.add_documents(req.documents, req.chunk_size or CHUNK_SIZE, req.chunk_overlap or CHUNK_OVERLAP)
        return {
            "status": "ok",
            "kb_id": req.kb_id,
            "tenant_id": req.tenant_id,
            "total_chunks": len(store.chunks),
            "message": f"Successfully indexed {len(req.documents)} documents ({len(store.chunks)} total chunks)."
        }
    except Exception as e:
        logger.error(f"Failed to index documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search", response_model=SearchResponse)
async def search_knowledge(req: SearchRequest):
    try:
        store = get_store(req.kb_id, req.tenant_id)
        results = store.search(req.query, req.top_k, req.min_score or 0.0)
        return SearchResponse(
            kb_id=req.kb_id,
            query=req.query,
            total_chunks=len(store.chunks),
            results=results
        )
    except Exception as e:
        logger.error(f"Search failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/index/{kb_id}")
async def delete_knowledge_base(kb_id: str, tenant_id: str = Query("default")):
    key = f"{tenant_id}:{kb_id}"
    store = get_store(kb_id, tenant_id)
    store.delete()
    if key in _STORES:
        del _STORES[key]
    return {"status": "ok", "message": f"Knowledge base [{kb_id}] deleted."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
