import os
import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Any

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader

from .embeddings import SentenceTransformerEmbeddings


SECTION_HEADINGS = [
    "skills", "tools", "projects", "roadmap", "resources", "courses", "path", "roles"
]


def load_text_file(file_path: Path) -> str:
    try:
        return file_path.read_text(encoding='utf-8')
    except Exception:
        return ""


def load_pdf_text(file_path: Path) -> str:
    try:
        reader = PdfReader(str(file_path))
        pages = [p.extract_text() or "" for p in reader.pages]
        return "\n".join(pages)
    except Exception:
        # Some datasets contain plain text with .pdf extension.
        return load_text_file(file_path)


def load_json_as_text(file_path: Path) -> str:
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except Exception:
        return ""

    if isinstance(data, dict):
        # Common mindmap structure: collect readable labels/text
        parts: List[str] = []
        for key in ("title", "name", "topic"):
            v = data.get(key)
            if isinstance(v, str) and v.strip():
                parts.append(v)
        nodes = data.get("nodes") or data.get("links") or []
        if isinstance(nodes, list):
            for node in nodes:
                if isinstance(node, dict):
                    for k in ("label", "name", "text", "id"):
                        v = node.get(k)
                        if isinstance(v, str) and v.strip():
                            parts.append(v)
                            break
        if parts:
            return "\n".join(parts)

    return json.dumps(data, ensure_ascii=False)


def extract_sections(text: str) -> Dict[str, str]:
    # Very simple heuristic: split when we see a section heading on its own line
    sections: Dict[str, str] = {}
    current = "general"
    buf: List[str] = []
    heading_pattern = re.compile(r"^\s*([A-Za-z ]{3,40})\s*$")
    for raw_line in text.splitlines():
        line = raw_line.strip()
        m = heading_pattern.match(line)
        if m:
            candidate = m.group(1).strip().lower()
            if any(h in candidate for h in SECTION_HEADINGS):
                if buf:
                    sections[current] = sections.get(current, "") + "\n" + "\n".join(buf)
                    buf = []
                current = candidate
                continue
        buf.append(raw_line)
    if buf:
        sections[current] = sections.get(current, "") + "\n" + "\n".join(buf)
    return sections


class IngestionService:
    def __init__(self, roadmap_dir: Path, mindmap_dir: Path, storage_dir: Path) -> None:
        self.roadmap_dir = roadmap_dir
        self.mindmap_dir = mindmap_dir
        self.storage_dir = storage_dir
        self.index_dir = storage_dir / "faiss_index"
        self.index_dir.mkdir(parents=True, exist_ok=True)
        print(f"Storage directory: {self.storage_dir}")
        print(f"Roadmap directory: {self.roadmap_dir}")
        print(f"Mindmap directory: {self.mindmap_dir}")
        model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
        self.st_model = SentenceTransformer(model_name)
        self.embedder = SentenceTransformerEmbeddings(self.st_model)
        self._mindmap_cache: Dict[str, Dict[str, Any]] = {}

    def _build_documents(self) -> Tuple[List[Document], Dict[str, Dict[str, Any]]]:
        docs: List[Document] = []
        mindmap_structs: Dict[str, Dict[str, Any]] = {}
        splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
        print("Building document index...")

        def process_file(file_path: Path, kind: str) -> None:
            suffix = file_path.suffix.lower()
            if suffix == ".pdf":
                text = load_pdf_text(file_path)
            elif suffix == ".txt":
                text = load_text_file(file_path)
            elif suffix == ".json":
                text = load_json_as_text(file_path)
            else:
                return

            if not text:
                return
            sections = extract_sections(text)
            # Create a simple mindmap structure from sections
            mindmap_structs[file_path.name] = {
                "title": file_path.stem,
                "nodes": [
                    {"id": sec.lower(), "label": sec.title()} for sec in sections.keys()
                ],
                "edges": [
                    {"source": "general", "target": sec.lower()} for sec in sections.keys() if sec != "general"
                ],
            }
            for section, content in sections.items():
                for chunk in splitter.split_text(content):
                    docs.append(
                        Document(
                            page_content=chunk,
                            metadata={
                                "source": file_path.name,
                                "path": str(file_path),
                                "kind": kind,
                                "section": section,
                                "title": file_path.stem,
                            },
                        )
                    )

        if self.roadmap_dir and self.roadmap_dir.exists():
            for roadmap_file in sorted(self.roadmap_dir.glob("*")):
                process_file(roadmap_file, "roadmap")
        if self.mindmap_dir and self.mindmap_dir.exists():
            for mindmap_file in sorted(self.mindmap_dir.glob("*")):
                process_file(mindmap_file, "mindmap")
        return docs, mindmap_structs

    def build_index(self) -> int:
        docs, mindmap_structs = self._build_documents()
        if not docs:
            print("No documents found to index. Using empty index.")
            return 0
            
        # Build FAISS index
        index = FAISS.from_documents(
            documents=docs,
            embedding=self.embedder,
        )
        index.save_local(str(self.index_dir))
        
        # Save mindmap cache
        self._mindmap_cache = mindmap_structs
        mindmap_cache_path = self.storage_dir / "mindmaps.json"
        mindmap_cache_path.write_text(
            json.dumps(mindmap_structs, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        
        return len(docs)

    def get_mindmap_graph(self, source_filename: str) -> Dict[str, Any]:
        from .mindmap import load_mindmap
        filename = source_filename if source_filename.lower().endswith(".json") else f"{source_filename}.json"
        graph = load_mindmap(filename)
        return {"ok": True, "graph": graph}


