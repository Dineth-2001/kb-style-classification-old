from dotenv import load_dotenv
import os
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    ENVIRONMENT: str = os.getenv("ENVIRONMENT")
    CLIENT_URL: str = os.getenv("CLIENT_URL")
    IMAGE_SIMILARITY_SERVICE_URL: str = os.getenv("IMAGE_SIMILARITY_SERVICE_URL")
    OB_SIMILARITY_SERVICE_URL: str = os.getenv("OB_SIMILARITY_SERVICE_URL")

    class Config:
        env_file = ".env"


settings = Settings()
