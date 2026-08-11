"""
EduNavigator FastAPI backend - Local Mistral version
Runs completely locally without Google API key
Endpoints for career guidance with RAG + local LLM
"""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any

import orjson
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

from rag.ingest import IngestionService
from rag.retrieval import RetrievalService
from rag.generation_local import LocalGenerationService


def json_dumps(v: Any, *, default: Any = None) -> str:
    return orjson.dumps(v, default=default).decode()


app = FastAPI(
    title="EduNavigator Local",
    description="Career guidance with local Mistral LLM (no API key needed)"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Profile(BaseModel):
    branch: Optional[str] = None
    interests: List[str] = []
    skills: List[str] = []
    goal: Optional[str] = None


class RecommendRequest(BaseModel):
    profile: Profile


class AskRequest(BaseModel):
    question: str
    profile: Optional[Profile] = None


class FeedbackRequest(BaseModel):
    event: str
    payload: Dict[str, Any]


@app.on_event("startup")
def on_startup() -> None:
    """Initialize services on startup."""
    load_dotenv(override=True)
    
    base_dir = Path(__file__).resolve().parent
    storage_dir = base_dir / "storage"
    roadmap_dir = storage_dir / "Roadmap_dataset"
    mindmap_dir = storage_dir / "Mindmaps"
    
    # Ensure directories exist
    storage_dir.mkdir(parents=True, exist_ok=True)
    roadmap_dir.mkdir(parents=True, exist_ok=True)
    mindmap_dir.mkdir(parents=True, exist_ok=True)
    
    print("\n" + "="*70)
    print("🚀 EduNavigator Starting (Local Mistral Mode)")
    print("="*70)
    print(f"Storage:  {storage_dir}")
    print(f"Roadmaps: {roadmap_dir}")
    print(f"Mindmaps: {mindmap_dir}")
    
    # Initialize services
    try:
        app.state.ingestion = IngestionService(
            roadmap_dir=roadmap_dir,
            mindmap_dir=mindmap_dir,
            storage_dir=storage_dir,
        )
        print("✅ Ingestion service initialized")
    except Exception as e:
        print(f"⚠️  Ingestion service error: {e}")
        app.state.ingestion = None
    
    try:
        app.state.retrieval = RetrievalService(storage_dir=storage_dir)
        print("✅ Retrieval service initialized")
    except Exception as e:
        print(f"⚠️  Retrieval service error: {e}")
        app.state.retrieval = None
    
    try:
        ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        app.state.generation = LocalGenerationService(ollama_url=ollama_url)
        print("✅ Local Mistral generation service initialized")
        print(f"   Ollama endpoint: {ollama_url}")
    except Exception as e:
        print(f"❌ Generation service FAILED: {e}")
        print(f"   Make sure Ollama is running: ollama serve")
        print(f"   And Mistral is pulled: ollama pull mistral")
        raise


@app.get("/health")
def health() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "ok",
        "mode": "local_mistral",
        "services": {
            "ingestion": app.state.ingestion is not None,
            "retrieval": app.state.retrieval is not None,
            "generation": app.state.generation is not None,
        }
    }


@app.post("/api/ingest")
def ingest() -> Dict[str, Any]:
    """Parse PDFs and build FAISS index."""
    if not app.state.ingestion:
        raise HTTPException(status_code=503, detail="Ingestion service not available")
    
    try:
        count = app.state.ingestion.build_index()
        return {
            "ok": True,
            "chunks_indexed": count,
            "message": f"Successfully indexed {count} document chunks"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/recommend")
def recommend(req: RecommendRequest) -> Dict[str, Any]:
    """Generate personalized learning roadmap."""
    if not app.state.retrieval or not app.state.generation:
        raise HTTPException(status_code=503, detail="Required services not available")
    
    try:
        retrieved = app.state.retrieval.retrieve_profile(req.profile.dict())
        plan = app.state.generation.generate_plan(req.profile.dict(), retrieved)
        
        return {
            "ok": True,
            "plan": plan,
            "sources": [d.metadata for d in retrieved["documents"]],
            "profile": req.profile.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ask")
def ask(req: AskRequest) -> Dict[str, Any]:
    """Answer career guidance question with context."""
    if not app.state.retrieval or not app.state.generation:
        raise HTTPException(status_code=503, detail="Required services not available")
    
    try:
        profile_dict = req.profile.dict() if req.profile else {}
        retrieved = app.state.retrieval.retrieve_query(req.question, profile_dict)
        answer = app.state.generation.answer_question(req.question, profile_dict, retrieved)
        
        return {
            "ok": True,
            "answer": answer,
            "sources": [d.metadata for d in retrieved["documents"]],
            "question": req.question
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/mindmap")
def mindmap(source: str = Query(..., description="Source file name")) -> Dict[str, Any]:
    """Get mindmap graph for a document."""
    if not app.state.ingestion:
        raise HTTPException(status_code=503, detail="Ingestion service not available")
    
    try:
        graph = app.state.ingestion.get_mindmap_graph(source)
        return {"ok": True, "graph": graph}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/feedback")
def feedback(req: FeedbackRequest) -> Dict[str, Any]:
    """Log user feedback."""
    try:
        storage_dir = Path(__file__).resolve().parent / "storage"
        path = storage_dir / "feedback.jsonl"
        line = orjson.dumps({"event": req.event, "payload": req.payload}).decode()
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        return {"ok": True, "message": "Feedback logged"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Serve frontend
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("EDUNAVIGATOR_PORT", "8010"))
    host = os.getenv("EDUNAVIGATOR_HOST", "0.0.0.0")
    
    print(f"\n🎯 Starting EduNavigator on {host}:{port}")
    print(f"📍 Open: http://localhost:{port}")
    print(f"📚 API Docs: http://localhost:{port}/docs")
    
    uvicorn.run(app, host=host, port=port)
