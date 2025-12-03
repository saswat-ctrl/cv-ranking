import json
from pathlib import Path
from typing import List
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

_skills_cache = None

def load_skills_database() -> List[str]:
    """Load skills from external JSON file"""
    global _skills_cache
    
    if _skills_cache is not None:
        return _skills_cache
    
    try:
        # Handle relative path from app root
        skills_path = Path(settings.SKILLS_DATABASE_PATH)
        if not skills_path.is_absolute():
            # Assuming running from backend root
            skills_path = Path.cwd() / skills_path
            
        if not skills_path.exists():
            logger.warning(f"Skills database not found at {skills_path}, trying absolute path fallback")
            # Fallback for Docker environment
            skills_path = Path("/app/app/data/skills.json")
            
        with open(skills_path, 'r') as f:
            data = json.load(f)
        
        # Flatten all categories
        all_skills = []
        for category_skills in data.get("categories", {}).values():
            all_skills.extend(category_skills)
        
        _skills_cache = list(set(all_skills))  # Remove duplicates
        logger.info(f"Loaded {len(_skills_cache)} skills from database")
        return _skills_cache
        
    except Exception as e:
        logger.error(f"Failed to load skills database: {e}")
        # Fallback to hardcoded minimal set
        return ["python", "javascript", "sql", "aws", "docker", "react", "django"]

def reload_skills_database():
    """Force reload skills (for updates)"""
    global _skills_cache
    _skills_cache = None
    return load_skills_database()

if __name__ == "__main__":
    # Inline test
    skills = load_skills_database()
    print(f"Loaded {len(skills)} skills")
    assert "python" in skills
    assert "react" in skills
    print("✅ Skills service working")
