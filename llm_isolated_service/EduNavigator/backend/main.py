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
from rag.generation import GenerationService


def json_dumps(v: Any, *, default: Any = None) -> str:
    return orjson.dumps(v, default=default).decode()


app = FastAPI(title="EduNavigator")

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
    load_dotenv(override=True)
    base_dir = Path(__file__).resolve().parent
    storage_dir = base_dir / "storage"
    roadmap_dir = storage_dir / "Roadmap_dataset"
    mindmap_dir = storage_dir / "Mindmaps"
    
    # Ensure directories exist
    storage_dir.mkdir(parents=True, exist_ok=True)
    roadmap_dir.mkdir(parents=True, exist_ok=True)
    mindmap_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Using directories:")
    print(f"  Storage: {storage_dir}")
    print(f"  Roadmap: {roadmap_dir}")
    print(f"  Mindmap: {mindmap_dir}")
    
    # Services
    app.state.ingestion = IngestionService(
        roadmap_dir=roadmap_dir,
        mindmap_dir=mindmap_dir,
        storage_dir=storage_dir,
    )
    app.state.retrieval = RetrievalService(storage_dir=storage_dir)
    app.state.generation = GenerationService()


@app.post("/api/ingest")
def ingest() -> Dict[str, Any]:
    try:
        count = app.state.ingestion.build_index()
        return {"ok": True, "chunks_indexed": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/recommend")
def recommend(req: RecommendRequest) -> Dict[str, Any]:
    try:
        retrieved = app.state.retrieval.retrieve_profile(req.profile.dict())
        plan = app.state.generation.generate_plan(req.profile.dict(), retrieved)
        return {"ok": True, "plan": plan, "sources": [d.metadata for d in retrieved["documents"]]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/ask")
def ask(req: AskRequest) -> Dict[str, Any]:
    try:
        profile_dict = req.profile.dict() if req.profile else {}
        retrieved = app.state.retrieval.retrieve_query(req.question, profile_dict)
        answer = app.state.generation.answer_question(req.question, profile_dict, retrieved)
        return {"ok": True, "answer": answer, "sources": [d.metadata for d in retrieved["documents"]]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/mindmap")
def mindmap(source: str = Query(..., description="Source file name from metadata")) -> Dict[str, Any]:
    try:
        graph = app.state.ingestion.get_mindmap_graph(source)
        return {"ok": True, "graph": graph}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/feedback")
def feedback(req: FeedbackRequest) -> Dict[str, Any]:
    try:
        path = Path(os.getenv("STORAGE_DIR", "backend/storage")) / "feedback.jsonl"
        line = orjson.dumps({"event": req.event, "payload": req.payload}).decode()
        with open(path, "a", encoding="utf-8") as f:
            f.write(line + "\n")
        return {"ok": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Serve frontend
frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


