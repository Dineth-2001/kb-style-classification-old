import json
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional
from config import settings
import requests

search_router = APIRouter()


class OperationData(BaseModel):
    operation_name: str
    machine_name: str
    sequence_number: int


# GET OB BY LAYOUT CODE - Fetch OB data using tenant_id and style_number
@search_router.get("/get-ob/{tenant_id}/{style_number}")
async def get_ob_by_style_number(tenant_id: int, style_number: str):
    """
    Fetch OB data for a specific style_number (layout_code).
    
    This endpoint retrieves the Operation Bulletin for a given tenant and style_number.
    The style_number is the same as layout_code in the database.
    
    Args:
        tenant_id: The tenant ID
        style_number: The style number (also known as layout_code)
        
    Returns:
        OB data including operation_data (list of operations with machine names and sequences)
    """
    try:
        ob_url = f"{settings.OB_SIMILARITY_SERVICE_URL}/ob/get-ob-by-layout/{tenant_id}/{style_number}"
        response = requests.get(ob_url, timeout=60)
        
        if response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"No OB found for tenant_id={tenant_id} and style_number={style_number}"
            )
        
        response.raise_for_status()
        return JSONResponse(content=response.json())

    except requests.Timeout:
        raise HTTPException(status_code=504, detail="OB service timed out")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching OB: {str(e)}")


# 2. GET MULTIPLE OBs - Fetch OBs for multiple style_numbers at once
@search_router.post("/get-obs")
async def get_multiple_obs(
    tenant_id: str = Form(...),
    style_numbers: str = Form(..., description="JSON array of style_numbers: [\"style1\", \"style2\"]"),
):
    """
    Fetch OB data for multiple style_numbers at once.
    
    This is useful after finding similar images - you can fetch all their OBs in one call.
    
    Args:
        tenant_id: The tenant ID
        style_numbers: JSON array of style_numbers to fetch OBs for
        
    Returns:
        List of OB data for each style_number
    """
    try:
        style_number_list = json.loads(style_numbers)
        if not isinstance(style_number_list, list):
            raise HTTPException(status_code=400, detail="style_numbers must be a JSON array")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON for style_numbers")

    results = []
    for style_number in style_number_list:
        try:
            ob_url = f"{settings.OB_SIMILARITY_SERVICE_URL}/ob/get-ob-by-layout/{tenant_id}/{style_number}"
            response = requests.get(ob_url, timeout=30)
            
            if response.status_code == 200:
                ob_data = response.json()
                ob_data["style_number"] = style_number
                results.append(ob_data)
            else:
                results.append({
                    "style_number": style_number,
                    "error": "OB not found",
                    "ob_data": None
                })
        except Exception as e:
            results.append({
                "style_number": style_number,
                "error": str(e),
                "ob_data": None
            })

    return JSONResponse(content={
        "tenant_id": tenant_id,
        "total_requested": len(style_number_list),
        "total_found": len([r for r in results if "error" not in r]),
        "obs": results
    })


# COMPARE OB - Compare user's OB with existing OBs
@search_router.post("/compare-ob")
async def compare_ob(
    tenant_id: str = Form(...),
    style_type: str = Form(..., description="Style type to search within"),
    operation_data: str = Form(..., description="JSON array of user's OB operations"),
    no_of_results: int = Form(10, description="Number of similar OBs to return"),
    allocation_data: bool = Form(False, description="Include allocation data in results"),
    no_of_allocations: int = Form(5, description="Number of allocations to include per result"),
):
    """
    Compare a user-created OB with existing OBs to find similarity scores.

    1. Takes the user's new OB 
    2. Compares it against all existing OBs of the same style_type
    3. Returns ranked results based on similarity score
    
    Args:
        tenant_id: The tenant ID
        style_type: The style type to search within (e.g., "LADIES BRIEF - TEZENIS BEACHWEAR")
        operation_data: JSON array of operations: [{"operation_name": "...", "machine_name": "...", "sequence_number": 1}]
        no_of_results: Number of similar OBs to return (default: 10)
        allocation_data: Whether to include allocation data (default: False)
        no_of_allocations: Number of allocations per result (default: 5)
        
    Returns:
        Ranked list of similar OBs with similarity scores
    """
    try:
        ops_parsed = json.loads(operation_data)
        if not isinstance(ops_parsed, list):
            raise HTTPException(status_code=400, detail="operation_data must be a JSON array")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON for operation_data")

    request_data = {
        "tenant_id": int(tenant_id),
        "style_type": style_type,
        "allocation_data": allocation_data,
        "no_of_results": no_of_results,
        "no_of_allocations": no_of_allocations,
        "operation_data": ops_parsed,
    }

    try:
        ob_search_url = f"{settings.OB_SIMILARITY_SERVICE_URL}/ob/search"
        response = requests.post(
            ob_search_url,
            json=request_data,
            timeout=360,
        )
        response.raise_for_status()
        
        result = response.json()
        
        response_data = {
            "message": "OB comparison completed",
            "tenant_id": tenant_id,
            "style_type": style_type,
            "total_obs_compared": result.get("total_obs"),
            "no_of_results": result.get("no_of_results"),
            "process_time": result.get("process_time"),
            "similar_obs": result.get("results", []),
        }
        
        return JSONResponse(content=response_data)

    except requests.Timeout:
        raise HTTPException(status_code=504, detail="OB similarity service timed out")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error comparing OBs: {str(e)}")


# COMPARE OB WITH SPECIFIC LAYOUT CODES - Compare with OBs of similar images only
@search_router.post("/compare-ob-filtered")
async def compare_ob_filtered(
    tenant_id: str = Form(...),
    style_type: str = Form(...),
    operation_data: str = Form(..., description="JSON array of user's OB operations"),
    layout_codes: str = Form(..., description="JSON array of layout_codes to compare against"),
):
    """
    Compare user's OB with specific OBs (filtered by layout_codes).
    
    Use this after finding similar images to compare your new OB only against
    the OBs of those similar images.
    
    Args:
        tenant_id: The tenant ID
        style_type: The style type
        operation_data: JSON array of user's operations
        layout_codes: JSON array of layout_codes to filter results (e.g., from similar images)
        
    Returns:
        Filtered and ranked OB comparison results
    """
    try:
        ops_parsed = json.loads(operation_data)
        codes_parsed = json.loads(layout_codes)
        if not isinstance(ops_parsed, list) or not isinstance(codes_parsed, list):
            raise HTTPException(status_code=400, detail="Both operation_data and layout_codes must be JSON arrays")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON format")

    request_data = {
        "tenant_id": int(tenant_id),
        "style_type": style_type,
        "allocation_data": False,
        "no_of_results": 100,  # Get more results to filter
        "no_of_allocations": 3,
        "operation_data": ops_parsed,
    }

    try:
        ob_search_url = f"{settings.OB_SIMILARITY_SERVICE_URL}/ob/search"
        response = requests.post(
            ob_search_url,
            json=request_data,
            timeout=360,
        )
        response.raise_for_status()
        result = response.json()
        
        # Filter results to only include specified layout_codes
        all_results = result.get("results", [])
        filtered_results = [
            r for r in all_results 
            if r.get("layout_code") in codes_parsed
        ]
        
        return JSONResponse(content={
            "message": "Filtered OB comparison completed",
            "tenant_id": tenant_id,
            "style_type": style_type,
            "total_compared": len(filtered_results),
            "similar_obs": filtered_results,
        })

    except requests.Timeout:
        raise HTTPException(status_code=504, detail="OB similarity service timed out")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error comparing OBs: {str(e)}")


# FULL WORKFLOW - Search images, get OBs, and compare
@search_router.post("/search-images-with-obs")
async def search_images_with_obs(
    image: UploadFile = File(...),
    tenant_id: str = Form(...),
    style_number: str = Form(..., description="Style number for the new image"),
    top_k: int = Form(10, description="Number of similar images to return"),
    store_image: bool = Form(True, description="Whether to store the new image"),
):
    """
    Complete workflow: Search for similar images and fetch their OBs.
    
    This endpoint:
    1. Uploads the new image
    2. Finds similar images across all tenants
    3. Optionally stores the new image with its embeddings
    4. For each similar image, fetches its OB using the style_number (layout_code)
    5. Returns combined results
    
    Args:
        image: The image file to search with
        tenant_id: Tenant ID for the new image
        style_number: Style number (layout_code) for the new image
        top_k: Number of similar images to return (default: 10)
        store_image: Whether to store the new image (default: True)
        
    Returns:
        Similar images with their OB data
    """
    try:
        image_bytes = await image.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading image: {str(e)}")

    # Search (and optionally store) the image
    try:
        files = {"image": (image.filename, image_bytes, image.content_type)}
        
        if store_image:
            # Use search-and-store endpoint
            data = {
                "style_number": style_number,
                "tenant_id": tenant_id,
                "top_k": top_k,
            }
            img_url = f"{settings.IMAGE_SIMILARITY_SERVICE_URL}/img/search-and-store"
        else:
            # Use find-similar-tenants endpoint (search only)
            data = {"top_k": top_k}
            img_url = f"{settings.IMAGE_SIMILARITY_SERVICE_URL}/search/find-similar-tenants"
        
        response = requests.post(img_url, files=files, data=data, timeout=180)
        response.raise_for_status()
        img_result = response.json()

    except requests.Timeout:
        raise HTTPException(status_code=504, detail="Image service timed out")
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error searching images: {str(e)}")

    # Extract similar images
    if store_image:
        similar_images = img_result.get("similar_images", [])
        new_image_id = img_result.get("image_id")
        new_image_url = img_result.get("image_url")
    else:
        similar_images = img_result if isinstance(img_result, list) else []
        new_image_id = None
        new_image_url = None

    # Fetch OBs for each similar image
    results_with_ob = []
    for sim_img in similar_images:
        img_tenant_id = sim_img.get("tenant_id")
        img_style_number = sim_img.get("style_number")
        
        ob_data = None
        if img_style_number:
            try:
                ob_url = f"{settings.OB_SIMILARITY_SERVICE_URL}/ob/get-ob-by-layout/{img_tenant_id}/{img_style_number}"
                ob_response = requests.get(ob_url, timeout=30)
                if ob_response.status_code == 200:
                    ob_data = ob_response.json()
            except Exception:
                pass  # OB not found, continue
        
        results_with_ob.append({
            "image_id": sim_img.get("image_id"),
            "tenant_id": img_tenant_id,
            "style_number": img_style_number,
            "image_url": sim_img.get("image_url"),
            "similarity": sim_img.get("similarity") or sim_img.get("similarity_score"),
            "ob_data": ob_data,
        })

    response_data = {
        "message": "Search completed successfully",
        "new_image": {
            "stored": store_image,
            "image_id": new_image_id,
            "tenant_id": tenant_id,
            "style_number": style_number,
            "image_url": new_image_url,
        },
        "similar_images_count": len(results_with_ob),
        "similar_images": results_with_ob,
    }

    return JSONResponse(content=response_data)
