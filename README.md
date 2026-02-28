# ForensIQ — PageIndex RAG for UFDR/CLBE Forensics

A **PageIndex RAG** system that ingests Cellebrite **UFDR** and **CLBE** forensic extraction archives, indexes their contents into token-bounded **pages**, and feeds them into two downstream RAGs:

| RAG Layer | Purpose | Backend |
|-----------|---------|---------|
| **Vector RAG** | Page-based semantic embedding & similarity search | FAISS + Gemini Embeddings |
| **Graph RAG** | Entity extraction & relationship mapping | Neo4j |

---

## Monorepo Structure

```
ForensIQ/
├── backend/          ← Python FastAPI (hosted on Render)
│   ├── forensiq/     ← Core application code
│   ├── config/       ← Settings (pydantic-settings)
│   ├── api/          ← Vercel-legacy shim (unused)
│   ├── data/         ← Demo datasets, FAISS index, uploads
│   ├── tests/        ← Pytest suite
│   ├── tools/        ← CLI tooling / demo scripts
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── render.yaml   ← Render IaC blueprint
│   ├── pyproject.toml
│   └── requirements.txt
│
├── frontend/         ← React + Vite + shadcn/ui (hosted on Vercel)
│   ├── src/
│   ├── vercel.json   ← Vercel config
│   ├── vite.config.js
│   └── package.json
│
└── README.md         ← This file
```

---

## Hosting

### Backend — Render

| Setting | Value |
|---|---|
| **Root Directory** | `backend` |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn forensiq.main:app --host 0.0.0.0 --port $PORT` |

Set these **Environment Variables** on the Render dashboard:

```
GEMINI_API_KEY=...
NEO4J_URI=...
NEO4J_USER=...
NEO4J_PASSWORD=...
MONGODB_URI=...
REDIS_URL=...
JWT_SECRET=...
OPENROUTER_API_KEY=...   (optional)
OPENAI_API_KEY=...       (optional)
```

Alternatively, connect the repo and point Render at `backend/render.yaml` for IaC blueprint deployment.

### Frontend — Vercel

| Setting | Value |
|---|---|
| **Root Directory** | `frontend` |
| **Framework Preset** | Vite |
| **Build Command** | `npm install && npm run build` |
| **Output Directory** | `dist` |

Set this **Environment Variable** on the Vercel dashboard:

```
VITE_API_URL=https://<your-render-service>.onrender.com
```

This tells the frontend SPA where to send API requests.

---

## Local Development

```bash
# 1. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill in your keys
uvicorn forensiq.main:app --reload --port 8000

# 2. Frontend (in another terminal)
cd frontend
npm install
npm run dev                    # starts on :8080, proxies /api → :8000
```

The Vite dev server proxies `/api` and `/health` to `localhost:8000` automatically.

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/ingest/upload` | Upload a `.ufdr`/`.clbe` file for full ingestion |
| `POST` | `/api/v1/ingest/path` | Ingest from a local filesystem path |
| `POST` | `/api/v1/query` | Hybrid semantic + graph RAG search |
| `GET`  | `/api/v1/pages/{extraction_id}` | List all pages for an extraction |
| `GET`  | `/api/v1/stats` | System statistics |
| `GET`  | `/health` | Health check |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ForensIQ Pipeline                        │
│                                                                 │
│  UFDR Parser ──▶ PageIndex Indexer ──▶ Vector RAG (FAISS)      │
│                                   └──▶ Graph RAG  (Neo4j)      │
│                                                                 │
│  FastAPI /api/v1  ─── Render (backend)                         │
│  React SPA        ─── Vercel (frontend)                        │
└─────────────────────────────────────────────────────────────────┘
```
- 💰 Financial trail (Hawala, crypto mixers, wire transfers under ₹10L)
- 🌐 International laundering network (India → Dubai → Mauritius → BVI → China)
- 🔒 Privacy tool usage (Tor, VPN, encrypted messaging, calculator vault)
- 📍 Location timeline linking suspects to warehouses, banks, and meeting points

**Neo4j Browser:** http://localhost:7474 (`neo4j` / `forensiq_secret`)

```cypher
-- Full graph
MATCH (n)-[r]->(m) RETURN n,r,m LIMIT 200

-- Suspect's communication network
MATCH (p:Person)-[r:MESSAGED]-(other:Person)
WHERE p.name CONTAINS 'Vikram'
RETURN p, r, other

-- Organisation network
MATCH (o:Organization)<-[:BELONGS_TO_ORG]-(p:Person)
RETURN o, p
```

---

## Google Drive Integration

ForensIQ can download `.clbe` files directly from Google Drive:

```bash
# Authenticate via OAuth2
curl http://localhost:8000/api/v1/gdrive/auth

# List .clbe files in a Drive folder
curl http://localhost:8000/api/v1/gdrive/list/{folder_id}

# Ingest all .clbe files from a Drive folder
curl -X POST http://localhost:8000/api/v1/gdrive/ingest/{folder_id}
```

---

## Running Tests

```bash
pytest tests/ -v
```

All 10 tests pass.

---

## License

MIT
