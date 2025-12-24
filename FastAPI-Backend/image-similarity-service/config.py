from dotenv import load_dotenv
import os
from typing import Optional
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    ENVIRONMENT: Optional[str] = None
    
    # MongoDB (optional - not used for vector storage)
    MONGO_URL: Optional[str] = None
    MONGO_DB: Optional[str] = None
    
    # Client
    CLIENT_URL: Optional[str] = None
    
    # AWS S3
    AWS_ACCESS_KEY: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: Optional[str] = None
    AWS_BUCKET_NAME: Optional[str] = None
    
    # PostgreSQL / Neon (pgvector)
    DATABASE_URL: Optional[str] = None
    POSTGRES_DSN: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_PORT: Optional[str] = "5432"
    POSTGRES_DB: Optional[str] = None
    
    # pgvector settings
    PGVECTOR_DIM: Optional[str] = "768"  # CLIP ViT-L/14 embedding dimension

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields in .env


settings = Settings()
