# Contributing to PolyglotPipe

This document defines the two-person development workflow, branching strategy, CI/CD pipeline, and conventions for contributing to PolyglotPipe.

---

## Team Structure

### Engineer A — Pipeline & Orchestration Lead

Owns the data flow from raw media to embedded vectors.

**Directories owned:** `chains/`, `graph/`, `providers/`

**Responsibilities:**

- LangGraph graph assembly (nodes, edges, state, checkpointing)
- LangChain chains (translation, extraction, summarization)
- Provider-agnostic interfaces (Gemini provider, local opus-mt fallback)
- Rate-limiter and exponential backoff logic
- Document loaders and text splitters
- Ingestion CLI and batch processing

### Engineer B — Retrieval, API & Eval Lead

Owns the data flow from embedded vectors to user-facing answers.

**Directories owned:** `retrieval/`, `eval/`, `api/`, `observability/`

**Responsibilities:**

- pgvector / sqlite-vec store setup and schema
- Hybrid retrieval (dense + BM25 + reranker)
- RAG query chain (retrieve → rerank → generate)
- FastAPI server and Pydantic request/response models
- Gradio demo UI
- RAGAS eval harness and translation quality benchmarks
- Prometheus metrics and structured logging
- Cost tracking dashboard

### Shared Files

The following files are jointly owned and require **both engineers' approval** on any PR that modifies them:

- `api/models.py` — Pydantic types used across the interface boundary
- `graph/state.py` — LangGraph shared state definition
- `requirements.txt` / `pyproject.toml` — dependency changes
- `docker-compose.yml` — infrastructure changes
- `.github/workflows/` — CI/CD pipeline changes
- `.env.example` — environment variable changes

---

## Interface Contracts

Both engineers agree on these contracts before building. Any change requires a PR to the shared types file with both approvals before implementation begins.

### Contract 1: Document Schema

Engineer A produces LangChain `Document` objects with standardized metadata. Engineer B consumes them for embedding and storage.

```python
from langchain_core.documents import Document

# Every document produced by the ingestion pipeline must include:
Document(
    page_content="extracted and translated text",
    metadata={
        "source_path": "path/to/original/file.pdf",      # str, required
        "source_lang": "de",                               # str, ISO 639-1, required
        "target_lang": "en",                               # str, ISO 639-1, required
        "media_type": "pdf",                               # str, one of: audio|pdf|image|text
        "timestamp": "00:03:42",                           # Optional[str], for audio/video segments
        "confidence": 0.92,                                # float, translation/extraction confidence
        "chunk_index": 0,                                  # int, position within source document
    }
)
```

### Contract 2: Query Protocol

Engineer B exposes a query function that Engineer A's LangGraph query node calls.

```python
from pydantic import BaseModel

class QueryRequest(BaseModel):
    question: str
    target_lang: str = "en"
    top_k: int = 5
    filters: dict = {}           # e.g. {"media_type": "audio", "source_lang": "ja"}

class Source(BaseModel):
    content: str
    source_path: str
    source_lang: str
    media_type: str
    timestamp: str | None = None
    relevance_score: float

class QueryResult(BaseModel):
    answer: str
    sources: list[Source]
    latency_ms: float
    tokens_used: int
```

### Contract 3: Eval Dataset Format

Both engineers contribute test cases in JSONL format stored in `eval/datasets/`.

```jsonl
{"question": "What were the key findings?", "ground_truth": "Revenue increased 12%...", "context": ["In Q3 2025, the company reported..."], "lang": "en"}
{"question": "Was bedeutet die neue Richtlinie?", "ground_truth": "Die Richtlinie besagt...", "context": ["Gemäß Abschnitt 4..."], "lang": "de"}
```

File naming convention: `<domain>_<lang>.jsonl` (e.g., `finance_de.jsonl`, `legal_ja.jsonl`, `general_en.jsonl`).

---

## Branching Strategy

We use trunk-based development with short-lived feature branches.

### Branch Naming

```
feat/<initials>/<description>       # Feature work
fix/<initials>/<description>        # Bug fixes
refactor/<initials>/<description>   # Refactoring (no behavior change)
docs/<initials>/<description>       # Documentation only
```

Examples:

```
feat/ea/langgraph-orchestrator
feat/eb/ragas-eval-harness
fix/ea/whisper-vad-silence-bug
refactor/eb/retriever-interface
docs/ea/architecture-blog-post
```

### Branch Rules

1. **No direct commits to `main`.** All changes go through pull requests.
2. **Feature branches live at most 3 days.** If a feature takes longer, break it into smaller PRs with incremental progress.
3. **Every PR requires one approval** from the other engineer.
4. **PRs must pass CI** (lint, type check, unit tests) before merge.
5. **Squash merge to `main`** for clean, readable history.
6. **Delete branches after merge.** No stale branches.

### Typical Daily Flow

```bash
# Start your day: pull latest main
git checkout main
git pull origin main

# Create a feature branch
git checkout -b feat/ea/translation-chain

# Work, commit frequently with clear messages
git add .
git commit -m "feat: add translation chain with Gemini Flash-Lite provider"

# Push and open a PR
git push origin feat/ea/translation-chain
# Open PR on GitHub, request review from the other engineer

# After approval and CI passes: squash merge via GitHub UI
# Delete the branch
```

---

## Commit Message Convention

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <short description>

<optional body explaining why, not what>
```

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `ci`, `chore`

Examples:

```
feat: add rate-limited Gemini client with exponential backoff
fix: handle empty audio segments in Whisper loader
test: add RAGAS faithfulness baseline tests
refactor: extract provider interface into abstract base class
ci: add pip-audit security scan to PR workflow
docs: add architecture diagram to README
```

---

## CI/CD Pipeline

### On Every Pull Request (`ci.yml`)

All of the following must pass before a PR can be merged:

1. **Lint:** `ruff check .` and `ruff format --check .`
2. **Type check:** `mypy --strict polyglotpipe/`
3. **Unit tests:** `pytest tests/unit/ --cov=polyglotpipe --cov-fail-under=80`
4. **Integration tests:** `pytest tests/integration/` (with mocked Gemini API)
5. **Security scan:** `pip-audit` for known dependency vulnerabilities

### On Merge to Main (`eval.yml`)

1. Full RAGAS eval suite against all test datasets
2. Translation quality benchmarks (chrF++ across 5 language pairs)
3. Latency benchmarks (p50, p95, p99 on a standard 50-query set)
4. Results posted as a GitHub Actions summary
5. **Eval gates:** PR fails if faithfulness drops below 0.80 or latency p95 exceeds 5 seconds
6. Docker image build and push to GitHub Container Registry

### Running CI Locally

```bash
# Run the full CI suite before pushing
make ci

# Or run individual checks
make lint          # ruff check + format
make typecheck     # mypy --strict
make test          # pytest unit tests
make test-int      # pytest integration tests (needs .env)
make security      # pip-audit
make eval          # full RAGAS eval suite
```

---

## PR Review Guidelines

When reviewing the other engineer's PR:

1. **Check the interface contract.** If the PR changes anything in `api/models.py` or `graph/state.py`, verify both sides still agree.
2. **Run the tests locally** if CI is green but you want to verify behavior.
3. **Look for hardcoded values** that should be in `.env` or config.
4. **Check error handling.** Gemini API calls must have try/except with structured logging. Local model calls must handle OOM gracefully.
5. **Check for API key leaks.** No keys, tokens, or secrets in code, comments, or test fixtures.
6. **Check type hints.** All public functions must have full type annotations.
7. **Approve or request changes.** Don't leave PRs in limbo — respond within 24 hours.

---

## Conflict Resolution

The directory ownership model minimizes merge conflicts:

| Directory | Owner |
|-----------|-------|
| `chains/` | Engineer A |
| `graph/` | Engineer A |
| `providers/` | Engineer A |
| `retrieval/` | Engineer B |
| `eval/` | Engineer B |
| `api/` | Engineer B |
| `observability/` | Engineer B |
| `scripts/` | Whoever wrote it |
| `tests/unit/` | Matches source ownership |
| `tests/integration/` | Whoever wrote it |

If a merge conflict occurs on a shared file:

1. The engineer who opened the PR resolves the conflict.
2. Push the resolution and request re-review.
3. Never force-push to a branch that has an open PR with comments.

---

## Communication

- **Daily async standup:** Each engineer posts a 3-line update (yesterday / today / blockers) in the shared channel by 10 AM.
- **Weekly sync (30 min):** Review open PRs, discuss interface changes, adjust priorities, demo recent work.
- **Interface change protocol:** Any change to the three contracts requires a PR to the shared types file with both approvals before implementation work begins.
- **Urgent issues:** If you're blocked on the other person's code, message directly rather than waiting for standup.

---

## Development Environment Setup

```bash
# Clone and set up
git clone https://github.com/your-username/polyglotpipe.git
cd polyglotpipe
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt   # adds ruff, mypy, pytest, pip-audit

# Copy env template
cp .env.example .env
# Edit .env: set GOOGLE_API_KEY

# Initialize database
python scripts/init_db.py

# Verify everything works
make ci

# Pre-commit hooks (optional but recommended)
pre-commit install
```

---

## Makefile Reference

```makefile
make ci            # Run full CI suite locally
make lint          # Lint and format check
make typecheck     # mypy strict mode
make test          # Unit tests with coverage
make test-int      # Integration tests
make security      # pip-audit
make eval          # Full RAGAS eval suite
make eval-translation  # Translation quality benchmarks only
make eval-report   # Generate eval report
make serve         # Start FastAPI server
make demo          # Start Gradio demo UI
make docker-up     # Start Docker Compose environment
make docker-down   # Stop Docker Compose environment
make clean         # Remove build artifacts and caches
```