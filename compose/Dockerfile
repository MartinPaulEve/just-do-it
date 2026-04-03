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

ARG SECRET_KEY=build-only-key
RUN SECRET_KEY=${SECRET_KEY} \
    ALLOWED_HOSTS=localhost \
    CSRF_TRUSTED_ORIGINS=https://localhost \
    POSTGRES_HOST=localhost \
    uv run python manage.py collectstatic --noinput

ENTRYPOINT ["/app/compose/entrypoint.sh"]
CMD ["uv", "run", "daphne", "-b", "0.0.0.0", "-p", "8000", "todo.asgi:application"]
