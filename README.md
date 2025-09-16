# Agentic Job Matching Platform

This project is a walking skeleton prototype for an agentic AI job-matching system.

## Components
- **backend/**: FastAPI service exposing profiles and matches API
- **crawler/**: Scrapes job postings from known sources.yaml
- **discovery/**: Agentic discovery service to find new ATS career sites
- **infra/**: Docker Compose and DB initialization

## Running
```
cd infra
docker compose up --build
```

To run crawler:
```
docker compose run --rm crawler python crawler.py
```

To run discovery:
```
docker compose run --rm discovery python discovery.py
```
