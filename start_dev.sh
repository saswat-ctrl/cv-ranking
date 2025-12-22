#!/bin/bash

# Ensure .env exists
if [ ! -f .env ]; then
    echo "Creating .env from backend defaults..."
    cat > .env <<EOF
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=cv_ranking
POSTGRES_SERVER=db
SECRET_KEY=supersecretkey
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:4000"]
EOF
fi

# Start Database
echo "Starting Database container..."
docker compose up -d db

# Wait for DB to be ready
echo "Waiting for Database to be ready..."
sleep 5

# Run Migrations
echo "Running Migrations..."
cd backend
python3 -m alembic upgrade head
cd ..

echo "---------------------------------------------------"
echo "✅ Database is UP and Migrations applied."
echo "---------------------------------------------------"
echo "To start services locally:"
echo "1. Backend: cd backend && SECRET_KEY=supersecretkey POSTGRES_SERVER=localhost python3 -m uvicorn app.main:app --reload --port 8000"
echo "2. Frontend: cd frontend && npm run dev -- -p 4000"
echo "---------------------------------------------------"
