import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from app.models.candidate import Candidate
from app.models.job import RankingJob

@pytest.mark.asyncio
async def test_download_stream_success(client: AsyncClient):
    """Test successful local file streaming"""
    
    # We need to mock path checks in downloads endpoint
    with patch("pathlib.Path.exists") as mock_exists, \
         patch("pathlib.Path.is_file") as mock_is_file, \
         patch("pathlib.Path.resolve") as mock_resolve:
         
        mock_exists.return_value = True
        mock_is_file.return_value = True
        # Mock resolve to return a safe path inside uploads
        mock_safe_path = MagicMock()
        mock_safe_path.__str__.return_value = "/backend/static/uploads/test.pdf"
        mock_safe_path.startswith.return_value = True
        mock_safe_path.suffix = ".pdf"
        mock_resolve.return_value = mock_safe_path
        
        response = await client.get("/api/v1/downloads/stream?path=test.pdf")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"

@pytest.mark.asyncio
async def test_download_stream_path_traversal(client: AsyncClient):
    """Test path traversal protection"""
    
    # This relies on the logic in downloads.py checking startswith base_dir
    # We can try to pass a path with ..
    
    response = await client.get("/api/v1/downloads/stream?path=../../etc/passwd")
    
    # Should be 404 or 403 depending on implementation details of resolve()
    # In our implementation, if it resolves outside base_dir, we might raise error or just fail check
    # Let's assume 404 for "File not found" or security block
    assert response.status_code in [403, 404]

@pytest.mark.asyncio
async def test_job_candidate_download_redirect(client: AsyncClient, mock_db_session):
    """Test redirect to download URL"""
    
    # Mock Job and Candidate
    mock_job = RankingJob(id="job1", user_id="test-user-id")
    mock_candidate = Candidate(id="c1", job_id="job1", cv_file_url="s3-key.pdf", name="John")
    
    def get_side_effect(model, id):
        if model == RankingJob and id == "job1":
            return mock_job
        if model == Candidate and id == "c1":
            return mock_candidate
        return None
        
    mock_db_session.get.side_effect = get_side_effect
    
    # Mock storage generate_download_url
    with patch("app.api.v1.endpoints.jobs.get_storage_provider") as mock_get_storage:
        mock_storage = MagicMock()
        mock_storage.generate_download_url.return_value = "http://s3.bucket/presigned-url"
        mock_get_storage.return_value = mock_storage
        
        # Client follows redirects by default? No, httpx default is follow_redirects=False (in newer versions)
        # But AsyncClient might differ. Let's check response status.
        
        response = await client.get("/api/v1/jobs/job1/candidates/c1/download", follow_redirects=False)
        
        assert response.status_code == 307
        assert response.headers["location"] == "http://s3.bucket/presigned-url"
