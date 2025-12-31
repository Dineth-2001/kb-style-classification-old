import io
import uuid
import base64
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from PIL import Image
from typing import List, Optional

from app.utils.feature_extraction import get_feature_vector_pretrained
from app.utils.s3_handler import upload_to_s3, delete_from_s3, get_image_by_tenant_id
from app.database import pg_connect


image_router = APIRouter()


class ImageSaveForm(BaseModel):
    style_number: str
    tenant_id: str


@image_router.post("/save-image")
async def save(
    image: UploadFile = File(...),
    style_number: str = Form(...),
    tenant_id: str = Form(...),
):
    """Save uploaded image to S3, compute CLIP embedding, and store in DB.

    Uses CLIP with image_size=224 and stores `feature_vector` as bytes.
    """
    form_data = ImageSaveForm(style_number=style_number, tenant_id=tenant_id)

    try:
        image_bytes = await image.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading uploaded file: {e}")

    # upload raw file to S3 with tenant_id prefix 
    file_name = f"{form_data.tenant_id}/{uuid.uuid4()}.png"
    try:
        image_url = upload_to_s3(image_bytes, file_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading image to S3: {e}")

    try:
        # compute CLIP embedding directly (no preprocessing)
        feature_vector = get_feature_vector_pretrained(image_bytes, i_type=None)
        # upsert to Postgres vector table
        pg_connect.init_table()
        pg_connect.upsert_vector(form_data.tenant_id, form_data.style_number, image_url, feature_vector)
    except Exception as e:
        # try to delete uploaded S3 object on failure
        try:
            delete_from_s3(file_name)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=str(e))

    return {"message": "Image saved successfully", "id": form_data.tenant_id}


@image_router.delete("/delete-image")
async def delete(tenant_id: str = Form(...)):
    # delete vector row from Postgres and remove S3 object
    try:
        image_url = pg_connect.delete_vector(tenant_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error deleting fvector from database: " + str(e))

    if not image_url:
        raise HTTPException(
            status_code=404,
            detail="No image found with the given tenant id",
        )

    try:
        # Extract full S3 key from URL 
        # URL format: https://bucket.s3.amazonaws.com/tenant_id/uuid.png
        from app.utils.s3_handler import BUCKET_NAME
        image_key = image_url.split(f"{BUCKET_NAME}.s3.amazonaws.com/")[-1]
        delete_from_s3(image_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail="Error deleting image from s3: " + str(e))

    return {"message": "Image and fvector deleted successfully"}


@image_router.put("/update-image")
async def update_image(
    image: UploadFile = File(...),
    style_number: str = Form(...),
    tenant_id: str = Form(...),
):
    try:
        image_bytes = await image.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading uploaded file: {e}")

    # Get old image URL before update
    old_image_url = None
    try:
        rows = pg_connect.fetch_vectors(tenant_id=tenant_id)
        if rows:
            old_image_url = rows[0].get('image_url')
    except Exception:
        pass

    # Upload new image with tenant_id prefix
    file_name = f"{tenant_id}/{uuid.uuid4()}.png"
    try:
        image_url = upload_to_s3(image_bytes, file_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading image to S3: {e}")

    try:
        feature_vector = get_feature_vector_pretrained(image_bytes, i_type=None)
        # upsert to Postgres
        pg_connect.init_table()
        pg_connect.upsert_vector(tenant_id, style_number, image_url, feature_vector)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Delete old image from S3
    if old_image_url:
        try:
            # Extract full S3 key from URL
            from app.utils.s3_handler import BUCKET_NAME
            image_key = old_image_url.split(f"{BUCKET_NAME}.s3.amazonaws.com/")[-1]
            delete_from_s3(image_key)
        except Exception:
            pass  

    return {"message": "Image updated successfully", "id": tenant_id}

class SimilarImageResult(BaseModel):
    """Response model for similar images."""
    tenant_id: str
    style_number: str
    image_url: str
    similarity: float
    image_base64: Optional[str] = None


class SearchAndStoreResponse(BaseModel):
    """Response model for search-and-store endpoint."""
    message: str
    uploaded_tenant_id: str
    image_url: str
    similar_images: List[SimilarImageResult]


@image_router.post("/upload-image")
async def upload_image_only(
    image: UploadFile = File(...),
    tenant_id: str = Form(...),
):
    """
    Upload an image to S3 bucket organized by tenant_id.
    This endpoint ONLY uploads to S3 - no embedding or database storage.
    
    Args:
        image: The image file to upload
        tenant_id: The tenant ID to associate with the image
        
    Returns:
        Success message with S3 URL
    """
    try:
        image_bytes = await image.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading uploaded file: {e}")

    # Create filename with tenant_id prefix for organization
    file_extension = image.filename.split('.')[-1] if '.' in image.filename else 'png'
    file_name = f"{tenant_id}/{uuid.uuid4()}.{file_extension}"
    
    try:
        image_url = upload_to_s3(image_bytes, file_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading image to S3: {e}")

    return {
        "message": "Image uploaded successfully to S3",
        "tenant_id": tenant_id,
        "image_url": image_url
    }


@image_router.post("/search-and-store", response_model=SearchAndStoreResponse)
async def search_and_store(
    image: UploadFile = File(...),
    style_number: str = Form(...),
    tenant_id: str = Form(...),
    top_k: int = Form(10),
):
    """
    Search for similar images across ALL tenants, then store the submitted image.
    
    This endpoint:
    1. Embeds the uploaded image using CLIP
    2. Searches for similar images across ALL tenant embeddings using cosine similarity
    3. Returns top K similar images with base64 encoded data
    4. Uploads the submitted image to S3 (organized by tenant_id)
    5. Stores the embedding in PostgreSQL with the tenant_id
    
    Args:
        image: The image file to search and store
        style_type: The style type/category of the image
        tenant_id: The tenant ID to associate with the stored image
        top_k: Number of similar images to return (default: 10)
        
    Returns:
        List of similar images and confirmation of storage
    """
    try:
        image_bytes = await image.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading uploaded file: {e}")

    # Compute CLIP embedding for the uploaded image
    try:
        feature_vector = get_feature_vector_pretrained(image_bytes, i_type=None)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting features: {e}")

    # Search for similar images across ALL tenants
    try:
        pg_connect.init_table()
        similar_results = pg_connect.search_similar_vectors(
            query_vector=feature_vector,
            top_k=top_k
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching for similar images: {e}")

    # Fetch base64 images for similar results
    similar_images = []
    for result in similar_results:
        image_base64 = None
        try:
            s3_image_bytes = get_image_by_tenant_id(result['tenant_id'])
            if s3_image_bytes:
                image_base64 = base64.b64encode(s3_image_bytes).decode('utf-8')
        except Exception:
            pass  # Continue even if we can't fetch the image

        similar_images.append(SimilarImageResult(
            tenant_id=result['tenant_id'],
            style_number=result.get('style_number', ''),
            image_url=result.get('image_url', ''),
            similarity=result.get('similarity', 0.0),
            image_base64=image_base64
        ))

    # Upload the submitted image to S3
    file_extension = image.filename.split('.')[-1] if '.' in image.filename else 'png'
    file_name = f"{tenant_id}/{uuid.uuid4()}.{file_extension}"
    
    try:
        image_url = upload_to_s3(image_bytes, file_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading image to S3: {e}")

    # Store the embedding in PostgreSQL
    try:
        pg_connect.upsert_vector(tenant_id, style_number, image_url, feature_vector)
    except Exception as e:
        # Try to clean up S3 on failure
        try:
            delete_from_s3(file_name)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Error storing embedding in database: {e}")

    return SearchAndStoreResponse(
        message="Image searched, stored in S3, and embedding saved to database successfully",
        uploaded_tenant_id=tenant_id,
        image_url=image_url,
        similar_images=similar_images
    )
