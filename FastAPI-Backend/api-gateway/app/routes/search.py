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


# Define main request model
class RequestModel(BaseModel):
    search_type: str
    allocation_data: Optional[bool] = False
    tenant_id: str
    style_type: str
    image_orientation: Optional[str] = None
    no_of_results_img: Optional[int] = 10
    no_of_results_ob: Optional[int] = 10
    no_of_allocations: Optional[int] = 5
    operation_data: Optional[List[OperationData]] = None


class RequestModelDatasource(BaseModel):
    tenant_id: str
    style_type: str
    allocation_data: Optional[bool] = False
    no_of_results: Optional[int] = 10
    no_of_allocations: Optional[int] = 5
    operation_data: List[OperationData]


@search_router.post("/search/")
async def search(
    search_type: str = Form(
        ..., regex="^(ob_only|image_only|ob_and_image)", example="ob_and_img"
    ),
    allocation_data: Optional[bool] = Form(
        False, example=True, description="Flag to include allocation data"
    ),
    tenant_id: str = Form(..., example="3"),
    style_type: str = Form(..., example="LADIES BRIEF - TEZENIS BEACHWEAR"),
    image_orientation: Optional[str] = Form(
        None,
        regex="^(portrait|landscape|square)$",
        description="Image orientation must be one of 'portrait', 'landscape', or 'square'",
    ),
    no_of_results_img: Optional[int] = Form(10),
    no_of_results_ob: Optional[int] = Form(10),
    no_of_allocations: Optional[int] = Form(5),
    operation_data: Optional[str] = Form(
        None,
        description="List of operation data: [{ 'operation_name': 'operation1', 'machine_name': 'machine1', 'sequence_number': 1 }, { 'operation_name': 'operation2', 'machine_name': 'machine2', 'sequence_number': 2 }]",
        example="[{ 'operation_name': 'operation1', 'machine_name': 'machine1', 'sequence_number': 1 }, { 'operation_name': 'operation2', 'machine_name': 'machine2', 'sequence_number': 2 }]",
    ),
    image_front: Optional[UploadFile] = File(None),
    image_back: Optional[UploadFile] = File(None),
):

    try:
        if search_type == "ob_only":
            if operation_data:
                try:
                    operation_data_parsed = json.loads(operation_data.replace("\n", ""))
                    if not isinstance(operation_data_parsed, list):
                        raise HTTPException(
                            status_code=400, detail="operation_data must be a list"
                        )
                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=400, detail="Invalid JSON for operation_data"
                    )

            else:
                raise HTTPException(
                    status_code=400,
                    detail="operation_data is required for 'ob_only' search type",
                )

            # Prepare request data
            request_data = RequestModel(
                search_type=search_type,
                allocation_data=allocation_data,
                tenant_id=tenant_id,
                style_type=style_type,
                no_of_results_ob=no_of_results_ob,
                no_of_allocations=no_of_allocations,
                operation_data=operation_data_parsed,
            )

            # Perform operation based search
            request_data_ob = {
                "tenant_id": int(tenant_id),
                "allocation_data": allocation_data,
                "style_type": style_type,
                "no_of_results": no_of_results_ob,
                "no_of_allocations": no_of_allocations,
                "operation_data": (
                    [data.model_dump() for data in request_data.operation_data]
                    if request_data.operation_data
                    else None
                ),
            }

            # Call operation based search service
            ob_search_url = f"{settings.OB_SIMILARITY_SERVICE_URL}/ob/search"
            try:
                response = requests.post(
                    ob_search_url,
                    json=request_data_ob,
                    timeout=360,  # 6 minutes timeout
                )
                response.raise_for_status()
            except requests.Timeout:
                raise HTTPException(
                    status_code=504, detail="Operation based search service timed out"
                )

            # Prepare response data
            response_data = {
                "search_type": search_type,
                "allocation_data": allocation_data,
                "style_type": style_type,
                "tenant_id": tenant_id,
                "no_of_results": response.json().get("no_of_results"),
                "total_obs": response.json().get("total_obs"),
                "process_time": response.json().get("process_time"),
                "operation_results": response.json().get("results"),
            }
            return JSONResponse(content=response_data)

        elif search_type == "image_only":
            request_data = RequestModel(
                search_type=search_type,
                tenant_id=tenant_id,
                style_type=style_type,
                image_orientation=image_orientation,
                no_of_results_img=no_of_results_img,
            )

            # Perform image based search
            try:
                image_front_bytes = await image_front.read()
                image_back_bytes = await image_back.read()
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail="Error reading uploaded image files"
                )

            # Prepare multipart/form-data payload
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
                "tenant_id": tenant_id,
                "style_type": style_type,
                "image_orientation": image_orientation,
                "no_of_results": no_of_results_img,
            }

            # Call image based search service
            image_search_url = (
                f"{settings.IMAGE_SIMILARITY_SERVICE_URL}/img/search-image"
            )
            try:
                response = requests.post(
                    image_search_url,
                    data=data,
                    files=files,
                    timeout=360,  # 6 minutes timeout
                )
                response.raise_for_status()
            except requests.Timeout:
                raise HTTPException(
                    status_code=504, detail="Image based search service timed out"
                )

            response_data = {
                "search_type": search_type,
                "style_type": style_type,
                "tenant_id": tenant_id,
                "no_of_results": response.json().get("no_of_results"),
                "total_images": response.json().get("total_images"),
                "process_time": response.json().get("process_time"),
                "image_results": response.json().get("results"),
            }
            return JSONResponse(content=response_data)

        elif search_type == "ob_and_image":
            try:
                image_front_bytes = await image_front.read()
                image_back_bytes = await image_back.read()
            except Exception as e:
                raise HTTPException(
                    status_code=400, detail="Error reading uploaded image files"
                )

            if operation_data:
                try:
                    operation_data_parsed = json.loads(operation_data.replace("\n", ""))
                    if not isinstance(operation_data_parsed, list):
                        raise HTTPException(
                            status_code=400, detail="operation_data must be a list"
                        )
                except json.JSONDecodeError:
                    raise HTTPException(
                        status_code=400, detail="Invalid JSON for operation_data"
                    )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="operation_data is required for 'ob_and_image' search type",
                )

            request_data = RequestModel(
                search_type=search_type,
                allocation_data=allocation_data,
                tenant_id=tenant_id,
                style_type=style_type,
                image_orientation=image_orientation,
                no_of_results_img=no_of_results_img,
                no_of_results_ob=no_of_results_ob,
                operation_data=operation_data_parsed,
            )

            # Perform operation based search
            request_data_ob = {
                "tenant_id": int(tenant_id),
                "allocation_data": allocation_data,
                "style_type": style_type,
                "no_of_results": no_of_results_ob,
                "operation_data": (
                    [data.model_dump() for data in request_data.operation_data]
                    if request_data.operation_data
                    else None
                ),
            }

            # Call operation based search service
            ob_search_url = f"{settings.OB_SIMILARITY_SERVICE_URL}/ob/search"

            try:
                response_ob = requests.post(
                    ob_search_url,
                    json=request_data_ob,
                    timeout=360,  # 6 minutes timeout
                )
                response_ob.raise_for_status()
            except requests.Timeout:
                raise HTTPException(
                    status_code=504, detail="Operation based search service timed out"
                )

            # Perform image based search
            # Prepare multipart/form-data payload
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
                "tenant_id": tenant_id,
                "style_type": style_type,
                "image_orientation": image_orientation,
                "no_of_results": no_of_results_img,
            }

            # Call image based search service
            image_search_url = (
                f"{settings.IMAGE_SIMILARITY_SERVICE_URL}/img/search-image"
            )
            try:
                response_img = requests.post(
                    image_search_url,
                    data=data,
                    files=files,
                    timeout=360,  # 6 minutes timeout
                )
                response_img.raise_for_status()
            except requests.Timeout:
                raise HTTPException(
                    status_code=504, detail="Image based search service timed out"
                )

            # Prepare response data
            response_data = {
                "search_type": search_type,
                "style_type": style_type,
                "tenant_id": tenant_id,
                "no_of_results_ob": response_ob.json().get("no_of_results"),
                "total_obs": response_ob.json().get("total_obs"),
                "no_of_results_img": response_img.json().get("no_of_results"),
                "total_images": response_img.json().get("total_images"),
                "process_time_ob": response_ob.json().get("process_time"),
                "process_time_img": response_img.json().get("process_time"),
                "ob_similarity_results": response_ob.json().get("results"),
                "img_similarity_results": response_img.json().get("results"),
            }

            return JSONResponse(content=response_data)

        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid search type. Must be one of 'ob_only', 'image_only', or 'ob_and_image'",
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@search_router.post("/search-ds/")
async def search_ob_ds(
    ob_datasource: UploadFile = File(...),
    allocation_datasource: Optional[UploadFile] = File(None),
    tenant_id: str = Form(..., example="3"),
    style_type: str = Form(..., example="LADIES BRIEF - TEZENIS BEACHWEAR"),
    allocation_data: Optional[bool] = Form(..., example=True),
    no_of_results: Optional[int] = Form(10),
    no_of_allocations: Optional[int] = Form(5),
    operation_data: str = Form(
        ...,
        example="[{ 'operation_name': 'operation1', 'machine_name': 'machine1', 'sequence_number': 1 }, { 'operation_name': 'operation2', 'machine_name': 'machine2', 'sequence_number': 2 }]",
    ),
):
    try:
        if allocation_data:
            try:
                ob_datasource_json = json.loads(await ob_datasource.read())
                allocation_datasource_json = json.loads(
                    await allocation_datasource.read()
                )

            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400, detail="Invalid JSON for datasource"
                )

        else:
            try:
                ob_datasource_json = json.loads(await ob_datasource.read())
            except json.JSONDecodeError:
                raise HTTPException(
                    status_code=400, detail="Invalid JSON for datasource"
                )

        try:
            operation_data_parsed = json.loads(operation_data.replace("\n", ""))
            if not isinstance(operation_data_parsed, list):
                raise HTTPException(
                    status_code=400, detail="operation_data must be a list"
                )
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=400, detail="Invalid JSON for operation_data"
            )

        # Prepare request data
        request_data = RequestModelDatasource(
            tenant_id=tenant_id,
            style_type=style_type,
            allocation_data=allocation_data,
            no_of_results=no_of_results,
            no_of_allocations=no_of_allocations,
            operation_data=operation_data_parsed,
        )

        if allocation_data:
            request_ds = {
                "tenant_id": tenant_id,
                "style_type": style_type,
                "allocation_data": allocation_data,
                "no_of_results": no_of_results,
                "no_of_allocations": no_of_allocations,
                "operation_data": (
                    [data.model_dump() for data in request_data.operation_data]
                ),
                "ob_datasource": ob_datasource_json,
                "allocation_datasource": allocation_datasource_json,
            }

        else:

            request_ds = {
                "tenant_id": tenant_id,
                "style_type": style_type,
                "allocation_data": allocation_data,
                "no_of_results": no_of_results,
                "no_of_allocations": no_of_allocations,
                "operation_data": (
                    [data.model_dump() for data in request_data.operation_data]
                ),
                "ob_datasource": ob_datasource_json,
            }

        try:
            search_url = f"{settings.OB_SIMILARITY_SERVICE_URL}/ob/search-ds"
            response = requests.post(
                search_url,
                json=request_ds,
                timeout=360,  # 6 minutes timeout
            )

            response.raise_for_status()
        except requests.Timeout:
            raise HTTPException(
                status_code=504, detail="Operation based search service timed out"
            )

        response_data = {
            "tenant_id": tenant_id,
            "style_type": style_type,
            "no_of_results": response.json().get("no_of_results"),
            "total_obs": response.json().get("total_obs"),
            "process_time": response.json().get("process_time"),
            "operation_results": response.json().get("results"),
        }

        return JSONResponse(content=response_data)

    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
