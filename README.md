# Agentic Job Matching — Walking Skeleton (Phase 0)
This repo is a minimal end‑to‑end slice:
- Upload résumé → parse → store profile
- Seed crawler fetches a few job pages → stores jobs
- `/matches` returns top matches via simple hybrid scoring (keyword + vectors)

## Quick Start (Docker Compose)
Requirements: Docker & Docker Compose
```bash
podman compose -f infra/docker-compose.yml up --build
```
Services:
- Postgres @ `localhost:5433` (user: `postgres`, pass: `postgres`)
- API @ `http://localhost:8000/docs`

### Initialize database schema
Docker compose runs `init.sql` enabling `pgvector` and creating tables/schemas.

### Seed crawl (optional)
In a new terminal run:
```bash
podman compose -f infra/docker-compose.yml run --rm crawler python crawler.py
```

## API (FastAPI)
Open Swagger at `http://localhost:8000/docs`
- `POST /profiles` — multipart: `file=<resume>`; returns `profile_id`
- `GET /matches?profile_id=...&limit=20` — returns ranked jobs
- `POST /feedback` — save/dismiss feedback

## Folder Layout
```
backend/
  app/
    main.py
    db.py
    models.py
    embeddings.py
    matching.py
  requirements.txt
  Dockerfile
crawler/
  crawler.py
  requirements.txt
  Dockerfile
  sources.yaml
infra/
  docker-compose.yml
  init.sql
README.md
```
## Replace Stubs Later
- **embeddings.py**: plug your real embedding model/API.
- **crawler.py**: add more adapters and robust parsing.
- **matching.py**: replace heuristic weighting with LTR or reranker.
