from typing import List, Union, Optional
from pydantic import AnyHttpUrl, validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "CV Ranking MVP"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:4000",
        "http://127.0.0.1:4000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # Database
    # NOTE: For Docker we talk to the 'db' service by default. If you want to use
    # a different DSN, you can override SQLALCHEMY_DATABASE_URI via env vars.
    POSTGRES_SERVER: str = "db"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "cv_ranking"
    SQLALCHEMY_DATABASE_URI: Optional[str] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict[str, any]) -> str:
        if isinstance(v, str) and v:
            return v
        return (
            f"postgresql+asyncpg://"
            f"{values.get('POSTGRES_USER')}:"
            f"{values.get('POSTGRES_PASSWORD')}@"
            f"{values.get('POSTGRES_SERVER')}/"
            f"{values.get('POSTGRES_DB')}"
        )

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Logging
    LOG_JSON_FORMAT: bool = False
    LOG_LEVEL: str = "INFO"

    # Storage Configuration
    STORAGE_TYPE: str = "local"  # local, s3, gcs
    
    # S3 / GCS Configuration
    STORAGE_BUCKET_NAME: str = "cv-ranking-bucket"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    AWS_ENDPOINT_URL: Optional[str] = None  # For MinIO or other S3-compatible services

    # Ranking Configuration
    MIN_CANDIDATES: int = 2
    MAX_CANDIDATES: int = 15
    RANKING_VERSION: str = "v1.0-sbert-miniLM-l6-tfidf300"

    # Text Processing Limits
    MAX_TEXT_LENGTH: int = 200_000  # 200K chars max
    JD_EMBEDDING_LENGTH: int = 3_000  # Truncate JD for SBERT
    MIN_READABLE_LENGTH: int = 50  # Increased from 50
    MIN_JD_LENGTH: int = 50  # Minimum JD length for quality warning

    # Model Configuration
    SBERT_MODEL: str = "all-MiniLM-L6-v2"
    TFIDF_MAX_FEATURES: int = 300

    # Skills Database
    SKILLS_DATABASE_PATH: str = "app/data/skills.json"

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")

settings = Settings()
