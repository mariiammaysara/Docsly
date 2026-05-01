# Docsly - Production-Ready RAG Application

**Docsly** is an open-source, full-stack **RAG (Retrieval-Augmented Generation)** application designed for production environments. It provides a robust infrastructure for ingesting, processing, and querying large document collections using state-of-the-art AI.

---

## Roadmap: What's Next?
1. **Vectorization**: Transform processed chunks into high-dimensional **Embeddings**.
2. **Vector DB Integration**: Storing and indexing embeddings for semantic search.
3. **Retrieval Logic**: Implementing similarity search to find the most relevant document pieces.
4. **LLM Synthesis**: Connecting to models (like OpenAI or Local LLMs) to generate precise answers based on retrieved context.

---

## Local Setup

### 1. Manual Installation
```bash
# Create virtual environment
py -3.12 -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r src/requirements.txt

# Run the server
$env:PYTHONPATH="src"; uvicorn main:app --reload --host 0.0.0.0 --app-dir src
```

### 2. Environment Configuration
- **Application (src/.env)**: Copy src/.env.example -> src/.env
- **Infrastructure (docker/.env)**: Copy docker/.env.example -> docker/.env

---

## Docker Usage (Infrastructure)
Run the required MongoDB instance using **Docker Compose**:
```bash
cd docker
docker-compose up -d
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET  | / | Welcome message |
| GET  | /api/v1/health | System health check |
| GET  | /api/v1/data/info | Data configuration info |
| POST | /api/v1/data/upload/{project_id} | **Upload file** and register Asset |
| POST | /api/v1/data/process/{project_id} | **Process Asset** into Chunks |

---

## Environment Variables

### Application Settings (src/.env)
| Variable | Description |
|----------|-------------|
| APP_NAME | **Docsly** |
| APP_VERSION | **v0.1.0** |
| MONGODB_URL | Your MongoDB URI |
| OPEN_AI_KEY | Your OpenAI API Key |

---
*Developed as part of the **mini-RAG** series.*
