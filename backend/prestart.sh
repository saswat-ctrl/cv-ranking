#! /usr/bin/env bash
set -e

# Run migrations
echo "Running database migrations..."
alembic upgrade head

# Start Gunicorn
echo "Starting production server..."
# Use the command passed from Docker CMD or default to gunicorn if no arguments
if [ "$#" -eq 0 ]; then
    exec gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
else
    exec "$@"
fi
