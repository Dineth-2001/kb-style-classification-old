from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()


class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    CLIENT_URL: str = "http://localhost:3000"
    DATABASE_URL: str | None = None

    model_config = {
        "env_file": ".env",
        # ignore extra env vars such as DATABASE_USERNAME/PASSWORD
        "extra": "ignore",
    }


settings = Settings()
