# Facial Authentication System

This project implements a comprehensive facial registration and authentication system leveraging modern deep learning and computer vision techniques. It provides a FastAPI back-end to handle facial embeddings and database interactions, and a Tkinter-based desktop interface for real-time camera capture and authentication.

## Features

- **Real-Time Facial Registration**: Users can register by providing their name and an ID. The UI visually captures their face and sends it for processing.
- **Continuous Facial Authentication**: The front-end automatically captures and authenticates users via their camera feed in a background thread every 5 seconds.
- **Advanced Deep Learning Pipeline**: Utilizes **DeepFace** with Keras/TensorFlow for high-quality facial representations (`Facenet512` by default, 512-dim embeddings) and SSD for face detection.
- **Vector Search Engine**: Face embeddings are indexed and compared using **Qdrant** with cosine similarity; a match threshold of `0.40` gates authentication.
- **Data Stores**: **MongoDB** (via Motor async client) persists client records; **Qdrant** stores embeddings; **Firebase Realtime DB** receives the live authentication status (`/Status` = `1` on success, `0` on failure).
- **Full Containerization**: The FastAPI backend, MongoDB, and Qdrant all run via Docker Compose — a single `docker-compose up` brings up the entire stack.
- **Factory/Provider Architecture**: Embedding model and vector DB are pluggable via factory + interface patterns (`stores/deeplearning`, `stores/vectordb`), so providers can be swapped without touching the controllers.

## Technology Stack

- **Backend Framework**: FastAPI, Uvicorn
- **Computer Vision & ML**: DeepFace, TensorFlow-Keras, OpenCV
- **Databases**: Qdrant (Vector DB), MongoDB (NoSQL), Firebase
- **Frontend / Client UI**: Python Tkinter with PIL and Async API requests
- **Infra/Deployment**: Docker, Docker Compose

## Prerequisites

Before running this project, ensure you have the following installed:

- Python 3.8+
- Docker and Docker Compose (to run the database services)
- A webcam (for the Tkinter UI to capture face frames)

## Project Structure

```
.
├── Dockerfile                   # Image for the FastAPI backend (python:3.11-slim + uv)
├── docker/
│   ├── docker-compose.yml       # App + MongoDB + Qdrant services
│   └── .env                     # Docker environment variables (Mongo credentials)
├── src/
│   ├── main.py                  # FastAPI entry point; lifespan wires up all clients
│   ├── requirements.txt         # Python dependencies
│   ├── .env                     # Backend configuration variables
│   ├── assets/                  # DeepFace model cache (DEEPFACE_HOME)
│   ├── helpers/
│   │   └── config.py            # pydantic-settings Settings loader
│   ├── controllers/             # ImageController, EmbeddingController, ClientController
│   ├── models/
│   │   ├── db_schemes/          # Pydantic MongoDB schemas (Client)
│   │   ├── ClientDataModel.py   # Async Motor data access layer
│   │   └── enums/               # ResponseSignal string constants
│   ├── routes/                  # base.py (health), user.py (register), authenticate.py
│   ├── stores/
│   │   ├── deeplearning/        # Factory + providers/deepface.py
│   │   ├── vectordb/            # Factory + providers/qdrant.py
│   │   └── firebase/Firebase.py # Firebase Admin SDK wrapper
│   └── ui/
│       └── main.py              # Tkinter desktop client
└── README.md
```

## Architecture & Data Flow

**Registration**
1. UI captures a webcam frame and POSTs it to `/api/v1/client/register_client` — the backend saves the image and writes a client record to MongoDB.
2. UI then calls `/api/v1/client/proccess_client_image/{client_id}` — DeepFace (`Facenet512`) generates a 512-dim embedding, which is upserted into Qdrant.

**Authentication**
1. The Tkinter client auto-captures a frame every 5 seconds and POSTs it to `/api/v1/authenticate/authenticate`.
2. The backend embeds the frame, runs a cosine similarity search in Qdrant, and if the top score ≥ `0.40` it considers the client authenticated.
3. On success, the backend writes `Status = 1` to Firebase Realtime DB (`0` on failure). The top match's `client_id` and `client_name` are returned in the JSON response.

The FastAPI `lifespan` in `src/main.py` eagerly initializes every external client (MongoDB, Qdrant, DeepFace model, Firebase) at startup and attaches them to `app.state`, so request handlers can pull ready-to-use clients via `request.app.*`.

## Setup & Installation

You have two options: run the **whole stack in Docker** (recommended), or run the backend locally and use Docker only for MongoDB + Qdrant.

### 1. Clone the Repository

```bash
git clone https://github.com/tarek1488/Facial-Authentication-System.git
cd Facial-Authentication-System
```

### Option A — Run everything in Docker (recommended)

The `docker/docker-compose.yml` builds the backend image from the root `Dockerfile` and starts `face_auth_app`, `mongodb`, and `qdrant` on a shared `backend` network.

```bash
cd docker
docker-compose up -d --build
```

Requirements before running:
- Populate `docker/.env` with `MONGO_INITDB_ROOT_USERNAME` / `MONGO_INITDB_ROOT_PASSWORD`.
- Place your Firebase service account JSON at `src/stores/firebase/credentials/firebase_credentials.json` — the compose file mounts that directory read-only into `/app/credentials`.
- The backend expects DeepFace models to be cached under `src/assets/models` (mounted into the container at `/app/assets`). On first run, DeepFace will download them if absent.

The API will be available at http://localhost:5000/docs. MongoDB is exposed on `27007` and Qdrant on `6333` / `6334`.

The Tkinter desktop client is **not** containerized (it needs host webcam + display access); follow Option B's venv steps to run it against the dockerized backend.

### Option B — Local backend, Dockerized databases

Start only the DB services (you can run compose with the `mongodb` and `qdrant` services, or comment out the `app` service temporarily):

```bash
cd docker
docker-compose up -d mongodb qdrant
cd ..
```

### 3. Create a Virtual Environment and Install Dependencies

```bash
python -m venv .venv
source .venv/bin/activate  # On Unix/macOS
# or: .venv\Scripts\activate # On Windows

# Install the necessary python packages
pip install -r src/requirements.txt
```

### 4. Configuration Requirements

A `.env` file should be present in the `src/` directory. Create or update it with settings similar to the following:

```env
APP_NAME="Facial Authentication"
APP_VERSION="0.1"

# MongoDB Config
MONGO_DB_URL="mongodb://admin:admin@localhost:27007"
MONGO_DB_DATABASE="FacialAuthentication"

# Deep Learning Model Config
EMBEDDING_MODEL_PROVIDER="DeepFace"
EMBEDDING_MODEL_NAME="Facenet512"
EMBEDDING_MODEL_SIZE=512
DETECTION_BACKEND="ssd"
# Set this to a valid path on your machine where models will be cached
DEEPFACE_HOME="D:/path/to/project/src/assets/models"

# VectorDB Config
VECTORDB_PROVIDER="QDRANT"
QDRANT_URL="http://localhost:6333"
COLLECTION_NAME="GymClients"

# Firebase (If utilized, set correct credentials path)
CREDENTIALS_PATH="D:/path/to/credentials/firebase_credentials.json"
DATABASE_URL="https://your-firebase-db.firebaseio.com/"
```

*Ensure that `DEEPFACE_HOME` and `CREDENTIALS_PATH` point to valid absolute paths in your local system to avoid path-resolution issues.*

### 5. Running the Application

**Start the FastAPI Backend**
Start the backend server on port 5000 (which is expected by the client UI).
```bash
cd src
uvicorn main:app --reload --port 5000
```
*You can access the API documentation at http://localhost:5000/docs.*

**Start the Tkinter UI Client**
In a new terminal window (with the virtual environment activated), start the desktop client:
```bash
cd src
python ui/main.py
```

## Usage Instructions

1. **Wait for UI to Boot**: Complete the setup steps above and ensure both backend and UI are running. The UI window should display your webcam feed.
2. **Register a User**:
   - Provide a "Client Name" and a numeric "Client ID" in the appropriate fields.
   - Look straight into your webcam and click on the **Register** button.
   - A success message will appear in the API Response panel once your facial embeddings are processed and saved in Qdrant and MongoDB.
3. **Face Authentication**:
   - As long as the interface is running, the app automatically captures a frame and pings the authentication endpoint every 5 seconds.
   - Information about authentication success or failure will stream seamlessly into the response panel.
