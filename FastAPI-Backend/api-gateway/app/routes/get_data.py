from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import httpx
from config import settings


get_data_router = APIRouter()


@get_data_router.get("/get-style-types/{tenant_id}")
async def get_styles(tenant_id: int):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.OB_SIMILARITY_SERVICE_URL}/ob/get-style-types/{tenant_id}"
            )
            response.raise_for_status()
            data = response.json()
            return JSONResponse(content=data)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail=str(exc))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
