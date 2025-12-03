import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.ranking_service import rank_candidates
from app.core.exceptions import AppException
from app.core.error_codes import RankingErrorCode
from app.models.job import Job
from app.models.candidate import Candidate

@pytest.mark.asyncio
async def test_ranking_insufficient_candidates():
    """Test that ranking raises AppException when candidates are insufficient"""
    mock_db = AsyncMock()
    
    # Mock Job
    mock_job = Job(id="job1", extracted_text="Job Description")
    mock_db.execute.return_value.scalars.return_value.first.return_value = mock_job
    
    # Mock Candidates (only 1)
    mock_candidate = Candidate(id="c1", job_id="job1", is_readable=True)
    
    # Setup second execute call for candidates
    mock_result_candidates = MagicMock()
    mock_result_candidates.scalars.return_value.all.return_value = [mock_candidate]
    
    # Configure side_effect for execute to return job first, then candidates
    mock_result_job = MagicMock()
    mock_result_job.scalars.return_value.first.return_value = mock_job
    
    mock_db.execute.side_effect = [mock_result_job, mock_result_candidates]
    
    with pytest.raises(AppException) as exc_info:
        await rank_candidates("job1", mock_db)
    
    assert exc_info.value.code == RankingErrorCode.INSUFFICIENT_CANDIDATES.value
    assert exc_info.value.status_code == 400
    assert "Need at least" in exc_info.value.message

@pytest.mark.asyncio
async def test_ranking_job_not_found():
    """Test that ranking raises AppException when job is not found"""
    mock_db = AsyncMock()
    
    # Mock Job not found
    mock_result_job = MagicMock()
    mock_result_job.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_result_job
    
    with pytest.raises(AppException) as exc_info:
        await rank_candidates("job1", mock_db)
        
    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.message
