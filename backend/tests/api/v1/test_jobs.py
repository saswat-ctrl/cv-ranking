import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from app.models.job import RankingJob

@pytest.mark.asyncio
async def test_upload_jd_success(client: AsyncClient, mock_db_session):
    """Test successful JD upload and job creation"""
    
    # Mock extraction service
    with patch("app.api.v1.endpoints.jobs.extract_text") as mock_extract:
        mock_extract.return_value = ("Extracted JD Text", None)
        
        # Mock DB behavior for creating job
        mock_db_session.add = MagicMock()
        mock_db_session.commit = MagicMock()
        mock_db_session.refresh = MagicMock()
        
        # Prepare file upload
        files = {
            "file": ("jd.pdf", b"dummy content", "application/pdf")
        }
        
        response = await client.post("/api/v1/jobs/upload_jd", files=files)
        
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["filename"] == "jd.pdf"
        assert data["extracted_text"] == "Extracted JD Text"

@pytest.mark.asyncio
async def test_upload_jd_invalid_file_type(client: AsyncClient):
    """Test upload with invalid file type"""
    
    files = {
        "file": ("jd.exe", b"dummy content", "application/x-msdownload")
    }
    
    response = await client.post("/api/v1/jobs/upload_jd", files=files)
    
    # Should fail validation or extraction
    # The current implementation might accept it but fail extraction, or validate extension
    # Let's assume validation
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]

@pytest.mark.asyncio
async def test_upload_jd_extraction_failure(client: AsyncClient):
    """Test handling of extraction failure"""
    
    with patch("app.api.v1.endpoints.jobs.extract_text") as mock_extract:
        mock_extract.return_value = (None, "Extraction failed")
        
        files = {
            "file": ("jd.pdf", b"corrupt content", "application/pdf")
        }
        
        response = await client.post("/api/v1/jobs/upload_jd", files=files)
        
        assert response.status_code == 400
        assert "Extraction failed" in response.json()["detail"]
