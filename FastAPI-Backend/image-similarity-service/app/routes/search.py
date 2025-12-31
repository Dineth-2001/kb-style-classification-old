import io
import time
import json
import base64
from typing import List, Optional
import numpy as np
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.utils.feature_extraction import get_feature_vector_pretrained
from app.utils.s3_handler import list_images_from_s3, download_from_s3, download_from_s3_url, get_image_by_tenant_id
from app.utils.embedding_extractor import compute_clip_embedding
from app.database import pg_connect


class SearchResponse(BaseModel):
    tenant_id: str
    style_number: Optional[str] = None
    image_url: str
    similarity_score: float
    rank: int


class SimilarImageResponse(BaseModel):
    """Response model for similar images with full image data"""
    tenant_id: str
    style_number: Optional[str] = None
    image_url: str
    similarity_score: float
    rank: int
    image_base64: Optional[str] = None  # Base64 encoded image data


class EmbeddingCreationResponse(BaseModel):
    status: str
    message: str
    processed_count: int
    failed_count: int
    details: List[dict] = []


router = APIRouter()
search_router = router  # Alias for backward compatibility


@router.post('/find-similar-tenants', response_model=List[SimilarImageResponse])
async def find_similar_tenants(
    image: UploadFile = File(...),
    top_k: int = Form(10),
    style_number: Optional[str] = Form(None),
    include_image_data: bool = Form(False)
):
    """
    Find similar tenant images by uploading a new image.

    1. Takes an uploaded image
    2. Creates an embedding for it using CLIP
    3. Compares with ALL stored embeddings using cosine similarity
    4. Finds the top K most similar tenant IDs
    5. Fetches the images from S3 for those tenant IDs
    6. Returns the images along with similarity scores
    
    Args:
        image: The uploaded image file to search with
        top_k: Number of top similar tenant results to return (default: 10)
        style_type: Optional style type to filter results
        include_image_data: If True, includes base64 encoded image data in response
        
    Returns:
        List of similar tenant images with similarity scores, ranked by similarity.
        Includes the actual image bytes (base64 encoded)
    """
    start_time = time.time()
    
    try:
        # Read uploaded image data
        data = await image.read()
        
        # Compute embedding for the uploaded image using CLIP
        query_vec = get_feature_vector_pretrained(data, 'clip')
        
        # Search across ALL tenants for similar images using cosine similarity
        results = pg_connect.search_similar_vectors(
            query_vector=query_vec,
            top_k=top_k,
            style_number=style_number,
            exclude_tenant_id=None  # Don't exclude any tenant
        )
        
        if not results:
            return []
        
        # Build response with images fetched from S3
        response = []
        for r in results:
            tenant_id = r['tenant_id']
            image_url = r['image_url']
            
            # Optionally fetch image from S3 and encode as base64
            image_base64 = None
            if include_image_data:
                try:
                    # Fetch image from S3 using the stored URL
                    image_bytes = download_from_s3_url(image_url)
                    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                except Exception as e:
                    # If fetching fails, try using tenant_id to find image
                    try:
                        image_bytes = get_image_by_tenant_id(tenant_id)
                        if image_bytes:
                            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
                    except Exception:
                        pass  # Continue without image data
            
            response.append(SimilarImageResponse(
                tenant_id=tenant_id,
                style_number=r.get('style_number'),
                image_url=image_url,
                similarity_score=r['similarity_score'],
                rank=r['rank'],
                image_base64=image_base64
            ))
        
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error finding similar tenants: {str(e)}")


@router.post('/search-image', response_model=List[SearchResponse])
async def search_image(
    image: UploadFile = File(...),
    top_k: int = Form(10),
    style_number: Optional[str] = Form(None)
):
    """
    Search for similar images using the provided image file.
    
    Uses cosine similarity to compare the uploaded image's embedding with stored embeddings
    across ALL tenants.
    
    Args:
        image: The uploaded image file to search with
        top_k: Number of top similar results to return (default: 10)
        style_type: Optional style type to filter results
        
    Returns:
        List of similar images with similarity scores, ranked by similarity
    """
    try:
        # Read uploaded image data
        data = await image.read()
        
        # Compute embedding for the uploaded image using CLIP
        query_vec = get_feature_vector_pretrained(data, 'clip')
        
        # Search across ALL tenants using cosine similarity
        results = pg_connect.search_similar_vectors(
            query_vector=query_vec,
            top_k=top_k,
            style_number=style_number
        )
        
        if not results:
            return []
        
        # Convert to response model
        response = [
                SearchResponse(
                    tenant_id=r['tenant_id'],
                    style_number=r.get('style_number'),
                    image_url=r['image_url'],
                    similarity_score=r['similarity_score'],
                    rank=r['rank']
                )
                for r in results
            ]
        
        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching images: {str(e)}")


# @router.post('/search-by-url', response_model=List[SearchResponse])
# async def search_by_url(
#     image_url: str = Form(...),
#     top_k: int = Form(10),
#     style_number: Optional[str] = Form(None)
# ):
#     """
#     Search for similar images using an image URL (S3 or external).
    
#     Downloads the image from the URL, computes its embedding, and searches for similar images
#     across ALL tenants.
    
#     Args:
#         image_url: URL of the image to search with
#         top_k: Number of top similar results to return (default: 10)
#         style_type: Optional style type to filter results
        
#     Returns:
#         List of similar images with similarity scores, ranked by similarity
#     """
#     try:
#         # Download image from URL
#         try:
#             image_data = download_from_s3_url(image_url)
#         except Exception:
#             # If not an S3 URL, try downloading as external URL
#             import requests
#             response = requests.get(image_url, timeout=30)
#             response.raise_for_status()
#             image_data = response.content
        
#         # Compute embedding for the image
#         query_vec = compute_clip_embedding(image_data)
        
#         # Search for similar vectors across ALL tenants
#         results = pg_connect.search_similar_vectors(
#             query_vector=query_vec,
#             top_k=top_k,
#             style_number=style_number
#         )
        
#         if not results:
#             return []
        
#         # Convert to response model
#         response = [
#             SearchResponse(
#                 tenant_id=r['tenant_id'],
#                 style_type=r.get('style_type'),
#                 image_url=r['image_url'],
#                 similarity_score=r['similarity_score'],
#                 rank=r['rank']
#             )
#             for r in results
#         ]
        
#         return response

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error searching images: {str(e)}")


@router.post('/create-embeddings-from-s3', response_model=EmbeddingCreationResponse)
async def create_embeddings_from_s3(
    tenant_id: Optional[str] = Form(None),
    prefix: str = Form(""),
    limit: int = Form(0)
):
    """
    Fetch images from S3, compute their embeddings, and store them in the vector database.
    
    This endpoint scans S3 for images under the specified prefix,
    computes CLIP embeddings for each image, and stores them in PostgreSQL with pgvector.
    
    Args:
        tenant_id: Optional tenant ID - if provided, only processes images for that tenant.
                   If omitted, processes ALL images in the bucket.
        prefix: Optional S3 prefix to filter objects
        limit: Maximum number of images to process (0 = all)
        
    Returns:
        Status of the embedding creation process
    """
    try:
        # Initialize the database table
        pg_connect.init_table()
        
        # List images from S3 (all images if tenant_id is None)
        images = list_images_from_s3(prefix=prefix, tenant_id=tenant_id)
        
        if not images:
            message = "No images found" if not tenant_id else f"No images found for tenant {tenant_id}"
            return EmbeddingCreationResponse(
                status="success",
                message=message,
                processed_count=0,
                failed_count=0,
                details=[]
            )
        
        # Apply limit if specified
        if limit > 0:
            images = images[:limit]
        
        processed_count = 0
        failed_count = 0
        details = []
        vectors_to_insert = []
        
        for img_info in images:
            try:
                # Download image from S3
                image_data = download_from_s3(img_info['key'])
                
                # Compute CLIP embedding
                embedding = compute_clip_embedding(image_data, image_size=224)
                
                # Prepare vector data for bulk insert
                vectors_to_insert.append({
                    'tenant_id': img_info['tenant_id'],
                    'style_type': img_info.get('style_type', ''),
                    'image_url': img_info['url'],
                    'feature_vector': embedding
                })
                
                processed_count += 1
                details.append({
                    'key': img_info['key'],
                    'status': 'success'
                })
                
            except Exception as e:
                failed_count += 1
                details.append({
                    'key': img_info['key'],
                    'status': 'failed',
                    'error': str(e)
                })
        
        # Bulk insert all vectors
        if vectors_to_insert:
            pg_connect.bulk_upsert_vectors(vectors_to_insert)
        
        return EmbeddingCreationResponse(
            status="success",
            message=f"Processed {processed_count} images, {failed_count} failed",
            processed_count=processed_count,
            failed_count=failed_count,
            details=details
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating embeddings: {str(e)}")


# @router.post('/create-all-embeddings', response_model=EmbeddingCreationResponse)
# async def create_all_embeddings(
#     prefix: str = Form(""),
#     limit: int = Form(0),
#     skip_existing: bool = Form(True)
# ):
#     """
#     Create embeddings for ALL images in the S3 bucket.
    
#     This endpoint scans the entire S3 bucket (or a prefix), finds all images,
#     computes CLIP embeddings for each, and stores them in PostgreSQL.
    
#     Args:
#         prefix: Optional S3 prefix to filter objects (e.g., 'images/')
#         limit: Maximum number of images to process (0 = all)
#         skip_existing: If True, skip images that already have embeddings in DB (default: True)
        
#     Returns:
#         Status of the embedding creation process with details
#     """
#     try:
#         # Initialize the database table
#         pg_connect.init_table()
        
#         # List ALL images from S3
#         images = list_images_from_s3(prefix=prefix)
        
#         if not images:
#             return EmbeddingCreationResponse(
#                 status="success",
#                 message="No images found in S3 bucket",
#                 processed_count=0,
#                 failed_count=0,
#                 details=[]
#             )
        
#         # Get existing tenant_ids if skip_existing is True
#         existing_tenant_ids = set()
#         if skip_existing:
#             try:
#                 existing_vectors = pg_connect.fetch_vectors()
#                 existing_tenant_ids = {v['tenant_id'] for v in existing_vectors}
#             except Exception:
#                 pass  # If fetch fails, process all
        
#         # Filter out existing if needed
#         if skip_existing and existing_tenant_ids:
#             original_count = len(images)
#             images = [img for img in images if img['tenant_id'] not in existing_tenant_ids]
#             skipped_count = original_count - len(images)
#         else:
#             skipped_count = 0
        
#         # Apply limit if specified
#         if limit > 0:
#             images = images[:limit]
        
#         processed_count = 0
#         failed_count = 0
#         details = []
#         vectors_to_insert = []
        
#         for img_info in images:
#             try:
#                 # Download image from S3
#                 image_data = download_from_s3(img_info['key'])
                
#                 # Compute CLIP embedding
#                 embedding = compute_clip_embedding(image_data, image_size=224)
                
#                 # Prepare vector data for bulk insert
#                 vectors_to_insert.append({
#                     'tenant_id': img_info['tenant_id'],
#                     'style_type': img_info.get('style_type', ''),
#                     'image_url': img_info['url'],
#                     'feature_vector': embedding
#                 })
                
#                 processed_count += 1
#                 details.append({
#                     'key': img_info['key'],
#                     'tenant_id': img_info['tenant_id'],
#                     'status': 'success'
#                 })
                
#             except Exception as e:
#                 failed_count += 1
#                 details.append({
#                     'key': img_info['key'],
#                     'tenant_id': img_info.get('tenant_id', 'unknown'),
#                     'status': 'failed',
#                     'error': str(e)
#                 })
        
#         # Bulk insert all vectors
#         if vectors_to_insert:
#             pg_connect.bulk_upsert_vectors(vectors_to_insert)
        
#         message = f"Processed {processed_count} images, {failed_count} failed"
#         if skipped_count > 0:
#             message += f", {skipped_count} skipped (already exist)"
        
#         return EmbeddingCreationResponse(
#             status="success",
#             message=message,
#             processed_count=processed_count,
#             failed_count=failed_count,
#             details=details
#         )
        
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error creating embeddings: {str(e)}")


@router.get('/list-s3-images')
async def list_s3_images(
    tenant_id: str = Query(...),
    prefix: str = Query("")
):
    """
    List all images in S3 for a specific tenant.
    
    Args:
        tenant_id: The tenant ID to filter images
        prefix: Optional S3 prefix
        
    Returns:
        List of images with their metadata
    """
    try:
        images = list_images_from_s3(prefix=prefix, tenant_id=tenant_id)
        return {
            "status": "success",
            "count": len(images),
            "images": images
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing images: {str(e)}")


@router.get('/embedding-stats')
async def get_embedding_stats(tenant_id: Optional[str] = Query(None)):
    """
    Get statistics about stored embeddings.
    
    Args:
        tenant_id: Optional tenant ID to filter stats
        
    Returns:
        Count of embeddings and other stats
    """
    try:
        total_count = pg_connect.get_vector_count()
        tenant_count = pg_connect.get_vector_count(tenant_id) if tenant_id else None
        
        return {
            "status": "success",
            "total_embeddings": total_count,
            "tenant_embeddings": tenant_count,
            "tenant_id": tenant_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting stats: {str(e)}")
