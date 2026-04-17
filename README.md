# Docsly - RAG Application

A RAG (Retrieval-Augmented Generation) API built with FastAPI and OpenAI, using MongoDB for data persistence.

---

## ⚙️ Local Setup

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
We use separate environment files for the application and the infrastructure.
- **Application (`src/.env`)**: Copy `src/.env.example` -> `src/.env`
- **Infrastructure (`docker/.env`)**: Copy `docker/.env.example` -> `docker/.env`

---

## 🐳 Docker Usage (Infrastructure)
You can run the required MongoDB instance using Docker Compose:

```bash
cd docker
docker-compose up -d
```

### 💡 Variable Substitution (Interpolation)
The `docker-compose.yml` uses **Variable Substitution** (Syntax: `${VARIABLE_NAME}`) to pull credentials from `docker/.env`. This keeps secrets separate from configuration and allows for flexible environment management.

---

## 🚀 API Endpoints

Base URL: `http://localhost:8000`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/` | Welcome message |
| `GET`  | `/api/v1/health` | System health check |
| `GET`  | `/api/v1/data/info` | Data configuration info |
| `POST` | `/api/v1/data/upload/{project_id}` | Upload file in chunks |
| `POST` | `/api/v1/data/process/{project_id}` | Process file into chunks |

---

## 🔑 Environment Variables

### Application Settings (`src/.env`)
| Variable | Description |
|----------|-------------|
| `APP_NAME` | Application name |
| `APP_VERSION` | Application version |
| `MONGODB_URL` | Connection string |
| `OPENAI_API_KEY` | OpenAI API key |

### Docker/Mongo Settings (`docker/.env`)
| Variable | Description |
|----------|-------------|
| `MONGO_ROOT_USER` | Admin username |
| `MONGO_ROOT_PASSWORD` | Admin password |
| `MONGO_INITDB_DATABASE` | Initial database name |
