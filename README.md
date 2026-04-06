# Django Project Template

A production-ready Django project scaffold with Docker, CI/CD, and modern tooling.

## What's Included

- **Django 5.2** with split settings (local / production / test)
- **Docker Compose** with Traefik reverse proxy, PostgreSQL 17, and Valkey (Redis)
- **ASGI support** via Daphne and Django Channels
- **HTMX** integration with django-htmx middleware
- **uv** for fast Python package management
- **Ruff** linter and formatter with pre-commit hooks
- **Commitizen** for conventional commits and automated versioning
- **GitHub Actions** CI (lint + test) and deploy (Docker build + ECR push)
- **WhiteNoise** for production static file serving
- **Traefik** with auto-generated self-signed TLS certificates for local dev
- **Split settings** architecture (`config/settings/base.py`, `local.py`, `production.py`, `test.py`)

## Quick Start

```bash
# 1. Clone and configure
git clone <your-repo-url> myproject
cd myproject
python manage.py configure_project --name myproject --description "My awesome app"

# 2. Set up environment
cp .env.example .env
# Edit .env with your secrets

# 3. Start services
docker compose up -d

# 4. Access
open http://localhost:8080
```

## Project Structure

```
├── config/settings/       # Split Django settings
│   ├── __init__.py        # Auto-selects settings based on DJANGO_ENV
│   ├── base.py            # Shared settings
│   ├── local.py           # Development overrides
│   ├── production.py      # Production security settings
│   └── test.py            # Test runner settings
├── todo/                  # Django project package (rename with configure_project)
│   ├── urls.py            # Root URL configuration
│   ├── wsgi.py            # WSGI entry point
│   └── asgi.py            # ASGI entry point (Channels)
├── compose/               # Docker build files
│   ├── Dockerfile         # Multi-stage (dev + production)
│   ├── entrypoint.sh      # Wait for DB + migrate
│   └── start.sh           # Start Daphne
├── traefik/               # Reverse proxy config
├── .github/workflows/     # CI, deploy, version-release
├── manage.py
├── pyproject.toml
└── docker-compose.yml
```

## Management Commands

### `configure_project`

Renames the project and updates all references:

```bash
python manage.py configure_project --name myproject --description "My project description"
```

This updates:
- `pyproject.toml` (name, description, isort config)
- Django settings (`ROOT_URLCONF`, `WSGI_APPLICATION`, `ASGI_APPLICATION`)
- Docker and compose files
- CI workflow environment variables
- `.env.example` and `.env.prod.example`
- Renames the `todo/` package directory

## Deployment

See [docs/deployment.md](docs/deployment.md) for production deployment instructions.

## CI/CD

- **CI** runs on all branches: linting (ruff) and tests (pytest with PostgreSQL)
- **Deploy** runs on `main`: builds Docker image and pushes to ECR
- **Version Release** runs on `main`: auto-bumps version using commitizen

---

*Template scaffold for Django projects with modern tooling and deployment infrastructure.*
