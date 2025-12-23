from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings

from app.routes.image import image_router
from app.routes.search import search_router


def create_app():
    app = FastAPI(
        title="API Gateway",
        version="0.1.0",
        description="API Gateway for the Image Classification Service",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            settings.CLIENT_URL,
            settings.IMAGE_SIMILARITY_SERVICE_URL,
            settings.OB_SIMILARITY_SERVICE_URL,
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(image_router, prefix="/api")
    app.include_router(search_router, prefix="/api")

    return app
