import pytest
from unittest.mock import MagicMock, patch
from app.services.ranking_service import rank_candidates
from app.models.job import Job
from app.models.candidate import Candidate
from app.core.config import settings

@pytest.mark.asyncio
async def test_rank_candidates_success():
    """Test successful ranking flow"""
    mock_db = MagicMock()
    
    # Mock Job
    mock_job = Job(id="job1", extracted_text="Python Developer with Django", embedding=None)
    mock_db.query().filter().first.return_value = mock_job
    
    # Mock Candidates
    c1 = Candidate(id="c1", job_id="job1", extracted_text="Python expert", is_readable=True)
    c2 = Candidate(id="c2", job_id="job1", extracted_text="Java expert", is_readable=True)
    mock_db.query().filter().all.return_value = [c1, c2]
    
    # Mock Services
    with patch("app.services.embedding_service.generate_embedding") as mock_gen_emb, \
         patch("app.services.embedding_service.generate_embeddings_batch") as mock_batch_emb, \
         patch("app.services.embedding_service.deserialize_embedding") as mock_deser, \
         patch("app.services.scoring_service.calculate_keyword_similarity_batch") as mock_tfidf:
        
        # Setup mocks
        mock_gen_emb.return_value = (b"job_emb", None)
        mock_batch_emb.return_value = [(b"c1_emb", None), (b"c2_emb", None)]
        mock_deser.return_value = MagicMock() # numpy array mock
        mock_tfidf.return_value = [0.8, 0.2]
        
        # Run
        result = await rank_candidates("job1", mock_db)
        
        # Verify
        assert result["success"] is True
        assert result["ranked_count"] == 2
        assert c1.ranking_score is not None
        assert c2.ranking_score is not None
        assert c1.embedding is not None
        assert c2.embedding is not None

@pytest.mark.asyncio
async def test_rank_candidates_insufficient():
    """Test insufficient candidates error"""
    mock_db = MagicMock()
    mock_db.query().filter().first.return_value = Job(id="job1")
    mock_db.query().filter().all.return_value = [Candidate(id="c1")] # Only 1
    
    result = await rank_candidates("job1", mock_db)
    
    assert "error_code" in result
    assert result["error_code"] == "INSUFFICIENT_CANDIDATES"

@pytest.mark.asyncio
async def test_rank_candidates_unreadable():
    """Test unreadable candidates handling"""
    mock_db = MagicMock()
    mock_db.query().filter().first.return_value = Job(id="job1", extracted_text="JD")
    
    # 2 candidates, but 1 unreadable
    c1 = Candidate(id="c1", is_readable=True, extracted_text="Text")
    c2 = Candidate(id="c2", is_readable=False, extracted_text="")
    mock_db.query().filter().all.return_value = [c1, c2]
    
    # Should fail because only 1 readable candidate (need min 2)
    result = await rank_candidates("job1", mock_db)
    
    assert "error_code" in result
    assert result["error_code"] == "INSUFFICIENT_CANDIDATES" 
    # Logic: Filter readable -> check count. 1 < 2 -> Fail.
