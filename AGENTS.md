# Repository Guidelines

## Project Overview

This repository contains a Vietnamese Legal Agentic RAG system.

Main stack:

- Python
- FastAPI
- LangGraph
- Chroma
- BM25
- Hybrid retrieval
- CrossEncoder / FlashRank reranking
- Gemini LLM
- Gradio
- Docker

The application is already functional. Current work focuses mainly on:

- reranker benchmarking
- Docker cleanup
- GitHub publication
- Hugging Face Docker deployment

Do not redesign the whole project unless explicitly requested.

---

## Project Structure & Module Organization

- `app/` contains the Python application.
- `app/api/` contains FastAPI routes.
- `app/graph/` contains LangGraph workflow and nodes.
- `app/prompts/` contains prompt templates.
- `app/state/` and `app/schemas/` contain shared state and Pydantic schemas.
- `app/retrieval/` contains retrieval and reranking logic.
- `app/ingestion/` contains indexing and ingestion code.
- `tests/` contains focused tests named `test_*.py`.
- `benchmark/` contains evaluation and retrieval experiments.
- `data/raw/` holds source legal documents.
- `vector_store/` holds Chroma and BM25 indexes used at runtime.
- `docs/` contains architecture and workflow notes.

Keep workflow decisions in `app/graph/`.

Keep retrieval logic inside `app/retrieval/`.

Keep prompts inside `app/prompts/`.

Do not duplicate retrieval or generation logic inside API routes.

---

## Current Retrieval Baseline

Do not change the production retrieval configuration unless the task explicitly requires it.

Current baseline includes:

- hybrid semantic + lexical retrieval
- Chroma / embedding retrieval
- BM25 retrieval
- reranking after retrieval
- top-k context selection

Existing benchmark results and ground-truth datasets must be preserved.

Any retrieval or reranker change must be evaluated before claiming improvement.

---

## Reranker Benchmark Rules

The next planned benchmark compares:

- CrossEncoder: `BAAI/bge-reranker-v2-m3`
- FlashRank: use the currently configured FlashRank model

For a fair benchmark:

1. Use the same queries.
2. Use the exact same retrieved candidate documents.
3. Do not rerun retrieval separately for each reranker unless necessary.
4. Prefer reusing saved retrieval candidates.
5. Keep benchmark code separate from the production reranker implementation.

Measure at minimum:

- total runtime
- average latency per query
- median latency
- minimum latency
- maximum latency
- available relevance / ranking metrics

Do not claim that FlashRank itself is faster or more accurate than CrossEncoder
if different underlying models are used.

Report the comparison as two complete reranker configurations.

Never modify benchmark ground truth to improve results.

Never overwrite historical benchmark outputs unless explicitly requested.

---

## Build, Test, and Development Commands

Create an environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Run the FastAPI backend:

```powershell
uvicorn app.main:app --reload --port 8000
```

Run the Gradio frontend:

```powershell
python app/gradio_app.py
```

Run the complete local application:

```powershell
docker compose up --build
```

Rebuild indexes only when explicitly necessary:

```powershell
python -m app.ingestion.build_chroma
python -m app.ingestion.build_bm25
```

Do not rebuild indexes automatically just because code was changed.

---

## Coding Style & Naming Conventions

Use:

- four-space indentation
- conventional Python / PEP 8 style
- `snake_case` for modules, functions, and variables
- `PascalCase` for classes
- `UPPER_SNAKE_CASE` for constants

Prefer:

- small focused functions
- type hints
- explicit configuration
- reusable services
- meaningful exceptions
- structured logging where appropriate

Avoid:

- giant functions
- hidden global state
- duplicated retrieval logic
- duplicated benchmark logic
- hard-coded absolute paths
- hard-coded secrets

Use `pathlib` and project-relative paths instead of Windows-specific absolute paths.

---

## Testing Guidelines

Tests use pytest conventions:

- files: `test_*.py`
- functions: `test_*`

Run:

```powershell
python -m pytest tests -q
```

Many tests may load models, indexes, or external services.

Run targeted tests first when appropriate.

Example:

```powershell
python -m pytest tests/test_chunker.py -q
```

Do not remove or weaken tests just to make them pass.

If a change affects:

- retrieval -> run relevant retrieval tests / benchmark
- reranking -> run reranker benchmark
- FastAPI -> test the affected endpoint
- Docker -> build and start the relevant containers
- Hugging Face deployment -> validate the production container locally

---

## Environment & Secrets

Never:

- modify `.env` unless explicitly requested
- print API keys
- commit `.env`
- copy `.env` into Docker images
- hard-code credentials
- expose secrets in benchmark output or logs

Use environment variables for secrets and deployment configuration.

`.env.example` must contain variable names only, never real secret values.

---

## Data & Index Safety

Do not delete, regenerate, or overwrite the following unless explicitly requested:

- `data/`
- `vector_store/`
- benchmark ground truth
- historical benchmark results

Before modifying index-related files, explain why regeneration is required.

---

## Docker Rules

Preserve the existing local architecture unless explicitly requested.

Current local deployment may use:

- FastAPI backend
- Gradio frontend
- Docker Compose

For Hugging Face deployment:

- do not break the existing local Docker Compose workflow
- prefer a separate production Dockerfile
- do not rely on host-mounted local paths
- do not include unnecessary raw data or benchmark files in the production image
- never include `.env`

---

## Agent Workflow

Before modifying code:

1. Inspect the relevant implementation.
2. Identify affected modules.
3. Explain the intended change.
4. Make the smallest reasonable change.
5. Run relevant validation.
6. Report the result.

For large changes, propose a plan before implementing.

Do not perform broad refactors unless explicitly requested.

---

## Completion Criteria

A task is not complete merely because code was written.

A task is complete when:

- the implementation works
- relevant validation passes
- existing behavior is not unintentionally broken
- changed files are listed
- executed commands are reported
- unresolved issues are clearly stated

---

## Commit & Pull Request Guidelines

Use short Conventional Commit-style messages, for example:

- `feat: add citation filter`
- `fix: handle empty retrieval`
- `benchmark: compare rerankers`
- `docs: update setup`
- `chore: prepare docker deployment`

Never:

- force push
- rewrite Git history
- merge branches automatically
- commit secrets
