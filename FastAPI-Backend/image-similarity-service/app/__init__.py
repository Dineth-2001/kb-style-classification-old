from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.status import status_router
from app.routes.image import image_router
from app.routes.search import search_router
from config import settings
import boto3


ALLOWED_ORIGINS = [settings.CLIENT_URL]


def create_app():

    app = FastAPI(
        title="Style Classification API",
        version="0.1.0",
        description="API for style classification",
    )

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        # allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(status_router)
    app.include_router(image_router, prefix="/img")
    app.include_router(search_router, prefix="/img")

    return app
