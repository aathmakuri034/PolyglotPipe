# PolyglotPipe

**Multilingual Media Intelligence Pipeline**

PolyglotPipe ingests multilingual video, audio, and documents, extracts structured knowledge across languages, and serves it through a RAG-powered query interface with a built-in evaluation harness.

Drop a folder of foreign-language conference talks, compliance PDFs, and meeting recordings — get a searchable, cross-lingual knowledge base you can query in any language.

---

## Problem

Global companies drown in multilingual content — investor calls in Mandarin, compliance PDFs in German, product demos in Japanese. Analysts rely on expensive human translation pipelines with multi-day turnaround. PolyglotPipe makes this content instantly queryable, with provenance tracking back to the original source and timestamp.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    LangGraph Orchestrator                       │
│            (stateful agent graph + checkpointing)               │
│                                                                 │
│  ┌──────────┐   ┌──────────────┐   ┌─────────────┐             │
│  │  Ingest   │──▶│  Translate    │──▶│   Query     │             │
│  │  Node     │   │  Node        │   │   Node      │             │
│  └──────────┘   └──────────────┘   └─────────────┘             │
│       │                │                   │                    │
│       ▼                ▼                   ▼                    │
│  ┌─────────────────────────────────────────────────────┐       │
│  │              Shared State (LangGraph)                │       │
│  │   documents, embeddings, API budget, checkpoints    │       │
│  └─────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LangChain Components                         │
│                                                                 │
│  DocumentLoaders    PromptTemplates    ChatGoogleGenerativeAI   │
│  Retrievers         OutputParsers      TextSplitters            │
└─────────────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
│  Local CPU   │  │  Gemini API  │  │  pgvector /       │
│  Models      │  │  (Free Tier) │  │  sqlite-vec       │
│              │  │              │  │                    │
│ Whisper small│  │ Flash-Lite   │  │ Hybrid search:     │
│ MiniLM-L6-v2│  │ Flash        │  │ dense + BM25       │
│ Tesseract    │  │              │  │                    │
│ Piper TTS   │  │ 15 RPM       │  │ Row-level security │
└──────────────┘  └──────────────┘  └──────────────────┘
```

## Key Features

- **Hybrid local/cloud inference** — CPU-friendly models run locally (Whisper, MiniLM, Tesseract); translation and reasoning use Gemini's free tier via a provider-agnostic interface
- **Multi-agent orchestration** — LangGraph state machine with conditional routing, parallel fan-out, rate-limit gating, and checkpoint/resume across laptop sleep cycles
- **LangChain component layer** — prompt templates, output parsers, retrievers, and document loaders following LangChain's composable abstractions
- **Cross-lingual RAG** — hybrid pgvector search (dense + BM25), reranking, and citation grounding across 15+ languages
- **Eval harness** — RAGAS metrics (faithfulness, context precision, answer relevance) plus custom translation quality scores, all running in CI
- **Production patterns at laptop scale** — rate limiting, exponential backoff, structured logging, Prometheus metrics, cost tracking, encrypted storage

## Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | Intel i5 (2020+) or Apple M1 | Any modern quad-core |
| RAM | 8 GB | 16 GB |
| Disk | 5 GB free | 10 GB free |
| GPU | Not required | Not required |
| Network | Required for Gemini API | Required for Gemini API |

Peak RAM usage: ~3.5 GB (Whisper 2 GB + MiniLM 0.1 GB + vector store 0.5 GB + overhead).

## Tech Stack

| Layer | Tool | License |
|-------|------|---------|
| Orchestration | LangGraph | Apache 2.0 |
| Chains / components | LangChain | MIT |
| Audio STT | faster-whisper (small, INT8) | MIT |
| OCR | Tesseract + PyMuPDF | Apache 2.0 |
| Translation / reasoning | Gemini 2.5 Flash-Lite | Free tier |
| Summarization / QA | Gemini 2.5 Flash | Free tier |
| Embeddings | all-MiniLM-L6-v2 | Apache 2.0 |
| Vector store | pgvector or sqlite-vec | PostgreSQL / MIT |
| API | FastAPI | MIT |
| UI | Gradio | Apache 2.0 |
| Eval | RAGAS | Apache 2.0 |
| Observability | Prometheus + structlog | Apache 2.0 |
| TTS (stretch) | Piper | MIT |

## Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 15+ with pgvector extension (or use sqlite-vec for zero-setup)
- FFmpeg (for audio extraction from video)
- Tesseract OCR
- A Google AI Studio API key (free, no credit card required)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/polyglotpipe.git
cd polyglotpipe

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template and add your Gemini API key
cp .env.example .env
# Edit .env and set GOOGLE_API_KEY=your_key_here

# Initialize the database
python scripts/init_db.py

# Verify installation
python scripts/healthcheck.py
```

### Ingest Your First Document

```bash
# Ingest a single file
python -m polyglotpipe.ingest --file path/to/document.pdf --target-lang en

# Ingest a directory of mixed media
python -m polyglotpipe.ingest --dir path/to/media/ --target-lang en

# Resume an interrupted ingestion
python -m polyglotpipe.ingest --resume
```

### Query the Knowledge Base

```bash
# Start the API server
python -m polyglotpipe.serve

# Or launch the Gradio demo UI
python -m polyglotpipe.demo
```

Then open `http://localhost:7860` and ask questions in any language.

## Project Structure

```
polyglotpipe/
├── chains/                    # LangChain chains
│   ├── translation.py         #   Translation chain (Gemini Flash-Lite)
│   ├── qa.py                  #   QA / RAG generation chain (Gemini Flash)
│   ├── extraction.py          #   Document extraction chain
│   └── summarization.py       #   Summarization chain
├── graph/                     # LangGraph orchestration
│   ├── nodes/                 #   Agent nodes
│   │   ├── ingest.py          #     Ingestion node (fan-out by file type)
│   │   ├── translate.py       #     Translation node (rate-limit aware)
│   │   ├── embed.py           #     Embedding node (local MiniLM)
│   │   └── query.py           #     Query node (retrieve + generate)
│   ├── state.py               #   Shared state definition
│   ├── edges.py               #   Conditional edge logic
│   └── pipeline.py            #   Graph assembly
├── providers/                 # Provider-agnostic interfaces
│   ├── base.py                #   Abstract base classes
│   ├── gemini.py              #   Gemini API provider
│   ├── local_opus.py          #   Local opus-mt fallback provider
│   └── rate_limiter.py        #   Rate-limit-aware client wrapper
├── retrieval/                 # Vector store and search
│   ├── store.py               #   pgvector / sqlite-vec store
│   ├── hybrid.py              #   Hybrid dense + BM25 search
│   └── reranker.py            #   Cross-encoder reranker
├── eval/                      # Evaluation harness
│   ├── harness.py             #   RAGAS evaluation runner
│   ├── translation_eval.py    #   Translation quality (chrF++)
│   ├── datasets/              #   Test datasets
│   └── reports/               #   Generated eval reports
├── api/                       # API layer
│   ├── server.py              #   FastAPI application
│   ├── models.py              #   Pydantic request/response models
│   └── middleware.py          #   Auth, rate limiting, CORS
├── observability/             # Monitoring
│   ├── metrics.py             #   Prometheus metrics
│   ├── logging.py             #   Structured logging config
│   └── cost_tracker.py        #   API cost tracking
├── scripts/                   # Utility scripts
│   ├── init_db.py             #   Database initialization
│   ├── healthcheck.py         #   Installation verification
│   └── seed_eval.py           #   Seed evaluation datasets
├── tests/                     # Test suite
│   ├── unit/                  #   Unit tests (chains, providers)
│   ├── integration/           #   Integration tests (graph, API)
│   └── eval/                  #   Eval suite (RAGAS benchmarks)
├── docker-compose.yml         #   Local dev environment
├── Makefile                   #   Common commands
├── .env.example               #   Environment template
├── .github/
│   └── workflows/
│       ├── ci.yml             #   Lint + unit tests on every PR
│       └── eval.yml           #   Full eval suite on main
└── requirements.txt
```

## Configuration

All configuration is via environment variables (loaded from `.env`):

```bash
# Required
GOOGLE_API_KEY=your_gemini_api_key

# Database (defaults to sqlite-vec for zero-setup)
DB_BACKEND=sqlite          # or "postgres"
DATABASE_URL=sqlite:///polyglotpipe.db
# DATABASE_URL=postgresql://user:pass@localhost:5432/polyglotpipe

# Model configuration
WHISPER_MODEL=small        # tiny | small | medium
EMBEDDING_MODEL=all-MiniLM-L6-v2
GEMINI_TRANSLATION_MODEL=gemini-2.5-flash-lite
GEMINI_QA_MODEL=gemini-2.5-flash

# Rate limiting
GEMINI_RPM_LIMIT=15
GEMINI_RPD_LIMIT=1000

# Security
ENCRYPT_DB=true
API_AUTH_ENABLED=false      # Enable for multi-user deployments
```

## Evaluation

Run the eval harness locally:

```bash
# Run the full RAGAS eval suite
make eval

# Run translation quality benchmarks
make eval-translation

# Generate eval report
make eval-report
```

The eval harness tracks:
- **Faithfulness** — are answers grounded in retrieved context?
- **Context precision** — is the retrieved context relevant?
- **Answer relevance** — does the answer address the question?
- **Translation quality** — chrF++ scores across language pairs
- **Latency** — p50 / p95 / p99 per query
- **Cost** — estimated API cost per query

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for the two-person development workflow, branching strategy, and CI/CD pipeline. See [PROJECT_PLAN.md](PROJECT_PLAN.md) for the full project specification.

## License

MIT