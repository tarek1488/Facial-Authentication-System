# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Start database services
```bash
cd docker
docker-compose up -d
```

### Install dependencies
```bash
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r src/requirements.txt
```

### Run the FastAPI backend
```bash
cd src
uvicorn main:app --reload --port 5000
```
API docs available at http://localhost:5000/docs

### Run the Tkinter desktop client
```bash
cd src
python ui/main.py
```

## Architecture

This is a **facial authentication system** with a FastAPI backend and a Tkinter desktop UI.

### Data flow
1. **Registration**: UI captures webcam frame → POST `/api/v1/client/register_client` (saves image + MongoDB record) → POST `/api/v1/client/proccess_client_image/{client_id}` (generates 512-dim embedding via DeepFace/Facenet512 → stores in Qdrant vector DB)
2. **Authentication**: UI auto-captures frame every 5s → POST `/api/v1/authenticate/authenticate` → embeds frame → cosine similarity search in Qdrant → if score ≥ 0.40, writes `Status=1` to Firebase Realtime DB

### Backend (`src/`)

**App startup** (`main.py`): FastAPI lifespan initializes all connections — MongoDB (via Motor async client), Qdrant (via `VectorDBFactory`), DeepFace model (via `ModelProviderFactory`), Firebase — and attaches them to `app` state.

**Layers:**
- `routes/` — FastAPI routers: `base.py` (health), `user.py` (register + process), `authenticate.py` (auth)
- `controllers/` — Business logic. `ImageController` handles file I/O and validation. `EmbeddingController` orchestrates embedding generation and vector DB queries. `ClientController` manages client file paths.
- `models/` — Pydantic models: `db_schemes/client.py` (MongoDB schema), `ClientDataModel.py` (async MongoDB queries), `enums/ResponseSignal.py` (response string constants)
- `stores/` — External service clients:
  - `deeplearning/` — Factory + interface pattern; `providers/deepface.py` wraps DeepFace
  - `vectordb/` — Factory + interface pattern; `providers/qdrant.py` wraps qdrant-client
  - `firebase/Firebase.py` — Firebase Admin SDK wrapper; writes auth status to `/Status` in Realtime DB
- `helpers/config.py` — `pydantic-settings` `Settings` class reads from `src/.env`

### Frontend (`src/ui/main.py`)
Single-file Tkinter app. Camera capture runs in a background thread sharing `last_frame` via a lock. API calls run in daemon threads and push results to a `queue.Queue` consumed by the Tk main loop via `root.after`.

### Infrastructure (`docker/`)
Docker Compose runs:
- **MongoDB** on port `27007` (mapped from container `27017`)
- **Qdrant** on ports `6333` (HTTP) and `6334` (gRPC)

### Configuration (`src/.env`)
Key variables:
- `DEEPFACE_HOME` — absolute path where DeepFace caches models (must exist)
- `CREDENTIALS_PATH` — absolute path to Firebase service account JSON
- `EMBEDDING_MODEL_SIZE` — must match the chosen model (512 for Facenet512)
- `DETECTION_BACKEND` — face detector used by DeepFace (e.g. `ssd`)
