from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import requests
from config import settings


image_router = APIRouter()


# define pydantic models
class ImageSaveForm(BaseModel):
    layout_code: str
    style_type: str
    tenant_id: str
    image_orientation: str


@image_router.post("/save-image")
async def save(
    image_front: UploadFile = File(...),
    image_back: UploadFile = File(...),
    layout_code: str = Form(...),
    style_type: str = Form(...),
    tenant_id: str = Form(...),
    image_orientation: str = Form(...),
):

    form_data = ImageSaveForm(
        layout_code=layout_code,
        style_type=style_type.lower(),
        tenant_id=tenant_id,
        image_orientation=image_orientation.lower(),
    )

    try:
        image_front_bytes = await image_front.read()
        image_back_bytes = await image_back.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail="Error reading uploaded files")

    try:
        files = {
            "image_front": (
                image_front.filename,
                image_front_bytes,
                image_front.content_type,
            ),
            "image_back": (
                image_back.filename,
                image_back_bytes,
                image_back.content_type,
            ),
        }

        data = {
            "layout_code": form_data.layout_code,
            "style_type": form_data.style_type,
            "tenant_id": form_data.tenant_id,
            "image_orientation": form_data.image_orientation,
        }

        image_save_url = f"{settings.IMAGE_SIMILARITY_SERVICE_URL}/img/save-image"
        response = requests.post(
            image_save_url,
            files=files,
            data=data,
        )
        response.raise_for_status()

        response_data = {
            "message": response.json().get("message"),
            "image_id": response.json().get("id"),
            "layout_code": form_data.layout_code,
            "style_type": style_type,
            "tenant_id": form_data.tenant_id,
        }

        return JSONResponse(content=response_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error saving images: " + str(e))


@image_router.put("/update-image")
async def update_image(
    image_front: UploadFile = File(...),
    image_back: UploadFile = File(...),
    layout_code: str = Form(...),
    style_type: str = Form(...),
    tenant_id: str = Form(...),
    image_orientation: str = Form(...),
):
    try:
        image_front_bytes = await image_front.read()
        image_back_bytes = await image_back.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail="Error reading uploaded files")

    try:
        files = {
            "image_front": (
                image_front.filename,
                image_front_bytes,
                image_front.content_type,
            ),
            "image_back": (
                image_back.filename,
                image_back_bytes,
                image_back.content_type,
            ),
        }

        data = {
            "layout_code": layout_code,
            "style_type": style_type,
            "tenant_id": tenant_id,
            "image_orientation": image_orientation,
        }

        image_update_url = f"{settings.IMAGE_SIMILARITY_SERVICE_URL}/img/update-image"
        response = requests.put(
            image_update_url,
            files=files,
            data=data,
        )
        response.raise_for_status()

        response_data = {
            "message": response.json().get("message"),
            "image_id": response.json().get("id"),
            "layout_code": layout_code,
            "style_type": style_type,
            "tenant_id": tenant_id,
        }

        return JSONResponse(content=response_data)

    except Exception as e:
        raise HTTPException(status_code=500, detail="Error updating images: " + str(e))


@image_router.delete("/delete-image")
async def delete_image(tenant_id: str = Form(...), layout_code: str = Form(...)):
    try:
        data = {
            "tenant_id": tenant_id,
            "layout_code": layout_code,
        }

        image_delete_url = f"{settings.IMAGE_SIMILARITY_SERVICE_URL}/img/delete-image"
        response = requests.delete(image_delete_url, data=data)
        response.raise_for_status()

        response_data = {
            "message": response.json().get("message"),
        }

        return JSONResponse(content=response_data)

    except Exception as e:
        if response.status_code == 404 and response.json().get("detail"):
            raise HTTPException(
                status_code=404,
                detail=str(response.json().get("detail")),
            )
        else:
            raise HTTPException(
                status_code=500, detail="Error deleting images: " + str(e)
            )


@image_router.post("/bg-remove")
async def bg_remove(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
    except Exception as e:
        raise HTTPException(
            status_code=400, detail="Error reading uploaded file: " + str(e)
        )

    try:
        files = {
            "file": (
                file.filename,
                image_bytes,
                file.content_type,
            ),
        }

        bg_remove_url = f"{settings.IMAGE_SIMILARITY_SERVICE_URL}/img/bg-remove"
        response = requests.post(
            bg_remove_url,
            files=files,
        )
        response.raise_for_status()

        image_stream = response.json()["image_bytes"].encode("latin-1")

        return StreamingResponse(
            content=iter([image_stream]),
            media_type="image/png",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Error removing background: " + str(e)
        )
