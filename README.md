# Agah Platform

A unified backend for a messaging-platform bot, its admin panel and its
mini-app — rewritten from three disconnected codebases (PHP bot, separate
panel, separate mini-app) into a single FastAPI service with one shared API.

**Stack:** Python · FastAPI · SQLAlchemy + Alembic · PostgreSQL · Docker Compose


## Architecture
app/           Core API — [چه چیزی سرو می‌کنه]
bot/           Webhook-only bot; all logic goes through the core API
admin-panel/   [توضیح]
alembic/       Database migrations
tests/         [pytest — چند تست، چه چیزی پوشش می‌ده]


## Running locally
```bash
cp .env.example .env
docker compose up
```

