import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from typing import List, Optional, Tuple, Dict
from app.core.config import settings
from app.core.error_codes import RankingErrorCode, create_error_response
import logging

logger = logging.getLogger(__name__)

# Singleton model
_model = None

def preload_model():
    """Preload SBERT model at server startup"""
    global _model
    if _model is None:
        logger.info(f"Loading SBERT model: {settings.SBERT_MODEL}")
        try:
            _model = SentenceTransformer(settings.SBERT_MODEL)
            logger.info("SBERT model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load SBERT model: {e}")
            raise
    return _model

def get_model():
    """Get SBERT model (lazy load if not preloaded)"""
    global _model
    if _model is None:
        return preload_model()
    return _model

def truncate_text(text: str, max_length: int) -> str:
    """Truncate text to prevent embedding failures"""
    if len(text) > max_length:
        logger.warning(f"Truncating text from {len(text)} to {max_length} chars")
        return text[:max_length]
    return text

def generate_embedding(text: str, max_length: int = 200_000) -> Tuple[Optional[bytes], Optional[Dict]]:
    """
    Generate embedding with text truncation
    Returns: (embedding_bytes, error_dict)
    """
    # Validate text
    if not text or not text.strip():
        return None, create_error_response(
            RankingErrorCode.TEXT_TOO_SHORT,
            "Cannot generate embedding: text is empty"
        )
    
    if len(text.strip()) < settings.MIN_READABLE_LENGTH:
        return None, create_error_response(
            RankingErrorCode.TEXT_TOO_SHORT,
            f"Text too short ({len(text)} chars). Minimum {settings.MIN_READABLE_LENGTH} required."
        )
    
    # Truncate if needed
    text = truncate_text(text, max_length)
    
    try:
        model = get_model()
        embedding = model.encode(text, convert_to_numpy=True, show_progress_bar=False)
        return pickle.dumps(embedding), None
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return None, create_error_response(
            RankingErrorCode.EMBEDDING_FAILED,
            f"Embedding generation failed: {str(e)}"
        )

def generate_embeddings_batch(texts: List[str], max_length: int = 200_000) -> List[Tuple[Optional[bytes], Optional[Dict]]]:
    """
    Generate embeddings for multiple texts (batch processing)
    Returns: List of (embedding_bytes, error_dict) tuples
    """
    # Truncate all texts
    processed_texts = []
    for t in texts:
        if t and t.strip() and len(t.strip()) >= settings.MIN_READABLE_LENGTH:
            processed_texts.append(truncate_text(t, max_length))
        else:
            processed_texts.append(None)
    
    # Get valid indices
    valid_indices = [i for i, t in enumerate(processed_texts) if t is not None]
    
    if not valid_indices:
        error = create_error_response(RankingErrorCode.TEXT_TOO_SHORT, "All texts too short or empty")
        return [(None, error)] * len(texts)
    
    try:
        model = get_model()
        valid_texts = [processed_texts[i] for i in valid_indices]
        embeddings = model.encode(valid_texts, batch_size=16, convert_to_numpy=True, show_progress_bar=False)
        
        # Map back to original indices
        result = []
        emb_idx = 0
        for i in range(len(texts)):
            if i in valid_indices:
                result.append((pickle.dumps(embeddings[emb_idx]), None))
                emb_idx += 1
            else:
                result.append((None, create_error_response(RankingErrorCode.TEXT_TOO_SHORT, "Text too short")))
        
        return result
    except Exception as e:
        logger.error(f"Batch embedding generation failed: {e}")
        error = create_error_response(RankingErrorCode.EMBEDDING_FAILED, str(e))
        return [(None, error)] * len(texts)

def deserialize_embedding(embedding_bytes: bytes) -> Optional[np.ndarray]:
    """Deserialize embedding from bytes"""
    if not embedding_bytes:
        return None
    try:
        return pickle.loads(embedding_bytes)
    except Exception as e:
        logger.error(f"Embedding deserialization failed: {e}")
        return None

if __name__ == "__main__":
    # Inline test
    import time
    print("Testing Embedding Service...")
    
    # Test 1: Preload
    start = time.time()
    preload_model()
    print(f"Model loaded in {time.time()-start:.2f}s")
    
    # Test 2: Single
    text = "This is a test document " * 10
    emb, err = generate_embedding(text)
    assert emb is not None
    assert err is None
    print("✅ Single embedding works")
    
    # Test 3: Batch
    texts = [text, "Short", text]
    results = generate_embeddings_batch(texts, max_length=1000)
    assert results[0][0] is not None
    assert results[1][0] is None  # Too short
    assert results[2][0] is not None
    print("✅ Batch embedding works")
