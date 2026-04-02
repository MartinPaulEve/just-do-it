#!/bin/bash
set -e

exec uv run daphne -b 0.0.0.0 -p 8000 todo.asgi:application
