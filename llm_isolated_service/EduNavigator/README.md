## EduNavigator

Personalized career guidance with RAG over your roadmap and mindmap PDFs. Extracts and indexes content from `Roadmap_dataset` and `Mindmaps`, retrieves with MMR + compression, and generates customized roadmaps using Gemini.

### Prerequisites
- Python 3.10+
- FAISS CPU wheels supported on your platform
- Google Gemini API key

### Setup
1. Create and activate a virtual environment.
2. Install dependencies:
```bash
pip install -r backend/requirements.txt
```
3. Copy env template and set paths/keys:
```bash
cp backend/.env.example backend/.env
```
Edit `backend/.env`:
- `GOOGLE_API_KEY` = your key
- `DATA_ROADMAP_DIR` = e.g. `E:\\College\\EDI\\Roadmap_dataset`
- `DATA_MINDMAP_DIR` = e.g. `E:\\College\\EDI\\Mindmaps`

### Run
```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
Open `http://localhost:8000` to access the UI.

### Endpoints
- `POST /api/ingest` — parse PDFs and build FAISS index
- `POST /api/recommend` — body: profile → returns structured roadmap and sources
- `POST /api/ask` — body: `{ question, profile }` → grounded answer
- `GET /api/mindmap` — query: `source` → mindmap JSON for a document

### Notes
- Uses MMR retrieval with contextual compression.
- Index persisted under `backend/storage/faiss_index`.


