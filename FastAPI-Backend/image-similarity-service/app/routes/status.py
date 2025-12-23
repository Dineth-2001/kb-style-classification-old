from fastapi import APIRouter
from fastapi.responses import JSONResponse

status_router = APIRouter()


@status_router.get("/status")
async def index():
    return JSONResponse(
        status_code=200,
        content={
            "service_status": "UP",
            "description": "Sketch similarity search engine is up and running",
        },
    )
