# Setup and Testing Guide

## Prerequisites
Ensure you have Docker installed and running on your system.

## Step 1: Start the Services

```bash
# Start all services (database, backend, frontend)
docker-compose up --build -d

# Check if services are running
docker-compose ps
```

## Step 2: Run Database Migrations

```bash
# Run migrations inside the backend container
docker-compose exec backend alembic upgrade head

# Verify migrations were applied
docker-compose exec backend alembic current
```

Expected output should show: `003 (head)` indicating all three migrations are applied.

## Step 3: Test the Full Flow

### 3.1 Access the Application
- Frontend: http://localhost:3000
- Backend API Docs: http://localhost:8000/docs

### 3.2 Complete User Flow

1. **Sign Up**
   - Navigate to http://localhost:3000/signup
   - Enter email and name
   - Click "Sign up"

2. **Set Password**
   - You'll be redirected to `/set-password`
   - Enter and confirm your password
   - Click "Set Password"

3. **Login**
   - You'll be redirected to `/login`
   - Enter your email and password
   - Click "Sign in"

4. **Create a Job**
   - Navigate to http://localhost:3000/jobs/new
   - Upload a JD file (PDF, DOCX, PNG, or JPG)
   - Wait for extraction to complete
   - Click "Continue to Candidate Upload"

5. **Upload Candidates**
   - You'll be on `/jobs/[id]/candidates`
   - Fill in candidate name and email
   - Upload CV file
   - Click "Upload Candidate"
   - Repeat for up to 10 candidates
   - Try uploading an 11th to verify the limit

6. **Delete a Candidate**
   - Click "Delete" on any candidate
   - Confirm deletion
   - Verify the candidate is removed

## Step 4: Verify Backend Directly

You can also test the API directly using the Swagger UI:

```bash
# Open in browser
http://localhost:8000/docs
```

Test these endpoints:
1. `POST /api/v1/auth/signup`
2. `POST /api/v1/auth/set_password`
3. `POST /api/v1/auth/login` (copy the access_token)
4. Click "Authorize" button, paste token as `Bearer <token>`
5. `POST /api/v1/jobs/` (upload JD)
6. `GET /api/v1/jobs/{job_id}` (get job details)
7. `POST /api/v1/jobs/{job_id}/candidates` (upload candidate)
8. `GET /api/v1/jobs/{job_id}/candidates` (list candidates)
9. `DELETE /api/v1/jobs/{job_id}/candidates/{candidate_id}`

## Troubleshooting

### If migrations fail:
```bash
# Check database connection
docker-compose logs db

# Recreate database
docker-compose down -v
docker-compose up -d db
docker-compose exec backend alembic upgrade head
```

### If backend fails to start:
```bash
# Check backend logs
docker-compose logs backend

# Common issues:
# - Missing environment variables (check .env file)
# - Database not ready (wait a few seconds and restart)
```

### If frontend fails:
```bash
# Check frontend logs
docker-compose logs frontend

# Rebuild frontend
docker-compose up --build frontend
```

## Environment Variables

Create a `.env` file in the backend directory if not exists:

```env
# Backend/.env
POSTGRES_SERVER=db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=cv_ranking
SECRET_KEY=your-secret-key-change-this-in-production
GEMINI_API_KEY=your-gemini-api-key
GCS_BUCKET_NAME=cv-ranking-bucket
GOOGLE_CLOUD_PROJECT=your-project-id
BACKEND_CORS_ORIGINS=["http://localhost:3000"]
```

Create a `.env.local` file in the frontend directory:

```env
# Frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## Next: Ranking Engine Module

Once testing is complete, we'll implement:
- AI-based CV ranking against JD
- Match score calculation (0-100)
- Reasoning generation
- Results display with sorted candidates
