from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse


save_router = APIRouter()


@save_router.post("/save")
async def save():
    return JSONResponse(content={"message": "Save API"})
