# CV Ranking MVP

## Project Structure

- `backend/`: FastAPI application
- `frontend/`: Next.js application
- `infra/`: Infrastructure configuration (Docker)
- `tests/`: Tests
- `docs/`: Documentation

## Setup

### Prerequisites
- Docker & Docker Compose
- Node.js 18+
- Python 3.11+
- Poetry

### Running Locally

1. Start the database and backend:
   ```bash
   docker-compose up --build
   ```

2. Start the frontend (in a separate terminal):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. Access the application:
   - Frontend: http://localhost:3000
   - Backend API Docs: http://localhost:8000/docs
