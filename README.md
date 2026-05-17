<p align="center">
  <img width="100%" alt="Production RAG Banner" src="docs/banner.png"/>
</p>

<p align="center">
  <a href="http://production-rag-frontend.s3-website.ap-south-1.amazonaws.com"><img src="https://img.shields.io/badge/Live_Demo-Visit_App-7c3aed?style=flat-square" alt="Live Demo" /></a>
  <a href="https://github.com/uditnegi16/production-rag"><img src="https://img.shields.io/badge/GitHub-Production_RAG-181717?style=flat-square&logo=github" alt="GitHub" /></a>
  <a href="#"><img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="MIT License" /></a>
  <a href="#"><img src="https://img.shields.io/badge/Python-3.12-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python 3.12" /></a>
  <a href="#"><img src="https://img.shields.io/badge/AWS-Deployed-FF9900?style=flat-square&logo=amazonaws&logoColor=white" alt="AWS" /></a>
  <a href="#"><img src="https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React 18" /></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/RAG-Production_Grade-7c3aed?style=flat-square" alt="RAG" />
  <img src="https://img.shields.io/badge/Vector_DB-ChromaDB-orange?style=flat-square" alt="ChromaDB" />
  <img src="https://img.shields.io/badge/Reranker-CrossEncoder-F7931E?style=flat-square" alt="CrossEncoder" />
  <img src="https://img.shields.io/badge/Cache-Upstash_Redis-red?style=flat-square" alt="Redis" />
  <img src="https://img.shields.io/badge/Tracing-LangSmith-1C3C3C?style=flat-square" alt="LangSmith" />
  <img src="https://img.shields.io/badge/CI-GitHub_Actions-2088FF?style=flat-square&logo=githubactions&logoColor=white" alt="GitHub Actions" />
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Groq-llama--3.1--8b-red?style=flat-square" alt="Groq" />
  <img src="https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat-square&logo=fastapi" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Docker-Containerized-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker" />
</p>

---

## Overview

Production RAG is a document intelligence system built across all 12 phases of a complete SDLC. Upload any PDF — an annual report, a policy document, a textbook chapter — ask a question in plain English, and get back a precise answer with the exact paragraph it came from, a confidence score, and an honest fallback if the system does not know.

The system is not a demo. It has a full observability layer, a hallucination checker, a Redis cache, prompt injection defense, an evaluation benchmark, a CI pipeline, and is deployed on AWS ECS Fargate with a frontend on S3.

> *"What is zero shot prompting?"*
>
> → Grounded answer · Cited source paragraph · Page number · Confidence score · Latency — in under 2 seconds.

---

## Live Demo

| Service | URL |
|---------|-----|
| Frontend | http://production-rag-frontend.s3-website.ap-south-1.amazonaws.com |
| Backend Health | http://13.204.157.210:8000/api/v1/health |
| API Docs | http://13.204.157.210:8000/docs |

> **Note:** ECS container is stopped when not in use to avoid billing. Start it before demoing — see [Deployment](#deployment).

---

## System Architecture

```mermaid
flowchart TD
    A["📄 PDF Upload"] --> B["Ingestion Pipeline\nParser · Chunker · Embedder"]
    B --> C["ChromaDB\nVector Store"]
    D["❓ User Query"] --> E["Sanitizer\nPrompt Injection Defense"]
    E --> F["Redis Cache\nUpstash — 1hr TTL"]
    F -->|Cache Miss| G["Retrieval Layer\nEmbed Query · Vector Search"]
    G --> C
    C --> H["CrossEncoder Reranker\nms-marco-MiniLM-L-6-v2"]
    H --> I["Confidence Scorer\nThreshold Gate"]
    I -->|Confident| J["Groq LLM\nllama-3.1-8b-instant"]
    I -->|Not Confident| K["Fallback Response"]
    J --> L["Answer + Citation\n+ Source Paragraph + Page"]
    L --> M["Query Logger\nSQLite / PostgreSQL"]
    L --> N["LangSmith Tracing\nLatency · Tokens · Chain"]
    F -->|Cache Hit| L

    style A fill:#7c3aed,color:#fff,stroke:#5b21b6
    style D fill:#7c3aed,color:#fff,stroke:#5b21b6
    style J fill:#1e40af,color:#fff,stroke:#1e3a8a
    style H fill:#065f46,color:#fff,stroke:#064e3b
    style I fill:#0369a1,color:#fff,stroke:#075985
    style F fill:#dc2626,color:#fff,stroke:#b91c1c
    style N fill:#1C3C3C,color:#fff,stroke:#0f2020
```

---

## RAG Pipeline

```mermaid
flowchart LR
    A["PDF"] --> B["pypdf Parser"]
    B --> C["512-token Chunker\n50-token overlap"]
    C --> D["all-MiniLM-L6-v2\nEmbedder"]
    D --> E["ChromaDB\nCosine Similarity"]
    F["Query"] --> G["Embed Query"]
    G --> H["Top-K Search\nk=10"]
    H --> E
    E --> I["CrossEncoder\nReranker top-n=5"]
    I --> J["Confidence Score\n0.7×score + 0.3×count"]
    J --> K["Groq LLM\nStrict grounded prompt"]
    K --> L["Answer + chunk_id\n+ page_number"]
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, plain HTML/JS, served via S3 static hosting |
| Backend | FastAPI, Python 3.12, Uvicorn |
| Embedding Model | sentence-transformers all-MiniLM-L6-v2 |
| Reranker | CrossEncoder ms-marco-MiniLM-L-6-v2 |
| Vector Store | ChromaDB (local) → Pinecone (production roadmap) |
| LLM | Groq llama-3.1-8b-instant |
| Cache | Upstash Redis (TTL 1hr, keyed by query + doc_id) |
| Query Logging | SQLite (dev) / PostgreSQL via SQLAlchemy (prod) |
| Observability | LangSmith distributed tracing |
| Security | Prompt injection sanitizer, CORS locked per env |
| Testing | Pytest — 46 tests (unit + integration + eval benchmark) |
| CI/CD | GitHub Actions — runs on every push to main |
| Containerization | Docker, docker-compose |
| Container Registry | AWS ECR |
| Deployment | AWS ECS Fargate |
| Frontend Hosting | AWS S3 static website |
| Drift Detection | Weekly hash-based document drift checker |

---

## Features

- **Grounded answers only** — strict prompt forbids answering outside retrieved chunks
- **Source citation** — every answer includes the exact paragraph, chunk ID, and page number
- **Confidence scoring** — derived from reranker scores, fallback fires below threshold
- **Honest fallback** — says it does not know rather than hallucinating
- **Prompt injection defense** — sanitizes queries and chunks before LLM sees them
- **Redis cache** — repeated identical queries bypass vector search and LLM entirely
- **LangSmith tracing** — every query traced with latency per step, inputs, outputs
- **Evaluation benchmark** — 10 Q&A pairs, 100% pass rate, zero hallucinations baseline
- **Drift detection** — detects if ingested documents have been modified since ingestion
- **Full observability** — p50/p95 latency, fallback rate, hallucination flag, feedback score
- **Feedback loop** — thumbs up/down on every response, logged for weekly review
- **Docker containerized** — one command local dev, same image in production
- **CI pipeline** — GitHub Actions runs 46 tests on every push, blocks merge on failure

---

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/api/v1/upload` | Upload and ingest a PDF |
| `POST` | `/api/v1/query` | Ask a question, get cited answer |
| `POST` | `/api/v1/feedback` | Submit thumbs up/down on a response |
| `GET` | `/api/v1/dashboard` | Monitoring data — stats, logs, hallucinations |
| `GET` | `/api/v1/drift` | Check if ingested documents have changed |
| `GET` | `/api/v1/health` | Health check |

---

## Evaluation Results

Baseline benchmark locked at 100% pass rate, zero hallucinations, zero fallbacks across 10 hand-curated Q&A pairs from real documents. Any future change to chunking strategy, reranker threshold, or prompt must match or beat this baseline to merge.

| Metric | Result |
|--------|--------|
| Pass rate | 100% |
| Hallucination rate | 0% |
| Fallback rate | 0% |
| Avg overlap score | 0.68 |
| Avg keyword coverage | 0.75 |

---

## AWS Infrastructure

| Service | Purpose |
|---------|---------|
| AWS ECS Fargate | Backend container — serverless, no EC2 to manage |
| AWS ECR | Private Docker image registry |
| AWS S3 | Frontend static website hosting |
| AWS CloudWatch | Container logs via awslogs driver |
| Upstash Redis | Managed Redis cache — ap-south-1, free tier |

---

## Local Development

### Prerequisites

- Python 3.12
- Docker Desktop
- Groq API key — free at [console.groq.com](https://console.groq.com)
- Upstash Redis account — free at [console.upstash.com](https://console.upstash.com)
- LangSmith account — free at [smith.langchain.com](https://smith.langchain.com)

### Clone and setup

```bash
git clone https://github.com/uditnegi16/production-rag.git
cd production-rag
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Create `.env`

```env
GROQ_API_KEY=your_groq_api_key
LLM_PROVIDER=groq
CHROMA_PERSIST_PATH=./data/processed/chroma
POSTGRES_URL=sqlite:///./data/processed/rag_logs.db
REDIS_URL=rediss://default:your_token@your-upstash-host:6379
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_key
LANGSMITH_PROJECT=production-rag
ALLOWED_ORIGINS=http://localhost:3000
ENVIRONMENT=development
```

### Run with Docker (recommended)

```bash
docker-compose up
```

Backend at `http://localhost:8000` · Frontend at `http://localhost:3000`

### Run manually (3 terminals)

**Terminal 1 — Backend:**
```powershell
uvicorn app.api.main:app --reload --port 8000
```

**Terminal 2 — Frontend:**
```powershell
cd frontend
python -m http.server 3000
```

**Terminal 3 — Tests:**
```powershell
pytest tests/unit/ -v
pytest tests/integration/ -v
python tests/evaluation/run_eval.py
```

---

## Deployment

### Start service (run in order, wait 2 mins after step 1)

```powershell
# 1. Start ECS container
aws ecs update-service --cluster production-rag-cluster --service production-rag-service --desired-count 1 --region ap-south-1

# 2. Get new public IP and update frontend
$task = aws ecs list-tasks --cluster production-rag-cluster --query "taskArns[0]" --output text --region ap-south-1
$eni = aws ecs describe-tasks --cluster production-rag-cluster --tasks $task --query "tasks[0].attachments[0].details[1].value" --output text --region ap-south-1
$ip = aws ec2 describe-network-interfaces --network-interface-ids $eni --query "NetworkInterfaces[0].Association.PublicIp" --output text --region ap-south-1
echo "New IP: $ip"

# 3. Update frontend API URL and upload to S3
(Get-Content frontend/index.html) -replace 'const API = "http://[^"]*"', "const API = `"http://$ip`:8000/api/v1`"" | Set-Content frontend/index.html
aws s3 cp frontend/index.html s3://production-rag-frontend/index.html --content-type "text/html"

echo "Live at: http://production-rag-frontend.s3-website.ap-south-1.amazonaws.com"
```

### Stop service (avoid billing when not in use)

```powershell
aws ecs update-service --cluster production-rag-cluster --service production-rag-service --desired-count 0 --region ap-south-1
```

### Deploy new code changes

```powershell
docker build -t production-rag .
docker tag production-rag:latest 381492009163.dkr.ecr.ap-south-1.amazonaws.com/production-rag:latest
aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin 381492009163.dkr.ecr.ap-south-1.amazonaws.com
docker push 381492009163.dkr.ecr.ap-south-1.amazonaws.com/production-rag:latest
aws ecs update-service --cluster production-rag-cluster --service production-rag-service --force-new-deployment --region ap-south-1
```

---

## Known Limitations and Production Roadmap

**PDF Storage:** Uploaded PDFs are stored in the ECS container's local filesystem. In production, PDFs would be stored in S3 and ChromaDB would be replaced with Pinecone for persistent vector storage, ensuring data survives container restarts.

**Redis Cache:** Currently using Upstash Redis free tier. In production, AWS ElastiCache in the same VPC would reduce latency to under 10ms.

**Authentication:** No user authentication in v1. Multi-user support with session scoping is planned for v2.

**Load Balancer:** ECS public IP changes on every container restart. An Application Load Balancer would provide a fixed DNS name and enable zero-downtime blue/green deployments.

---

## Project Structure

```
production-rag/
├── app/
│   ├── api/                  ← FastAPI routes and main app
│   ├── ingestion/            ← Parser, chunker, embedder, vector store, pipeline
│   ├── retrieval/            ← Search and CrossEncoder reranker
│   ├── generation/           ← Prompt builder, confidence scorer, LLM generator
│   ├── monitoring/           ← Query logger, dashboard data
│   ├── security/             ← Prompt injection sanitizer
│   ├── cache/                ← Redis cache layer
│   └── maintenance/          ← Drift detector
├── tests/
│   ├── unit/                 ← 9 test files, 46 tests
│   ├── integration/          ← API and ingestion pipeline tests
│   └── evaluation/           ← Eval dataset, hallucination checker, runner
├── frontend/                 ← Single-file React app
├── aws/                      ← Task definition, IAM trust policy
├── prompts/                  ← Versioned RAG prompt
├── .github/workflows/        ← GitHub Actions CI pipeline
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## CI Pipeline

GitHub Actions runs on every push to main:

1. Install Python 3.12 and all dependencies
2. Run 46 unit and integration tests with pytest
3. Assert evaluation benchmark pass rate is above 90%
4. Block merge if any step fails

---

## License

MIT — built for portfolio demonstration purposes.

---

<p align="center">
  Built across 12 SDLC phases with ☕ and debugging in India 🇮🇳
</p>