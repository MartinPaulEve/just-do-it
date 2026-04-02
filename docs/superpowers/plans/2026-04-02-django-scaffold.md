# Django Scaffold Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Set up production-ready Django scaffolding with Docker Compose (Traefik, Postgres, Valkey, Daphne), split settings, CI, and dev tooling.

**Architecture:** Docker Compose orchestrates four services (Traefik, Django/Daphne, Postgres, Valkey). Settings are split into base/local/production modules under `config/settings/`. All dependencies managed via `pyproject.toml` + uv. CI runs tests and linting on all branches.

**Tech Stack:** Django 5.2, Daphne, Channels, Channels-Redis, PostgreSQL 17, Valkey 8, Traefik v3, Ruff, uv, GitHub Actions

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `.gitignore` | Git ignore rules |
| Create | `.dockerignore` | Docker build context exclusions |
| Create | `.env.example` | Template for environment variables |
| Create | `.env` | Local working environment variables (not committed) |
| Create | `__version__.py` | Version string for commitizen |
| Modify | `pyproject.toml` | All deps, ruff config, commitizen config |
| Create | `config/__init__.py` | Empty package init |
| Create | `config/settings/__init__.py` | Dynamic settings import based on DJANGO_ENV |
| Create | `config/settings/base.py` | Shared Django settings |
| Create | `config/settings/local.py` | Dev overrides (DEBUG, toolbar) |
| Create | `config/settings/production.py` | Production overrides (security) |
| Modify | `manage.py` | Update DJANGO_SETTINGS_MODULE to config.settings |
| Modify | `todo/asgi.py` | Update for Channels + new settings path |
| Modify | `todo/wsgi.py` | Update settings path |
| Create | `compose/Dockerfile` | Multi-stage Docker build |
| Create | `compose/entrypoint.sh` | Wait for Postgres, migrate, exec CMD |
| Create | `compose/start.sh` | Start Daphne inside container |
| Create | `traefik/traefik.yml` | Traefik static configuration |
| Create | `traefik/dynamic/` | Traefik dynamic config directory |
| Create | `traefik/dynamic/tls.yml` | TLS config for HTTPS mode |
| Create | `traefik/generate-cert.sh` | Self-signed cert generator |
| Create | `docker-compose.yml` | All service definitions |
| Create | `.pre-commit-config.yaml` | Ruff linting + formatting hooks |
| Create | `.github/workflows/ci.yml` | Tests + linting CI on all branches |
| Create | `.github/workflows/version-release.yml` | Commitizen auto-versioning on main |

---

### Task 1: Ignore files and environment variables

**Files:**
- Create: `.gitignore`
- Create: `.dockerignore`
- Create: `.env.example`
- Create: `.env`

- [ ] **Step 1: Create `.gitignore`**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.egg-info/
dist/
*.egg

# Virtual environments
.venv/

# Django
db.sqlite3
staticfiles/

# IDE
.idea/
.vscode/
*.swp
*.swo

# Claude Code
.claude/

# Environment
.env

# Ruff
.ruff_cache/

# Traefik generated certs
traefik/certs/

# OS
.DS_Store
Thumbs.db
```

- [ ] **Step 2: Create `.dockerignore`**

```dockerignore
.git/
.github/
.venv/
.idea/
.vscode/
.claude/
.env
.ruff_cache/
.pre-commit-config.yaml
docs/
traefik/certs/
db.sqlite3
staticfiles/
*.md
__pycache__/
*.py[cod]
*.egg-info/
dist/
.DS_Store
```

- [ ] **Step 3: Create `.env.example`**

```
DJANGO_ENV=local
SECRET_KEY=change-me-to-a-real-secret-key
POSTGRES_DB=todo
POSTGRES_USER=todo
POSTGRES_PASSWORD=change-me-to-a-real-password
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
TRAEFIK_PORT=8080
TRAEFIK_HTTPS_PORT=8443
```

- [ ] **Step 4: Create `.env` with working local defaults**

```
DJANGO_ENV=local
SECRET_KEY=django-local-dev-key-not-for-production-use-change-me
POSTGRES_DB=todo
POSTGRES_USER=todo
POSTGRES_PASSWORD=todo
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
TRAEFIK_PORT=8080
TRAEFIK_HTTPS_PORT=8443
```

- [ ] **Step 5: Commit**

```bash
git add .gitignore .dockerignore .env.example
git commit -m "chore: add .gitignore, .dockerignore, and .env.example"
```

Note: `.env` is not committed (covered by `.gitignore`).

---

### Task 2: pyproject.toml and dependency installation

**Files:**
- Modify: `pyproject.toml`
- Create: `__version__.py`

- [ ] **Step 1: Update `pyproject.toml` with full configuration**

```toml
[project]
name = "todo"
version = "1.0.0"
description = "Todo application"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "django>=5.2",
    "channels>=4.0",
    "channels-redis>=4.0",
    "daphne>=4.0",
    "psycopg[binary]>=3.1",
]

[dependency-groups]
dev = [
    "ruff>=0.11",
    "pre-commit>=4.0",
    "django-extensions>=3.2",
    "werkzeug>=3.0",
    "pyopenssl>=24.0",
    "django-debug-toolbar>=5.0",
]

[tool.commitizen]
version = "1.0.0"
version_files = [
    "__version__.py",
    "pyproject.toml:version"
]
update_changelog_on_bump = true

[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = [
    "E",    # pycodestyle errors
    "W",    # pycodestyle warnings
    "F",    # pyflakes
    "I",    # isort
    "B",    # flake8-bugbear
    "UP",   # pyupgrade
]

[tool.ruff.lint.isort]
known-first-party = ["todo", "config"]
```

- [ ] **Step 2: Create `__version__.py`**

```python
__version__ = "1.0.0"
```

- [ ] **Step 3: Run `uv sync` to install all dependencies**

Run: `uv sync`
Expected: All dependencies installed, `uv.lock` updated.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock __version__.py
git commit -m "chore: configure pyproject.toml with all dependencies and tooling"
```

---

### Task 3: Split settings — base.py

**Files:**
- Create: `config/__init__.py`
- Create: `config/settings/__init__.py`
- Create: `config/settings/base.py`

- [ ] **Step 1: Create `config/__init__.py`**

Empty file.

- [ ] **Step 2: Create `config/settings/__init__.py`**

```python
import importlib
import os

DJANGO_ENV = os.environ.get("DJANGO_ENV", "local")

_module = importlib.import_module(f"config.settings.{DJANGO_ENV}")

from config.settings.base import *  # noqa: F401, F403

_globals = globals()
for _attr in dir(_module):
    if _attr.isupper():
        _globals[_attr] = getattr(_module, _attr)
```

Wait — this is fragile. A simpler and more standard approach:

```python
import os

DJANGO_ENV = os.environ.get("DJANGO_ENV", "local")

if DJANGO_ENV == "production":
    from config.settings.production import *  # noqa: F401, F403
else:
    from config.settings.local import *  # noqa: F401, F403
```

- [ ] **Step 3: Create `config/settings/base.py`**

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = os.environ["SECRET_KEY"]

ALLOWED_HOSTS = []

INSTALLED_APPS = [
    "daphne",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "channels",
    "django_extensions",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "todo.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "todo.wsgi.application"
ASGI_APPLICATION = "todo.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "todo"),
        "USER": os.environ.get("POSTGRES_USER", "todo"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "todo"),
        "HOST": os.environ.get("POSTGRES_HOST", "postgres"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": os.environ.get("CACHE_URL", "redis://valkey:6379/0"),
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [
                os.environ.get("CHANNELS_REDIS_URL", "redis://valkey:6379/1")
            ],
        },
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
```

- [ ] **Step 4: Commit**

```bash
git add config/
git commit -m "feat: add split settings base configuration"
```

---

### Task 4: Split settings — local.py and production.py

**Files:**
- Create: `config/settings/local.py`
- Create: `config/settings/production.py`

- [ ] **Step 1: Create `config/settings/local.py`**

```python
from config.settings.base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

INSTALLED_APPS += [  # noqa: F405
    "debug_toolbar",
]

MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405

INTERNAL_IPS = [
    "127.0.0.1",
    "172.0.0.0/8",
]

# django-debug-toolbar needs this for Docker
import socket

hostname, _, ips = socket.gethostbyname_ex(socket.gethostname())
INTERNAL_IPS += [".".join(ip.split(".")[:-1] + ["1"]) for ip in ips]
```

- [ ] **Step 2: Create `config/settings/production.py`**

```python
import os

from config.settings.base import *  # noqa: F401, F403

DEBUG = False

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

- [ ] **Step 3: Commit**

```bash
git add config/settings/local.py config/settings/production.py
git commit -m "feat: add local and production settings overrides"
```

---

### Task 5: Update manage.py, asgi.py, wsgi.py for new settings path

**Files:**
- Modify: `manage.py`
- Modify: `todo/asgi.py`
- Modify: `todo/wsgi.py`
- Delete: `todo/settings.py`

- [ ] **Step 1: Update `manage.py`**

Change line 9 from:
```python
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "todo.settings")
```
to:
```python
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
```

- [ ] **Step 2: Update `todo/asgi.py`**

Replace the full file with:

```python
import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter(
    {
        "http": django_asgi_app,
    }
)
```

- [ ] **Step 3: Update `todo/wsgi.py`**

Change line 14 from:
```python
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "todo.settings")
```
to:
```python
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
```

- [ ] **Step 4: Delete `todo/settings.py`**

```bash
rm todo/settings.py
```

- [ ] **Step 5: Verify settings load correctly**

Run: `DJANGO_ENV=local SECRET_KEY=test-key uv run python -c "import django; django.setup(); from django.conf import settings; print(settings.DEBUG)"`
Expected: `True`

- [ ] **Step 6: Commit**

```bash
git add manage.py todo/asgi.py todo/wsgi.py
git rm todo/settings.py
git commit -m "refactor: switch to split settings under config.settings"
```

---

### Task 6: Docker — Dockerfile and container scripts

**Files:**
- Create: `compose/Dockerfile`
- Create: `compose/entrypoint.sh`
- Create: `compose/start.sh`

- [ ] **Step 1: Create `compose/Dockerfile`**

```dockerfile
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

# ------- dev target -------
FROM base AS dev

RUN uv sync --frozen

COPY . .

ENV DJANGO_ENV=local
ENV DJANGO_SETTINGS_MODULE=config.settings

ENTRYPOINT ["/app/compose/entrypoint.sh"]
CMD ["/app/compose/start.sh"]

# ------- production target -------
FROM base AS production

RUN uv sync --frozen --no-dev

COPY . .

ENV DJANGO_ENV=production
ENV DJANGO_SETTINGS_MODULE=config.settings

RUN uv run python manage.py collectstatic --noinput || true

ENTRYPOINT ["/app/compose/entrypoint.sh"]
CMD ["uv", "run", "daphne", "-b", "0.0.0.0", "-p", "8000", "todo.asgi:application"]
```

- [ ] **Step 2: Create `compose/entrypoint.sh`**

```bash
#!/bin/bash
set -e

echo "Waiting for PostgreSQL..."
until pg_isready -h "${POSTGRES_HOST:-postgres}" -p "${POSTGRES_PORT:-5432}" -q; do
    sleep 1
done
echo "PostgreSQL is ready."

echo "Running migrations..."
uv run python manage.py migrate --noinput

exec "$@"
```

- [ ] **Step 3: Create `compose/start.sh`**

```bash
#!/bin/bash
set -e

exec uv run daphne -b 0.0.0.0 -p 8000 todo.asgi:application
```

- [ ] **Step 4: Make scripts executable**

```bash
chmod +x compose/entrypoint.sh compose/start.sh
```

- [ ] **Step 5: Commit**

```bash
git add compose/
git commit -m "feat: add Dockerfile and container scripts"
```

---

### Task 7: Traefik configuration

**Files:**
- Create: `traefik/traefik.yml`
- Create: `traefik/dynamic/tls.yml`
- Create: `traefik/generate-cert.sh`

- [ ] **Step 1: Create `traefik/traefik.yml`**

```yaml
api:
  dashboard: false

entryPoints:
  web:
    address: ":80"
  websecure:
    address: ":443"

providers:
  docker:
    exposedByDefault: false
  file:
    directory: /etc/traefik/dynamic
    watch: true
```

- [ ] **Step 2: Create `traefik/dynamic/tls.yml`**

```yaml
tls:
  stores:
    default:
      defaultCertificate:
        certFile: /etc/traefik/certs/cert.pem
        keyFile: /etc/traefik/certs/key.pem
```

- [ ] **Step 3: Create `traefik/generate-cert.sh`**

```bash
#!/bin/bash
set -e

CERT_DIR="/etc/traefik/certs"

if [ ! -f "$CERT_DIR/cert.pem" ]; then
    echo "Generating self-signed certificate..."
    mkdir -p "$CERT_DIR"
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$CERT_DIR/key.pem" \
        -out "$CERT_DIR/cert.pem" \
        -subj "/C=GB/ST=Dev/L=Dev/O=Dev/CN=localhost"
    echo "Certificate generated."
else
    echo "Certificate already exists, skipping generation."
fi

exec "$@"
```

- [ ] **Step 4: Make script executable and create certs directory**

```bash
chmod +x traefik/generate-cert.sh
mkdir -p traefik/certs
```

- [ ] **Step 5: Commit**

```bash
git add traefik/traefik.yml traefik/dynamic/ traefik/generate-cert.sh
git commit -m "feat: add Traefik configuration with HTTPS support"
```

---

### Task 8: Docker Compose

**Files:**
- Create: `docker-compose.yml`

- [ ] **Step 1: Create `docker-compose.yml`**

Single Traefik service listens on both HTTP (:80) and HTTPS (:443) entrypoints. Host ports are configurable via env vars. Access HTTP on `TRAEFIK_PORT` (default 8080), HTTPS on `TRAEFIK_HTTPS_PORT` (default 8443).

```yaml
services:
  traefik:
    image: traefik:v3.4
    ports:
      - "${TRAEFIK_PORT:-8080}:80"
      - "${TRAEFIK_HTTPS_PORT:-8443}:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik/traefik.yml:/etc/traefik/traefik.yml:ro
      - ./traefik/dynamic:/etc/traefik/dynamic:ro
      - ./traefik/certs:/etc/traefik/certs
      - ./traefik/generate-cert.sh:/generate-cert.sh:ro
    entrypoint: ["/generate-cert.sh"]
    command: ["traefik"]
    networks:
      - web

  django:
    build:
      context: .
      dockerfile: compose/Dockerfile
      target: dev
    volumes:
      - .:/app
    expose:
      - "8000"
    env_file:
      - .env
    depends_on:
      - postgres
      - valkey
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.django.rule=PathPrefix(`/`)"
      - "traefik.http.routers.django.entrypoints=web"
      - "traefik.http.services.django.loadbalancer.server.port=8000"
      - "traefik.http.routers.django-secure.rule=PathPrefix(`/`)"
      - "traefik.http.routers.django-secure.entrypoints=websecure"
      - "traefik.http.routers.django-secure.tls=true"
      - "traefik.http.services.django-secure.loadbalancer.server.port=8000"
    networks:
      - web
      - backend

  postgres:
    image: postgres:17
    volumes:
      - postgres_data:/var/lib/postgresql/data
    env_file:
      - .env
    networks:
      - backend

  valkey:
    image: valkey/valkey:8
    networks:
      - backend

volumes:
  postgres_data:

networks:
  web:
  backend:
```

- [ ] **Step 2: Commit**

```bash
git add docker-compose.yml .env.example
git commit -m "feat: add Docker Compose with Traefik, Postgres, and Valkey"
```

---

### Task 9: Pre-commit configuration

**Files:**
- Create: `.pre-commit-config.yaml`

- [ ] **Step 1: Create `.pre-commit-config.yaml`**

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

- [ ] **Step 2: Install pre-commit hooks**

Run: `uv run pre-commit install`
Expected: `pre-commit installed at .git/hooks/pre-commit`

- [ ] **Step 3: Run pre-commit on all files to verify**

Run: `uv run pre-commit run --all-files`
Expected: All hooks pass (may auto-fix some files).

- [ ] **Step 4: Commit any auto-fixed files along with the config**

```bash
git add .pre-commit-config.yaml
git add -u  # pick up any ruff auto-fixes
git commit -m "chore: add pre-commit hooks with ruff linting and formatting"
```

---

### Task 10: GitHub Actions — CI workflow

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  push:
    branches:
      - "**"
  pull_request:
    branches:
      - main

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v6

      - name: Set up Python
        run: uv python install 3.12

      - name: Install dependencies
        run: uv sync

      - name: Ruff check
        run: uv run ruff check .

      - name: Ruff format check
        run: uv run ruff format --check .

  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_DB: todo_test
          POSTGRES_USER: todo
          POSTGRES_PASSWORD: todo
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v6

      - name: Set up Python
        run: uv python install 3.12

      - name: Install dependencies
        run: uv sync

      - name: Run tests
        env:
          SECRET_KEY: test-secret-key-for-ci
          POSTGRES_DB: todo_test
          POSTGRES_USER: todo
          POSTGRES_PASSWORD: todo
          POSTGRES_HOST: localhost
          POSTGRES_PORT: 5432
          DJANGO_ENV: local
        run: uv run python manage.py test
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add CI workflow for linting and tests on all branches"
```

---

### Task 11: GitHub Actions — version release workflow

**Files:**
- Create: `.github/workflows/version-release.yml`

- [ ] **Step 1: Create `.github/workflows/version-release.yml`**

```yaml
name: Bump version

on:
  push:
    branches:
      - main

jobs:
  bump-version:
    if: "!startsWith(github.event.head_commit.message, 'bump:')"
    runs-on: ubuntu-latest
    name: "Bump version and create changelog with commitizen"
    steps:
      - name: Check out
        uses: actions/checkout@v6
        with:
          fetch-depth: 0
          ssh-key: "${{ secrets.COMMIT_KEY }}"
      - name: Create bump and changelog
        uses: commitizen-tools/commitizen-action@master
        with:
          push: false
      - name: Push using ssh
        run: |
          git push origin main --tags
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/version-release.yml
git commit -m "ci: add commitizen version-release workflow"
```

---

### Task 12: Final verification

- [ ] **Step 1: Verify ruff passes on all files**

Run: `uv run ruff check .`
Expected: No errors.

Run: `uv run ruff format --check .`
Expected: All files already formatted.

- [ ] **Step 3: Verify Django settings load**

Run: `SECRET_KEY=test DJANGO_ENV=local uv run python -c "import django; django.setup(); from django.conf import settings; print('DEBUG:', settings.DEBUG); print('ASGI:', settings.ASGI_APPLICATION)"`
Expected:
```
DEBUG: True
ASGI: todo.asgi.application
```

- [ ] **Step 4: Final commit if any files changed**

```bash
git add -u
git commit -m "chore: final scaffold verification and cleanup"
```
