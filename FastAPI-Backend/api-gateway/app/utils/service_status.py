import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from config import settings


async def get_service_status():

    service_status = [
        {
            "service_name": "Image Similarity Service",
            "service_status": "DOWN",
            "description": "Service not available",
        },
        {
            "service_name": "OB Similarity Service",
            "service_status": "DOWN",
            "description": "Service not available",
        },
    ]
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.IMAGE_SIMILARITY_SERVICE_URL}/status"
            )
            if response.status_code == 200:
                res = response.json()
                service_status[0]["service_status"] = res["service_status"]
                service_status[0]["description"] = res["description"]

    except Exception as e:
        print(e)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.OB_SIMILARITY_SERVICE_URL}/status")
            if response.status_code == 200:
                res = response.json()
                service_status[1]["service_status"] = res["service_status"]
                service_status[1]["description"] = res["description"]
    except Exception as e:
        print(e)

    return service_status
