# ForensIQ — PageIndex RAG for UFDR/CLBE Forensics

A **PageIndex RAG** system that ingests Cellebrite **UFDR** and **CLBE** forensic extraction archives, indexes their contents into token-bounded **pages**, and feeds them into two downstream RAGs:

| RAG Layer | Purpose | Backend |
|-----------|---------|---------|
| **Vector RAG** | Page-based semantic embedding & similarity search | FAISS + OpenAI `text-embedding-3-small` |
| **Graph RAG** | Entity extraction & relationship mapping | Neo4j |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        ForensIQ Pipeline                        │
│                                                                  │
│  ┌──────────┐    ┌────────────┐    ┌───────────┐   ┌──────────┐│
│  │  UFDR    │───▶│  PageIndex │───▶│ Vector RAG│   │ Graph RAG││
│  │  Parser  │    │  Indexer   │    │  (FAISS)  │   │  (Neo4j) ││
│  └──────────┘    └────────────┘    └───────────┘   └──────────┘│
│       │                │                 │               │      │
│  .ufdr / dir     Page objects      Embeddings      Entities +  │
│                  (token-bounded)   + similarity     relationships│
│                                    search                       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────────┐│
│  │                    FastAPI  /api/v1                          ││
│  │  POST /ingest/upload   POST /query   GET /pages/{id}        ││
│  └──────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
ForensIQ/
├── config/
│   └── settings.py              # Centralised config (pydantic-settings)
├── forensiq/
│   ├── ufdr/
│   │   ├── models.py            # Pydantic models for forensic artefacts
│   │   └── parser.py            # UFDR archive extractor + XML parser
│   ├── pageindex/
│   │   ├── page.py              # Page model (atomic unit of content)
│   │   ├── indexer.py           # Converts extraction → pages (token-bounded)
│   │   └── store.py             # JSONL-based persistent page store
│   ├── vectorrag/
│   │   ├── embedder.py          # OpenAI embedding client
│   │   ├── faiss_store.py       # FAISS index management
│   │   └── retriever.py         # Semantic search over pages
│   ├── graphrag/
│   │   ├── schema.py            # Neo4j node labels & relationship types
│   │   ├── neo4j_client.py      # Neo4j driver wrapper
│   │   └── extractor.py         # Entity extraction + graph population
│   ├── orchestrator/
│   │   └── pipeline.py          # End-to-end ingest & query orchestrator
│   ├── api/
│   │   └── routes.py            # FastAPI endpoints
│   └── main.py                  # FastAPI app entry-point
├── tests/
│   ├── test_indexer.py
│   └── test_extractor.py
├── docker-compose.yml           # Neo4j + ForensIQ app
├── Dockerfile
├── pyproject.toml
├── .env.example
└── README.md
```

## Quick Start

### 1. Clone & configure

```bash
cp .env.example .env
# Edit .env — set OPENAI_API_KEY and optionally NEO4J_PASSWORD
```

### 2. Install (local dev)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

### 3. Start Neo4j

```bash
sudo docker run -d --name forensiq-neo4j \
  -p 7474:7474 -p 7687:7687 \
  -e NEO4J_AUTH=neo4j/forensiq_secret \
  neo4j:5-community
```

### 4. Generate & Run Demo

```bash
# Generate synthetic forensic dataset (Operation Digital Trail)
python tools/generate_demo_dataset.py

# Run the full pipeline demo — parses, indexes, populates Neo4j, runs queries
python tools/demo.py
```

Output: **133 nodes**, **468 relationships** from 2 device extractions (29 pages).

### 5. Run the API server

```bash
uvicorn forensiq.main:app --reload
```

The API docs are at **http://localhost:8000/docs**.

### 5. Or run everything via Docker Compose

```bash
docker compose up --build
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/ingest/upload` | Upload a `.ufdr` file for full ingestion |
| `POST` | `/api/v1/ingest/path` | Ingest a UFDR source from a local filesystem path |
| `POST` | `/api/v1/query` | Hybrid semantic + graph search |
| `GET`  | `/api/v1/pages/{extraction_id}` | List all pages for an extraction |
| `GET`  | `/api/v1/stats` | System statistics (extractions, vectors, graph) |
| `GET`  | `/health` | Health check |

### Example: Ingest

```bash
curl -X POST http://localhost:8000/api/v1/ingest/upload \
  -F "file=@/path/to/case.ufdr"
```

### Example: Query

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Who did the suspect message on WhatsApp about the meeting?", "k": 5}'
```

---

## How It Works

### PageIndex (the core)

1. **UFDR Parser** reads the Cellebrite XML report inside the archive and extracts structured artefacts (contacts, calls, messages, locations, etc.).
2. **Indexer** serialises each artefact category into human-readable text and groups them into **Pages** — token-bounded chunks (default 512 tokens) that fit a single embedding call.
3. Pages are persisted as JSONL files.

### Vector RAG

- Each page is embedded via OpenAI `text-embedding-3-small`.
- Embeddings are stored in a **FAISS** inner-product index (cosine similarity via L2-normalised vectors).
- At query time the user's question is embedded and the top-K nearest pages are returned.

### Graph RAG

- **Entity extractor** runs regex + heuristic rules over each page to pull out **Person**, **PhoneNumber**, **EmailAddress**, **App**, **Location**, **URL**, **Organization**, **Account** entities.
- Entities and relationships (CALLED, MESSAGED, HAS_PHONE, BELONGS_TO_ORG, …) are merged into **Neo4j**.
- At query time, entities from the top vector hits are expanded through the graph to find related people, devices, and communication patterns.

---

## Demo: Operation Digital Trail

A synthetic financial fraud investigation with 2 device extractions:

| Character | Role | Device |
|-----------|------|--------|
| Vikram Mehta | Primary suspect, fake import/export firm | OnePlus 12 (121 artifacts) |
| Priya Sharma | Accomplice, Hawala broker | iPhone 15 Pro (38 artifacts) |
| Rajan Patel | Crypto launderer | — |
| Deepak Joshi | Bank insider | — |
| Ananya Singh | Lawyer, shell company setup | — |
| Farid Hassan | Dubai trade partner | — |
| Li Wei | Chinese supplier, falsified docs | — |

**What the graph reveals:**
- 🔗 Cross-device entity correlation (shared phone numbers/emails merge automatically)
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
