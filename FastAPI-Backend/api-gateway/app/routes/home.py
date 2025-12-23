from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.utils.service_status import get_service_status


home_router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@home_router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    service_status = await get_service_status()

    return templates.TemplateResponse(
        "index.html", {"request": request, "service_status": service_status}
    )
