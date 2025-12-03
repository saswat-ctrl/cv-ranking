import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from app.models.candidate import Candidate
from app.models.job import RankingJob

@pytest.mark.asyncio
async def test_create_candidate_success(client: AsyncClient, mock_db_session):
    """Test successful candidate upload"""
    
    # Mock Job existence
    mock_job = RankingJob(id="job1", user_id="test-user-id")
    mock_db_session.get.return_value = mock_job
    
    # Mock candidate count (below limit)
    mock_db_session.execute.return_value.scalar.return_value = 5
    
    # Mock extraction and parsing
    with patch("app.api.v1.endpoints.jobs.extract_text") as mock_extract, \
         patch("app.api.v1.endpoints.jobs.parse_resume") as mock_parse:
        
        mock_extract.return_value = ("Extracted CV", None)
        mock_parse.return_value = {"email": "candidate@example.com", "name": "John Doe"}
        
        files = {
            "file": ("cv.pdf", b"dummy content", "application/pdf")
        }
        
        response = await client.post("/api/v1/jobs/job1/candidates", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "candidate@example.com"
        assert data["name"] == "John Doe"

@pytest.mark.asyncio
async def test_create_candidate_max_limit(client: AsyncClient, mock_db_session):
    """Test that max candidates limit is enforced"""
    
    # Mock Job
    mock_job = RankingJob(id="job1", user_id="test-user-id")
    mock_db_session.get.return_value = mock_job
    
    # Mock candidate count (at limit)
    mock_db_session.execute.return_value.scalar.return_value = 15 # MAX_CANDIDATES
    
    files = {
        "file": ("cv.pdf", b"dummy content", "application/pdf")
    }
    
    response = await client.post("/api/v1/jobs/job1/candidates", files=files)
    
    assert response.status_code == 400
    assert "Maximum number of candidates" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_candidate_wrong_job_owner(client: AsyncClient, mock_db_session):
    """Test that users cannot upload to other users' jobs"""
    
    # Mock Job belonging to DIFFERENT user
    mock_job = RankingJob(id="job1", user_id="other-user-id")
    mock_db_session.get.return_value = mock_job
    
    files = {
        "file": ("cv.pdf", b"dummy content", "application/pdf")
    }
    
    response = await client.post("/api/v1/jobs/job1/candidates", files=files)
    
    assert response.status_code == 404 # Or 403 depending on implementation logic (usually 404 for security)

@pytest.mark.asyncio
async def test_delete_candidate_success(client: AsyncClient, mock_db_session):
    """Test successful candidate deletion"""
    
    # Mock Job and Candidate
    mock_job = RankingJob(id="job1", user_id="test-user-id")
    mock_candidate = Candidate(id="c1", job_id="job1", cv_file_url="/path/to/cv.pdf")
    
    # Setup mock_db_session.get side effects
    # First call gets Job, second gets Candidate (or vice versa depending on logic)
    # Actually, usually we get Candidate first, then check Job ownership
    
    def get_side_effect(model, id):
        if model == RankingJob and id == "job1":
            return mock_job
        if model == Candidate and id == "c1":
            return mock_candidate
        return None
        
    mock_db_session.get.side_effect = get_side_effect
    
    # Mock storage delete
    with patch("app.api.v1.endpoints.jobs.get_storage_provider") as mock_get_storage:
        mock_storage = MagicMock()
        mock_storage.delete.return_value = True
        mock_get_storage.return_value = mock_storage
        
        response = await client.delete("/api/v1/jobs/job1/candidates/c1")
        
        assert response.status_code == 200
        assert response.json()["success"] is True
