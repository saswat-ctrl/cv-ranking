#! /usr/bin/env bash
set -e

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start Uvicorn
echo "Starting production server (Uvicorn)..."
# Use the command passed from Docker CMD or default to uvicorn
if [ "$#" -eq 0 ]; then
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000
else
    exec "$@"
fi
