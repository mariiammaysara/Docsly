# Docsly — AI Document Q&A Backend (RAG)

**Docsly** is an open-source **RAG (Retrieval-Augmented Generation)** backend. It lets you upload large documents (like PDFs), break them into chunks, turn those chunks into searchable vectors, and ask questions about them using AI models like OpenAI, Cohere, Gemini, or local models via Ollama.

Built on a production-style architecture — Factory Pattern, FastAPI lifespan, pgvector, and modular providers.

---

## Table of Contents

- [What It Does](#what-it-does)
- [Feature Highlights](#feature-highlights)
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
3. **Embed & Index** — Convert chunks into vectors and store them in a vector database (pgvector) for fast semantic search.
4. **Ask** — Query your documents in natural language; the AI answers using the relevant chunks (LLM Factory: OpenAI, Cohere, Gemini, Ollama).

---

## Feature Highlights

### Document Ingestion Pipeline
| Step | Endpoint | Description |
|---|---|---|
| Upload | `POST /data/upload/:project_id` | Accepts PDF, TXT, DOCX up to 10 MB. Saves file to disk and creates asset record in Postgres. |
| Chunk | `POST /data/process/:project_id` | Splits document using LangChain text splitters. Saves each chunk with a foreign key back to its asset. |
| Index | `POST /nlp/index/push/:project_id` | Embeds every chunk via the configured embedding provider and upserts vectors into the vector store. |
| Search | `POST /nlp/index/search/:project_id` | Embeds the user query, runs ANN search, retrieves Top-K chunks, and generates a grounded answer. |

### Multi-Provider AI — Plug & Play

```
Generation Backends     Embedding Backends
─────────────────       ──────────────────
 OpenAI   (GPT-4o)       Cohere   (multilingual-v3)
 Google   (Gemini)       OpenAI   (text-embedding-3)
 Ollama   (local)        Ollama   (local)
```

Swap providers by changing a single env variable — no code changes required.

### Architecture & Engineering

- **Factory Pattern** — LLM and Vector DB providers are fully decoupled from business logic. Add a new provider by implementing one interface.
- **Async-first** — Built on FastAPI + SQLAlchemy (asyncpg) with zero blocking calls in the request path.
- **FastAPI Lifespan** — Clean startup and teardown of database engines, connection pools, and AI clients.
- **Separate chunk/embed steps** — Chunk IDs are persisted in Postgres before embedding, guaranteeing referential integrity in the vector store.
- **pgvector native** — Vectors are stored directly in PostgreSQL alongside relational data — no extra infrastructure needed for the default setup.
- **Modular repositories** — `ProjectRepository`, `AssetRepository`, `ChunkRepository` isolate all DB access behind clean async interfaces.

### Supported File Types

| Format | MIME Type |
|---|---|
| PDF | `application/pdf` |
| Plain Text | `text/plain` |
| Word Document | `application/vnd.openxmlformats-officedocument.wordprocessingml.document` |

---

## Architecture Overview

### System Context

```mermaid
C4Context
    title Docsly — System Context Diagram

    Person(user, "API Consumer", "Developer or Application calling the REST API")

    System(docsly, "Docsly Backend", "FastAPI RAG backend.\nHandles document ingestion, chunking, embedding, and semantic Q&A.")

    System_Ext(openai, "OpenAI API", "GPT models for text generation")
    System_Ext(cohere, "Cohere API", "Embedding models (multilingual)")
    System_Ext(ollama, "Ollama (local)", "Local LLM inference")
    System_Ext(gemini, "Google Gemini", "Gemini generation models")

    SystemDb(postgres, "PostgreSQL + pgvector", "Stores projects, assets, chunks\nand vector embeddings")
    SystemDb(qdrant, "Qdrant (optional)", "Alternative vector store")

    Rel(user, docsly, "HTTP REST", "JSON / multipart form-data")
    Rel(docsly, openai, "HTTPS", "Chat completions")
    Rel(docsly, cohere, "HTTPS", "Embed text")
    Rel(docsly, ollama, "HTTP", "Local inference")
    Rel(docsly, gemini, "HTTPS", "Chat completions")
    Rel(docsly, postgres, "asyncpg / SQLAlchemy", "Async SQL")
    Rel(docsly, qdrant, "REST / gRPC", "Vector ops")
```

---

### RAG Pipeline — Detailed Flow

```mermaid
flowchart TD
    subgraph Client["API Consumer"]
        A([HTTP Request])
    end

    subgraph API["FastAPI Layer — Routes"]
        B[POST /data/upload/:project_id]
        C[POST /data/process/:project_id]
        D[POST /nlp/index/push/:project_id]
        E[POST /nlp/index/search/:project_id]
    end

    subgraph Controllers["Controllers"]
        F[DataController\nupload_file / process_file]
        G[NLPController\npush_index / search_index]
    end

    subgraph Storage["Repositories — PostgreSQL"]
        H[(projects table)]
        I[(assets table)]
        J[(chunks table)]
    end

    subgraph LLM["LLM Factory"]
        K{EmbeddingBackend}
        K -->|COHERE| L[CoHereProvider\nembed-multilingual-v3]
        K -->|OPENAI| M[OpenAIProvider\ntext-embedding-*]
        K -->|OLLAMA| N[Ollama local]
    end

    subgraph GenLLM["Generation Factory"]
        O{GenerationBackend}
        O -->|OPENAI| P[OpenAI GPT]
        O -->|GEMINI| Q[Google Gemini]
        O -->|OLLAMA| R[Ollama local]
    end

    subgraph VectorDB["VectorDB Factory"]
        S{VectorDB Backend}
        S -->|PGVECTOR| T[(pgvector\nvectors in Postgres)]
        S -->|QDRANT| U[(Qdrant cluster)]
    end

    A --> B --> F
    F -->|"① Get-or-Create Project"| H
    F -->|"② Save asset metadata"| I
    F -->|"③ Store file on disk"| I

    A --> C --> F
    F -->|"④ Read file → LangChain splitter"| F
    F -->|"⑤ Save chunks with FK→asset"| J

    A --> D --> G
    G -->|"⑥ Load chunks from Postgres"| J
    G --> K
    K -->|"⑦ Embed each chunk"| G
    G -->|"⑧ Upsert vectors"| S

    A --> E --> G
    G -->|"⑨ Embed query"| K
    G -->|"⑩ ANN search"| S
    S -->|"⑪ Top-K chunks"| G
    G --> O
    O -->|"⑫ RAG prompt + answer"| G
    G -->|"⑬ Return answer"| Client

    style Client fill:#1a1a2e,color:#e0e0e0,stroke:#444
    style API fill:#16213e,color:#e0e0e0,stroke:#444
    style Controllers fill:#0f3460,color:#e0e0e0,stroke:#444
    style Storage fill:#533483,color:#e0e0e0,stroke:#444
    style LLM fill:#e94560,color:#fff,stroke:#444
    style GenLLM fill:#c84b31,color:#fff,stroke:#444
    style VectorDB fill:#2b2d42,color:#e0e0e0,stroke:#444
```

Key design choices:
- **Factory Pattern** for LLM providers and Vector DB — swap OpenAI ↔ Ollama or pgvector ↔ Qdrant without touching business logic.
- **FastAPI `lifespan`** for clean startup/shutdown of DB and AI clients.
- Chunking and embedding are **separate steps** so chunk IDs always exist in Postgres before indexing into the vector store (avoids broken foreign keys).
- **Async-first** — SQLAlchemy + asyncpg, no blocking calls in the request path.

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Framework | FastAPI |
| Database | PostgreSQL (+ pgvector) |
| Async Tasks | Celery |
| LLM Providers | OpenAI, Cohere, Google Gemini, Ollama (local) |
| Vector DB | pgvector (Qdrant support planned) |
| Containerization | Docker / docker-compose |

---

## Quick Start

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
| POST | `/api/v1/nlp/index/push/{project_id}` | Embed chunks and index them into the vector DB |

Full interactive docs available at `/docs` once the server is running.

---

## Postman Collection

A ready-to-use [Postman](https://www.postman.com/) collection is included so you can test every endpoint without writing requests manually.

1. Open Postman → **Import** → select `postman/Docsly.postman_collection.json`
2. Set the collection variable `base_url` to your running server (default: `http://localhost:8000/api/v1`)
3. Run **Upload** → **Process** → **Index** in order to test the full pipeline on a sample file

> 📌 If you don't see the collection file yet, it's coming soon — export it from your local Postman workspace and add it to `postman/Docsly.postman_collection.json` in the repo.

---

## Planned Improvements

- [ ] OCR support for scanned PDFs and images
- [ ] Improved RAG retrieval (reranking, hybrid search)
- [ ] Multi-document cross-referencing in answers
- [ ] Streaming responses for LLM output
- [ ] Celery-based async processing for large files
- [ ] Qdrant vector store provider
- [ ] Conversation history & multi-turn Q&A

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

Issues, suggestions, and pull requests are welcome. If you'd like to contribute:

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes
4. Open a Pull Request

---

## License

This project is licensed under the [Apache 2.0 License](./LICENSE).

---

## Acknowledgements

Built on the foundation of **Eng. Abu Bakr Soliman**'s work. See [ACKNOWLEDGEMENT.md](./ACKNOWLEDGEMENT.md).

---

<p align="center"><em><a href="https://mariammaysara.com">© Mariam Maysara</a></em></p>
