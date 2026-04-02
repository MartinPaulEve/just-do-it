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
