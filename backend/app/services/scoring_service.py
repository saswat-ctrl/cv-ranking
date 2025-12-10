import numpy as np
from typing import List, Dict, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from app.core.config import settings
from app.core.error_codes import RankingErrorCode, create_error_response
import logging

logger = logging.getLogger(__name__)

def calculate_semantic_similarity(jd_embedding: np.ndarray, cv_embedding: np.ndarray) -> float:
    """
    Calculate cosine similarity between JD and CV embeddings
    Returns: float between 0.0 and 1.0
    """
    if jd_embedding is None or cv_embedding is None:
        return 0.0
        
    try:
        # Reshape for sklearn (1, -1)
        jd_vec = jd_embedding.reshape(1, -1)
        cv_vec = cv_embedding.reshape(1, -1)
        
        score = cosine_similarity(jd_vec, cv_vec)[0][0]
        
        # Clamp to [0, 1] range
        return float(max(0.0, min(1.0, score)))
    except Exception as e:
        logger.error(f"Semantic similarity calculation failed: {e}")
        return 0.0

def calculate_keyword_similarity_batch(jd_text: str, cv_texts: List[str]) -> List[float]:
    """
    Calculate TF-IDF keyword similarity for multiple CVs (BATCH MODE)
    This is 10-20x faster than individual calculations
    """
    if not jd_text or not cv_texts:
        return [0.0] * len(cv_texts)
        
    try:
        # Create vectorizer with bigrams
        vectorizer = TfidfVectorizer(
            max_features=settings.TFIDF_MAX_FEATURES,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=1
        )
        
        # Fit on JD + all CVs together
        # Handle empty texts by replacing with placeholder
        processed_cvs = [t if t and t.strip() else "empty_document" for t in cv_texts]
        all_texts = [jd_text] + processed_cvs
        
        tfidf_matrix = vectorizer.fit_transform(all_texts)
        
        # Calculate similarities (JD vs each CV)
        jd_vector = tfidf_matrix[0:1]
        cv_vectors = tfidf_matrix[1:]
        
        similarities = cosine_similarity(jd_vector, cv_vectors)[0]
        
        # Clamp and return
        return [float(max(0.0, min(1.0, s))) for s in similarities]
        
    except Exception as e:
        logger.error(f"Batch keyword similarity calculation failed: {e}")
        return [0.0] * len(cv_texts)

def extract_matching_skills(jd_text: str, candidate_skills: List[str]) -> List[str]:
    """
    Extract skills that appear in JD using TOKENIZED matching
    Prevents false positives like "Go" matching "Google"
    """
    if not jd_text or not candidate_skills:
        return []
    
    # Tokenize JD (split on whitespace and common delimiters)
    jd_lower = jd_text.lower()
    trans_table = str.maketrans({
        ',': ' ', '.': ' ', '/': ' ', '(': ' ', ')': ' ', 
        ':': ' ', ';': ' ', '-': ' ', '[': ' ', ']': ' '
    })
    jd_processed = jd_lower.translate(trans_table)
    jd_tokens = set(jd_processed.split())
    
    matching = []
    for skill in candidate_skills:
        skill_lower = skill.lower()
        # Apply same normalization to skill
        skill_processed = skill_lower.translate(trans_table)
        skill_tokens = skill_processed.split()
        
        if not skill_tokens:
            continue
            
        # Check if all tokens from the skill appear in the JD
        if all(token in jd_tokens for token in skill_tokens):
            matching.append(skill)
    
    return matching

def calculate_final_score(
    semantic_score: float, 
    keyword_score: float, 
    skill_match_ratio: float
) -> float:
    """
    Calculate final weighted score (0-100)
    Weights: 50% Semantic, 30% Keyword, 20% Skills
    """
    # Weights
    W_SEMANTIC = 0.5
    W_KEYWORD = 0.3
    W_SKILLS = 0.2
    
    final = (
        (semantic_score * W_SEMANTIC) + 
        (keyword_score * W_KEYWORD) + 
        (skill_match_ratio * W_SKILLS)
    ) * 100
    
    return round(final, 1)

def generate_reasoning(
    semantic_score: float,
    keyword_score: float,
    matching_skills: List[str],
    missing_skills: List[str] = None
) -> Dict[str, Any]:
    """Generate structured reasoning for the score"""
    
    # Determine strength
    final_score = calculate_final_score(
        semantic_score, 
        keyword_score, 
        len(matching_skills) / (len(matching_skills) + len(missing_skills or []) + 1)
    )
    
    if final_score >= 80:
        summary = "Excellent Match"
    elif final_score >= 60:
        summary = "Good Match"
    elif final_score >= 40:
        summary = "Potential Match"
    else:
        summary = "Weak Match"
        
    return {
        "summary": summary,
        "score_breakdown": {
            "semantic": round(semantic_score * 100, 1),
            "keyword": round(keyword_score * 100, 1),
            "skill_match": len(matching_skills)
        },
        "key_skills_found": matching_skills[:10],  # Top 10
        "explanation": f"Candidate matches {len(matching_skills)} required skills. " +
                      f"Semantic relevance is {round(semantic_score*100)}%."
    }

if __name__ == "__main__":
    # Inline test
    print("Testing Scoring Service...")
    
    # Test 1: Semantic
    v1 = np.array([0.1, 0.2, 0.3])
    v2 = np.array([0.1, 0.2, 0.3])
    score = calculate_semantic_similarity(v1, v2)
    assert score > 0.99
    print("✅ Semantic similarity works")
    
    # Test 2: Batch TF-IDF
    jd = "Python Django"
    cvs = ["Python developer", "Java developer"]
    scores = calculate_keyword_similarity_batch(jd, cvs)
    assert scores[0] > scores[1]
    print("✅ Batch TF-IDF works")
    
    # Test 3: Skills
    jd = "Looking for Go developer"
    skills = ["Go", "Google"]
    matches = extract_matching_skills(jd, skills)
    assert "Go" in matches
    assert "Google" not in matches
    print("✅ Skill matching works")
