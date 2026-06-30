# Docsly — Simple AI Document Reader (RAG)

[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688.svg)](https://fastapi.tiangolo.com/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-green.svg)](https://opensource.org/licenses/Apache-2.0)
[![Status](https://img.shields.io/badge/status-in%20progress-yellow.svg)](#)
[![Stars](https://img.shields.io/github/stars/mariiammaysara/Docsly?style=social)](https://github.com/mariiammaysara/Docsly/stargazers)
[![Postman](https://img.shields.io/badge/Postman-Collection-FF6C37.svg?logo=postman&logoColor=white)](#postman-collection)

**Docsly** is an open-source **RAG (Retrieval-Augmented Generation)** backend. It lets you upload large documents (like PDFs), break them into chunks, turn those chunks into searchable vectors, and ask questions about them using AI models like OpenAI, Cohere, Gemini, or local models via Ollama.

This project is built as a learning + portfolio project, following the **mini-RAG** series to demonstrate a real, production-style AI backend architecture (Factory Pattern, FastAPI lifespan, pgvector, modular providers).

> ⚠️ **Status: Work in Progress.** Vector DB indexing and Celery-based async processing are currently being migrated/finished. File upload and chunking are fully working today.

---

## Table of Contents

- [What It Does](#what-it-does)
- [Architecture Overview](#architecture-overview)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Running the Database (Docker)](#running-the-database-docker)
- [API Endpoints](#api-endpoints)
- [Roadmap](#roadmap)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

---

## What It Does

1. **Upload** — Upload files and organize them into projects.
2. **Chunk** — Split large documents into smaller pieces so the AI can process them.
3. **Embed & Index** *(in progress)* — Convert chunks into vectors and store them in a vector database (pgvector) for fast semantic search.
4. **Ask** — Query your documents in natural language; the AI answers using the relevant chunks (LLM Factory: OpenAI, Cohere, Gemini, Ollama).

---

## Architecture Overview

```
Upload File  →  POST /data/upload/{project_id}
                       │
                       ▼
Chunk File   →  POST /data/process/{project_id}
                       │  (pure chunking, saves chunks to Postgres)
                       ▼
Index Chunks →  POST /nlp/index/push/{project_id}
                       │  (embeds chunks + writes to Vector DB with valid FKs)
                       ▼
Ask Question →  POST /nlp/index/answer/{project_id}  (coming soon)
```

Key design choices:
- **Factory Pattern** for both LLM providers and Vector DB providers — swap OpenAI ↔ Ollama or pgvector ↔ Qdrant without touching business logic.
- **FastAPI `lifespan`** for clean startup/shutdown of DB and AI clients.
- Chunking and embedding are kept as **separate steps** so chunk IDs always exist in Postgres before they're indexed into the vector store (avoids broken foreign keys).

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI |
| Database | PostgreSQL (+ pgvector) |
| Async Tasks | Celery *(in progress)* |
| LLM Providers | OpenAI, Cohere, Google Gemini, Ollama (local) |
| Vector DB | pgvector (Qdrant support planned) |
| Containerization | Docker / docker-compose |

---

## Quick Start

These steps work for **any beginner**, even if you've never run a FastAPI project before.

### 1. Clone the repo

```bash
git clone https://github.com/mariiammaysara/Docsly.git
cd Docsly
```

### 2. Create a virtual environment

**Windows (PowerShell):**
```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3.12 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r src/requirements.txt
```

### 4. Set up environment files

Copy the example env files and fill in your own keys (OpenAI API key, DB credentials, etc.):

```bash
cp src/.env.example src/.env
cp docker/.env.example docker/.env
```

### 5. Start the database (Docker required)

```bash
cd docker
docker-compose up -d
cd ..
```

### 6. Run the server

**Windows (PowerShell):**
```powershell
$env:PYTHONPATH="src"; uvicorn main:app --reload --host 0.0.0.0 --app-dir src
```

**macOS / Linux:**
```bash
PYTHONPATH=src uvicorn main:app --reload --host 0.0.0.0 --app-dir src
```

### 7. Open it in your browser

- App: `http://localhost:8000`
- Interactive API docs (Swagger): `http://localhost:8000/docs`
- Health check: `http://localhost:8000/api/v1/health`

---

## Environment Variables

Docsly uses two `.env` files:

| File | Purpose |
|---|---|
| `src/.env` | App-level settings: API keys (OpenAI/Cohere/Gemini), `GENERATION_MODEL_ID`, `EMBEDDING_MODEL_ID`, `LOG_LEVEL`, DB connection string |
| `docker/.env` | Docker/Postgres credentials used by `docker-compose.yml` |

Never commit real `.env` files — only `.env.example` should be tracked in git. Double-check `.gitignore` covers both.

---

## Running the Database (Docker)

```bash
cd docker
docker-compose up -d
```

This spins up PostgreSQL (with pgvector extension) for storing projects, files, chunks, and vector embeddings.

---

## API Endpoints

| Method | URL | Description |
|---|---|---|
| GET | `/` | Welcome message |
| GET | `/api/v1/health` | Health check |
| POST | `/api/v1/data/upload/{project_id}` | Upload a file to a project |
| POST | `/api/v1/data/process/{project_id}` | Chunk the uploaded file and save chunks to Postgres |
| POST | `/api/v1/nlp/index/push/{project_id}` | Embed chunks and index them into the vector DB *(in progress)* |

Full interactive docs available at `/docs` once the server is running.

---

## Postman Collection

A ready-to-use [Postman](https://www.postman.com/) collection is included so you can test every endpoint without writing requests manually.

1. Open Postman → **Import** → select `postman/Docsly.postman_collection.json`
2. Set the collection variable `base_url` to your running server (default: `http://localhost:8000/api/v1`)
3. Run **Upload** → **Process** → **Index** in order to test the full pipeline on a sample file

> 📌 If you don't see the collection file yet, it's coming soon — export it from your local Postman workspace and add it to `postman/Docsly.postman_collection.json` in the repo.

---

## Roadmap

- [x] File upload & project organization
- [x] Document chunking
- [x] LLM Factory (OpenAI, Cohere, Gemini, Ollama)
- [ ] Vector DB Factory — pgvector migration (in progress)
- [ ] Celery-based async processing for large files (in progress)
- [ ] Question answering endpoint (RAG query)
- [ ] Qdrant provider support
- [ ] Deployment (Railway / Render / HF Spaces) — *in progress*

---

## Project Structure

```
Docsly/
├── docker/              # docker-compose + Docker env config
├── src/
│   ├── controllers/      # ProcessController, NLPController, etc.
│   ├── routes/           # FastAPI route definitions
│   ├── models/           # DB models (Postgres)
│   ├── stores/
│   │   ├── llm/           # LLM Factory (OpenAI, Cohere, Gemini, Ollama)
│   │   └── vectordb/      # Vector DB Factory (pgvector, Qdrant)
│   ├── helpers/          # Config, logging, utilities
│   └── main.py           # FastAPI app entrypoint
├── .gitignore
├── ACKNOWLEDGEMENT.md
├── LICENSE
├── PROGRESS.md
└── README.md
```

---

## Contributing

This is primarily a learning/portfolio project, but issues, suggestions, and pull requests are welcome. If you'd like to contribute:

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Open a Pull Request

---

## License

This project is licensed under the [Apache 2.0 License](./LICENSE).

---

## Acknowledgements

See [ACKNOWLEDGEMENT.md](./ACKNOWLEDGEMENT.md). Built following the **mini-RAG** series to learn how to build real, production-style AI backend systems.
