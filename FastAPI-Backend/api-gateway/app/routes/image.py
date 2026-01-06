from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from typing import Optional
import requests
from config import settings


image_router = APIRouter()

# SAVE IMAGE - Upload image to S3 and store embeddings in vector database
@image_router.post("/save-image")
async def save_image(
    image: UploadFile = File(...),
    style_number: str = Form(..., description="Style number / layout code of the image"),
    tenant_id: str = Form(..., description="Tenant ID"),
):
    """
    Save an image to S3 and store its embeddings in the vector database.
    
    This endpoint:
    1. Uploads the image to S3 (organized by tenant_id)
    2. Computes CLIP embeddings for the image
    3. Stores the embedding in PostgreSQL with style_number and tenant_id
    
    Args:
        image: The image file to save
        style_number: The style number (also known as layout_code)
        tenant_id: The tenant ID to associate with the image
        
    Returns:
        Success message with image_id and tenant_id
    """
    try:
        image_bytes = await image.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading uploaded file: {str(e)}")

    try:
        files = {
            "image": (image.filename, image_bytes, image.content_type),
        }
        data = {
            "style_number": style_number,
            "tenant_id": tenant_id,
        }

        image_save_url = f"{settings.IMAGE_SIMILARITY_SERVICE_URL}/img/save-image"
        response = requests.post(
            image_save_url,
            files=files,
            data=data,
            timeout=120,
        )
        response.raise_for_status()

        response_data = {
            "message": response.json().get("message"),
            "image_id": response.json().get("image_id"),
            "style_number": style_number,
            "tenant_id": tenant_id,
        }

        return JSONResponse(content=response_data)

    except requests.Timeout:
        raise HTTPException(status_code=504, detail="Image service timed out")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error saving image: {str(e)}")


# SEARCH AND STORE - Find similar images AND store the new image
@image_router.post("/search-and-store")
async def search_and_store(
    image: UploadFile = File(...),
    style_number: str = Form(..., description="Style number / layout code for the new image"),
    tenant_id: str = Form(..., description="Tenant ID for the new image"),
    top_k: int = Form(10, description="Number of similar images to return"),
):
    """
    Upload an image, find similar images, and store the new image with its embeddings.
    
    This endpoint:
    1. Computes CLIP embeddings for the uploaded image
    2. Searches for similar images across ALL tenants
    3. Returns top K similar images with their style_numbers (layout_codes)
    4. Uploads the new image to S3
    5. Stores the embedding in PostgreSQL
    
    Args:
        image: The image file to search and store
        style_number: The style number (layout_code) for the new image
        tenant_id: The tenant ID for the new image
        top_k: Number of similar images to return (default: 10)
        
    Returns:
        Similar images with their details + confirmation of storage
    """
    try:
        image_bytes = await image.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading uploaded file: {str(e)}")

    try:
        files = {
            "image": (image.filename, image_bytes, image.content_type),
        }
        data = {
            "style_number": style_number,
            "tenant_id": tenant_id,
            "top_k": top_k,
        }

        search_store_url = f"{settings.IMAGE_SIMILARITY_SERVICE_URL}/img/search-and-store"
        response = requests.post(
            search_store_url,
            files=files,
            data=data,
            timeout=180,
        )
        response.raise_for_status()

        result = response.json()
        
        response_data = {
            "message": result.get("message"),
            "image_id": result.get("image_id"),
            "style_number": style_number,
            "tenant_id": tenant_id,
            "image_url": result.get("image_url"),
            "similar_images": result.get("similar_images", []),
        }

        return JSONResponse(content=response_data)

    except requests.Timeout:
        raise HTTPException(status_code=504, detail="Image service timed out")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error in search-and-store: {str(e)}")


# DELETE IMAGE
@image_router.delete("/delete-image")
async def delete_image(image_id: int = Form(...)):
    """
    Delete an image by its ID.
    
    This removes both:
    - The image from S3
    - The embedding from the vector database
    """
    try:
        data = {"image_id": image_id}

        image_delete_url = f"{settings.IMAGE_SIMILARITY_SERVICE_URL}/img/delete-image"
        response = requests.delete(image_delete_url, data=data, timeout=60)
        response.raise_for_status()

        return JSONResponse(content={"message": response.json().get("message")})

    except requests.RequestException as e:
        if hasattr(e, 'response') and e.response is not None:
            if e.response.status_code == 404:
                raise HTTPException(status_code=404, detail="Image not found")
        raise HTTPException(status_code=500, detail=f"Error deleting image: {str(e)}")


# UPDATE IMAGE
@image_router.put("/update-image")
async def update_image(
    image: UploadFile = File(...),
    style_number: str = Form(...),
    tenant_id: str = Form(...),
    image_id: int = Form(...),
):
    """
    Update an existing image with a new file.
    
    This:
    - Uploads new image to S3
    - Updates the embedding in the vector database
    - Deletes the old image from S3
    """
    try:
        image_bytes = await image.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading uploaded file: {str(e)}")

    try:
        files = {
            "image": (image.filename, image_bytes, image.content_type),
        }
        data = {
            "style_number": style_number,
            "tenant_id": tenant_id,
            "image_id": image_id,
        }

        image_update_url = f"{settings.IMAGE_SIMILARITY_SERVICE_URL}/img/update-image"
        response = requests.put(
            image_update_url,
            files=files,
            data=data,
            timeout=120,
        )
        response.raise_for_status()

        response_data = {
            "message": response.json().get("message"),
            "image_id": response.json().get("image_id"),
            "style_number": style_number,
            "tenant_id": tenant_id,
        }

        return JSONResponse(content=response_data)

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error updating image: {str(e)}")


# # BACKGROUND REMOVAL
# @image_router.post("/bg-remove")
# async def bg_remove(file: UploadFile = File(...)):
#     """
#     Remove background from an uploaded image.
    
#     Returns the processed image with transparent background as PNG.
#     """
#     try:
#         image_bytes = await file.read()
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f"Error reading uploaded file: {str(e)}")

#     try:
#         files = {
#             "file": (file.filename, image_bytes, file.content_type),
#         }

#         bg_remove_url = f"{settings.IMAGE_SIMILARITY_SERVICE_URL}/img/bg-remove"
#         response = requests.post(bg_remove_url, files=files, timeout=120)
#         response.raise_for_status()

#         image_stream = response.json()["image_bytes"].encode("latin-1")

#         return StreamingResponse(
#             content=iter([image_stream]),
#             media_type="image/png",
#         )

#     except requests.RequestException as e:
#         raise HTTPException(status_code=500, detail=f"Error removing background: {str(e)}")
