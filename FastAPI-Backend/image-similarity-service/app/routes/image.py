import io
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from PIL import Image

from app.utils.feature_extraction import get_feature_vector_pretrained
from app.utils.s3_handler import upload_to_s3, delete_from_s3
from app.database import pg_connect


image_router = APIRouter()


class ImageSaveForm(BaseModel):
    layout_code: str
    style_type: str
    tenant_id: str


@image_router.post("/save-image")
async def save(
    image: UploadFile = File(...),
    layout_code: str = Form(...),
    style_type: str = Form(...),
    tenant_id: str = Form(...),
):
    """Save uploaded image to S3, compute CLIP embedding, and store in DB.

    Uses CLIP with image_size=224 and stores `feature_vector` as bytes.
    """
    form_data = ImageSaveForm(layout_code=layout_code, style_type=style_type.lower(), tenant_id=tenant_id)

    try:
        image_bytes = await image.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading uploaded file: {e}")

    # upload raw file to S3
    file_name = f"{uuid.uuid4()}.png"
    try:
        image_url = upload_to_s3(image_bytes, file_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading image to S3: {e}")

    try:
        # compute CLIP embedding directly (no preprocessing)
        feature_vector = get_feature_vector_pretrained(image_bytes, i_type=None)
        # upsert to Postgres vector table
        pg_connect.init_table()
        pg_connect.upsert_vector(form_data.tenant_id, form_data.layout_code, form_data.style_type, image_url, feature_vector)
        fvector_id = f"{form_data.tenant_id}:{form_data.layout_code}"
    except Exception as e:
        # try to delete uploaded S3 object on failure
        try:
            delete_from_s3(file_name)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Image saved successfully", "id": str(fvector_id)}


@image_router.delete("/delete-image")
async def delete(tenant_id: str = Form(...), layout_code: str = Form(...)):
    # delete vector row from Postgres and remove S3 object
    try:
        image_url = pg_connect.delete_vector(tenant_id, layout_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error deleting fvector from database: " + str(e))

    if not image_url:
        raise HTTPException(
            status_code=404,
            detail="No image found with the given layout code and tenant id",
        )

    try:
        image_key = image_url.split("/")[-1]
        delete_from_s3(image_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error deleting image from s3: " + str(e))

    return {"message": "Image and fvector deleted successfully"}


@image_router.put("/update-image")
async def update_image(
    image: UploadFile = File(...),
    layout_code: str = Form(...),
    style_type: str = Form(...),
    tenant_id: str = Form(...),
):
    try:
        image_bytes = await image.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading uploaded file: {e}")

    file_name = f"{uuid.uuid4()}.png"
    try:
        image_url = upload_to_s3(image_bytes, file_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading image to S3: {e}")

    try:
        feature_vector = get_feature_vector_pretrained(image_bytes, i_type=None)
        # upsert to Postgres
        pg_connect.init_table()
        pg_connect.upsert_vector(tenant_id, layout_code, style_type.lower(), image_url, feature_vector)
        object_id = f"{tenant_id}:{layout_code}"
        # try to extract old image URL to delete
        old_image_url = None
        try:
            # attempt to find old image by querying Postgres
            rows = pg_connect.fetch_vectors(None)
            for r in rows:
                if r['tenant_id'] == tenant_id and r['layout_code'] == layout_code:
                    old_image_url = r.get('image_url')
                    break
        except Exception:
            old_image_url = None

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    try:
        image_key = old_image_url.split("/")[-1]
        delete_from_s3(image_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error deleting old image from s3: " + str(e))

    return {"message": "Image updated successfully", "id": str(object_id)}
