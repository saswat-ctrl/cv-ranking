"""
Resume Parsing Service
Extracts structured information from CV text using spaCy NER and regex patterns.
"""

import re
import logging
from typing import Optional, List, Dict
import spacy

logger = logging.getLogger(__name__)

# Lazy load spaCy model
_nlp = None

def get_nlp():
    """Lazy load spaCy model to avoid startup overhead"""
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.error("spaCy model 'en_core_web_sm' not found. Run: python -m spacy download en_core_web_sm")
            raise
    return _nlp


# Common skills database (can be extended)
SKILLS_DATABASE = {
    # Programming Languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust", "ruby", "php",
    "swift", "kotlin", "scala", "r", "matlab", "perl", "shell", "bash",
    
    # Web Frameworks
    "react", "angular", "vue", "vue.js", "next.js", "nuxt", "svelte", "django", "flask",
    "fastapi", "spring", "spring boot", "express", "express.js", "node.js", "nodejs",
    "laravel", "rails", "ruby on rails", "asp.net", ".net", "dotnet",
    
    # Databases
    "sql", "mysql", "postgresql", "postgres", "mongodb", "redis", "elasticsearch",
    "cassandra", "dynamodb", "oracle", "sql server", "sqlite", "mariadb", "neo4j", "firebase",
    
    # Cloud & DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s", "terraform",
    "ansible", "jenkins", "gitlab", "github actions", "circleci", "travis ci",
    "helm", "istio", "prometheus", "grafana", "elk", "datadog", "new relic",
    
    # Data & ML
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch", "keras", "spark",
    "hadoop", "kafka", "airflow", "dbt", "tableau", "power bi", "looker", "n8n", "langchain",
    "claude", "chatgpt", "openai", "llm", "genai", "generative ai", "perplexity",
    
    # Product Management
    "product management", "product roadmap", "roadmap", "strategy", "agile", "scrum", 
    "kanban", "jira", "confluence", "user stories", "backlog", "sprint planning", 
    "product strategy", "market research", "competitor analysis", "ab testing", 
    "user research", "wireframing", "prototyping", "mvp", "product launch",
    "stakeholder management", "kpi", "okr", "metrics", "analytics", "ga4", 
    "google analytics", "mixpanel", "amplitude", "segment", "hotjar",
    
    # Tools & Others
    "git", "postman", "swagger", "rest api", "graphql", "microservices", 
    "ci/cd", "tdd", "unit testing", "selenium", "replit", "lovable", "bolt",
    "salesforce", "servicenow", "excel", "powerpoint", "figma", "miro",
}


async def extract_name(text: str) -> Optional[str]:
    """
    Extract person name from CV text using spaCy NER.
    Assumes name is likely in first few lines or first PERSON entity.
    
    Args:
        text: CV text content
        
    Returns:
        Extracted name or None
    """
    try:
        nlp = get_nlp()
        
        # Process first 500 characters (name usually at top)
        doc = nlp(text[:500])
        
        # Find PERSON entities
        persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
        
        if persons:
            # Return first person name found
            name = persons[0].strip()
            logger.info(f"Extracted name: {name}")
            return name
        
        # Fallback: try first line if it looks like a name (2-4 words, capitalized)
        first_line = text.split('\n')[0].strip()
        words = first_line.split()
        if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w):
            logger.info(f"Extracted name from first line: {first_line}")
            return first_line
        
        logger.warning("Could not extract name from CV")
        return None
        
    except Exception as e:
        logger.error(f"Name extraction failed: {str(e)}")
        return None


async def extract_email(text: str) -> Optional[str]:
    """
    Extract email address from CV text using regex.
    
    Args:
        text: CV text content
        
    Returns:
        Extracted email or None
    """
    try:
        # Email regex pattern
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        if emails:
            # Return first email found
            email = emails[0].lower()
            logger.info(f"Extracted email: {email}")
            return email
        
        logger.warning("Could not extract email from CV")
        return None
        
    except Exception as e:
        logger.error(f"Email extraction failed: {str(e)}")
        return None


async def extract_phone(text: str) -> Optional[str]:
    """
    Extract phone number from CV text using regex.
    Handles Indian and international formats.
    
    Args:
        text: CV text content
        
    Returns:
        Extracted phone number or None
    """
    try:
        # Phone patterns (Indian and international)
        patterns = [
            r'\+91[-\s]?\d{10}',  # +91-9876543210 or +91 9876543210
            r'\+91\d{10}',  # +919876543210
            r'\d{10}',  # 9876543210
            r'\(\d{3}\)[-\s]?\d{3}[-\s]?\d{4}',  # (123) 456-7890
            r'\d{3}[-\s]?\d{3}[-\s]?\d{4}',  # 123-456-7890
        ]
        
        for pattern in patterns:
            phones = re.findall(pattern, text)
            if phones:
                phone = phones[0].strip()
                logger.info(f"Extracted phone: {phone}")
                return phone
        
        logger.warning("Could not extract phone from CV")
        return None
        
    except Exception as e:
        logger.error(f"Phone extraction failed: {str(e)}")
        return None


async def extract_skills(text: str) -> List[str]:
    """
    Extract skills from CV text using keyword matching against skills database.
    
    Args:
        text: CV text content
        
    Returns:
        List of extracted skills
    """
    try:
        text_lower = text.lower()
        found_skills = set()
        
        for skill in SKILLS_DATABASE:
            # Use word boundaries to avoid partial matches
            # e.g., "java" shouldn't match "javascript"
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                found_skills.add(skill)
        
        skills_list = sorted(list(found_skills))
        logger.info(f"Extracted {len(skills_list)} skills: {skills_list[:10]}...")
        return skills_list
        
    except Exception as e:
        logger.error(f"Skills extraction failed: {str(e)}")
        return []


async def extract_experience_years(text: str) -> Optional[int]:
    """
    Extract years of experience from CV text using regex patterns.
    
    Args:
        text: CV text content
        
    Returns:
        Years of experience or None
    """
    try:
        # Patterns like "5 years of experience", "7+ years", "10 yrs"
        patterns = [
            r'(\d+)\+?\s*years?\s+of\s+experience',
            r'(\d+)\+?\s*yrs?\s+experience',
            r'experience:\s*(\d+)\+?\s*years?',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                years = int(matches[0])
                logger.info(f"Extracted experience: {years} years")
                return years
        
        logger.warning("Could not extract years of experience")
        return None
        
    except Exception as e:
        logger.error(f"Experience extraction failed: {str(e)}")
        return None


async def parse_resume(text: str) -> Dict:
    """
    Main parsing function that extracts all structured information from CV text.
    
    Args:
        text: CV text content
        
    Returns:
        Dictionary with parsed fields
    """
    logger.info("Parsing resume...")
    
    parsed_data = {
        "name": await extract_name(text),
        "email": await extract_email(text),
        "phone": await extract_phone(text),
        "skills": await extract_skills(text),
        "experience_years": await extract_experience_years(text),
    }
    
    logger.info(f"Resume parsing complete. Found: name={bool(parsed_data['name'])}, "
                f"email={bool(parsed_data['email'])}, phone={bool(parsed_data['phone'])}, "
                f"skills={len(parsed_data['skills'])}")
    
    return parsed_data
