# Django Scaffold Design — Todo Project

## Overview

Production-ready Django scaffolding for the "todo" project with Docker Compose orchestration, split settings, CI, and tooling.

## Project Structure

```
todo/
├── compose/
│   ├── Dockerfile              # Multi-stage: dev + production targets
│   ├── entrypoint.sh           # Wait for postgres, run migrations, exec CMD
│   └── start.sh                # Start daphne or runserver_plus inside container
├── config/
│   └── settings/
│       ├── __init__.py         # Imports based on DJANGO_ENV env var
│       ├── base.py             # Shared: apps, middleware, db, cache, channels
│       ├── local.py            # DEBUG=True, debug-toolbar, runserver_plus
│       └── production.py       # DEBUG=False, secure cookies, HSTS
├── traefik/
│   ├── traefik.yml             # Static Traefik config
│   └── certs/                  # Self-signed certs for HTTPS dev (gitignored)
├── docker-compose.yml          # All services: traefik, django, postgres, valkey
├── .env.example                # Template for secrets and config
├── .github/
│   └── workflows/
│       ├── ci.yml              # Tests + ruff on all branches/PRs
│       └── version-release.yml # Commitizen auto-versioning on main
├── .pre-commit-config.yaml     # Ruff linting + formatting hooks
├── pyproject.toml              # Deps, ruff config, commitizen config
├── manage.py                   # Updated to use config.settings
└── todo/                       # Django project package
    ├── asgi.py                 # Updated for Channels
    ├── urls.py
    └── wsgi.py
```

## Docker Compose Services

### Traefik (reverse proxy)

- Image: `traefik:v3`
- External port: `${TRAEFIK_PORT:-8080}`
- Protocol: `${TRAEFIK_PROTOCOL:-http}`
- When `TRAEFIK_PROTOCOL=https`: uses self-signed certs from `traefik/certs/`. A `traefik/generate-cert.sh` script creates the self-signed cert via `openssl req` if `traefik/certs/cert.pem` does not exist. This script runs as a Compose entrypoint override for the Traefik service when HTTPS is configured.
- Routes all traffic to the django service via labels-based discovery

### Django (ASGI application)

- Built from `compose/Dockerfile`, dev target for local development
- Runs Daphne on port 8000 internally (`daphne -b 0.0.0.0 -p 8000 todo.asgi:application`)
- Alternatively: `runserver_plus --cert-file` for SSL testing at the Django level
- Source mounted as volume for hot reload in dev
- Depends on: postgres, valkey
- Traefik labels for routing

### PostgreSQL

- Image: `postgres:17`
- Credentials from `.env`: `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
- Named volume for data persistence

### Valkey

- Image: `valkey/valkey:8`
- Port 6379 internal only
- No auth for dev
- DB 0: Django cache backend
- DB 1: Channels layer

## Settings Configuration

### base.py (shared)

- `SECRET_KEY` from `os.environ["SECRET_KEY"]`
- Database: PostgreSQL via `psycopg`, reading `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST` (default `postgres`), `POSTGRES_PORT` (default `5432`)
- Cache: `django.core.cache.backends.redis.RedisCache` at `redis://valkey:6379/0`
- Channels: `channels_redis.core.RedisChannelLayer` at `redis://valkey:6379/1`
- `INSTALLED_APPS`: django defaults + `daphne`, `channels`, `django_extensions`
- `ASGI_APPLICATION = "todo.asgi.application"`
- `STATIC_URL = "static/"`, `STATIC_ROOT = BASE_DIR / "staticfiles"`

### local.py (development)

- Imports everything from base
- `DEBUG = True`
- `ALLOWED_HOSTS = ["*"]`
- Adds `debug_toolbar` to `INSTALLED_APPS` and its middleware
- `django_extensions` already in base (provides `runserver_plus`)

### production.py

- Imports everything from base
- `DEBUG = False`
- `ALLOWED_HOSTS` from `os.environ["ALLOWED_HOSTS"]` (comma-separated)
- `SECURE_SSL_REDIRECT = True`
- `SESSION_COOKIE_SECURE = True`
- `CSRF_COOKIE_SECURE = True`
- `SECURE_HSTS_SECONDS = 31536000`

### __init__.py

- Reads `DJANGO_ENV` (default `"local"`)
- Dynamically imports from `config.settings.{DJANGO_ENV}`

## Dockerfile (multi-stage)

### Base stage

- `FROM python:3.12-slim`
- Install system deps: `libpq-dev`, `gcc` (for psycopg)
- Install uv
- Copy `pyproject.toml` + `uv.lock`, install production deps

### Dev target

- Extends base
- Install dev dependency group (ruff, django-extensions, django-debug-toolbar, Werkzeug, pyOpenSSL)
- Copy source code
- Set `DJANGO_ENV=local`

### Prod target

- Extends base
- Copy source code
- Run `collectstatic --noinput`
- Set `DJANGO_ENV=production`

## Container Scripts

### entrypoint.sh

1. Wait for Postgres: loop `pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT` until success
2. Run `python manage.py migrate --noinput`
3. `exec "$@"` (run the CMD)

### start.sh

- Starts `daphne -b 0.0.0.0 -p 8000 todo.asgi:application`

## Environment Variables

`.env.example`:

```
DJANGO_ENV=local
SECRET_KEY=change-me-to-a-real-secret-key
POSTGRES_DB=todo
POSTGRES_USER=todo
POSTGRES_PASSWORD=change-me-to-a-real-password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
TRAEFIK_PORT=8080
TRAEFIK_PROTOCOL=http
```

A `.env` file (not committed) is generated during implementation with working local defaults (a random secret key, `todo`/`todo` for Postgres, etc.).

## Ignore Files

### .gitignore

Standard Python/Django ignores plus:
- `.env` (secrets)
- `.claude/` (Claude Code session data)
- `.idea/` (JetBrains IDE)
- `traefik/certs/` (generated self-signed certs)
- `staticfiles/` (collectstatic output)
- `__pycache__/`, `*.pyc`, `.venv/`, `db.sqlite3`, `*.egg-info/`, `dist/`, `.ruff_cache/`

### .dockerignore

Mirrors `.gitignore` plus: `.git/`, `docs/`, `.github/`, `.pre-commit-config.yaml`, `*.md` (except requirements), `.venv/`

## CI/CD

### ci.yml — runs on all branches and PRs to main

- Trigger: push to any branch, PRs to main
- Python 3.12
- Postgres service container for test DB
- Steps:
  1. Checkout
  2. Install uv
  3. `uv sync`
  4. `ruff check .`
  5. `ruff format --check .`
  6. `python manage.py test` with Postgres env vars

### version-release.yml — runs on push to main only

- Commitizen bump + changelog
- Per CLAUDE.md specification

## Tooling

### pyproject.toml

- **Dependencies**: `django>=5.2`, `channels`, `channels-redis`, `daphne`, `psycopg[binary]`
- **Dev dependencies** (uv group): `ruff`, `pre-commit`, `django-extensions`, `Werkzeug`, `pyOpenSSL`, `django-debug-toolbar`
- **Ruff config**: line-length 88, target Python 3.12, isort-compatible import sorting
- **Commitizen config**: version in `pyproject.toml` and `__version__.py`
- **No requirements.txt files**: all dependency metadata lives exclusively in `pyproject.toml` with `uv.lock`. All commands run via `uv` (e.g. `uv sync`, `uv run`). The Dockerfile uses `uv` to install deps.

### .pre-commit-config.yaml

- `ruff check --fix` (linting with auto-fix)
- `ruff format` (formatting)

## HTTPS in Development

Two options available:

1. **Traefik-level HTTPS**: Set `TRAEFIK_PROTOCOL=https` in `.env`. Traefik terminates SSL with a self-signed cert. Django sees plain HTTP internally.
2. **Django-level HTTPS**: Use `runserver_plus --cert-file /tmp/cert.pem 0.0.0.0:8000` for testing Django's HTTPS-specific settings (secure cookies, redirects). Requires Werkzeug + pyOpenSSL (included in dev deps).

## Key Decisions

- **Valkey over Redis**: drop-in compatible, avoids RSALv2/SSPL licensing concerns
- **Daphne as single ASGI server**: handles both HTTP and WebSocket, Channels reference server, simpler than split Gunicorn+Daphne
- **Env vars for port/protocol**: `TRAEFIK_PORT` and `TRAEFIK_PROTOCOL` in `.env` or command line, simpler than a shell wrapper script
- **Split settings modules**: explicit Python files per environment rather than django-environ single-file approach
- **uv for packaging**: fast, reliable dependency management
