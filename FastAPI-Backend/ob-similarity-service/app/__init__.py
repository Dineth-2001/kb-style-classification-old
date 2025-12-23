from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from app.database.db_connect import database
import logging as log

ALLOWED_ORIGINS = [settings.CLIENT_URL]


def create_app():
    app = FastAPI(
        title="OB Similarity API", version="0.1.0", description="API for OB similarity"
    )

    # Connect to the database when the application starts
    @app.on_event("startup")
    async def startup():
        await database.connect()
        log.basicConfig(level=log.INFO, format="%(asctime)s:    %(message)s")
        log.info("Connected to Database")
        # print("--- Connected to Database ---")

    @app.on_event("shutdown")
    async def shutdown():
        await database.disconnect()
        # print("--- Disconnected from Database ---")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        # allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app
