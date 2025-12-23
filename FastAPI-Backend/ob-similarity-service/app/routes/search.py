import time
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError
from typing import List, Optional
from app.utils.get_data import (
    add_allocation_data_ds,
    get_op_data,
    add_allocation_data,
    add_allocation_data_v2,
)
from app.utils.text_compare import get_ob_similarity_score, get_ob_similarity_score_v2
from app.utils.filter_data import filter_by_style_type
import json
import logging

logger = logging.getLogger(__name__)


search_router = APIRouter()


# Define Pydantic models
class OperationDataItem(BaseModel):
    operation_name: str = Field(..., example="TACK SIDE SEAMS UPPER+UNDER")
    machine_name: str = Field(..., example="Zig Zag Machine")
    sequence_number: int = Field(..., example=1)


class SearchRequest(BaseModel):
    tenant_id: int = Field(..., example=3)
    style_type: str = Field(..., example="LADIES BRIEF - TEZENIS BEACHWEAR")
    allocation_data: bool = Field(False, example=True)
    no_of_results: int = Field(10, gt=0, example=5)
    no_of_allocations: int = Field(3, gt=0, example=5)
    operation_data: List[OperationDataItem]


class SearchRequestDataSource(BaseModel):
    tenant_id: int = Field(..., example=3)
    style_type: str = Field(..., example="LADIES BRIEF - TEZENIS BEACHWEAR")
    allocation_data: bool = Field(False, example=True)
    no_of_results: int = Field(10, gt=0, example=5)
    no_of_allocations: int = Field(5, gt=0, example=5)
    operation_data: List[OperationDataItem]
    ob_datasource: List[dict]
    allocation_datasource: List[dict] = None


@search_router.post("/search")
async def search(request: SearchRequest):
    try:
        # Get the request data
        tenant_id = request.tenant_id
        style_type = request.style_type
        allocation_data = request.allocation_data
        no_of_results = request.no_of_results
        no_of_allocations = request.no_of_allocations
        operation_data = request.operation_data

        if not allocation_data:

            time_start = time.time()

            # Retrieve the data from the database
            data_records = await get_op_data(tenant_id, style_type)

            if not data_records:
                raise HTTPException(
                    status_code=404,
                    detail="No data records found for the given tenant and style type",
                )

            results = get_ob_similarity_score_v2(operation_data, data_records)

            # Filter the top results based on the no_of_results
            top_results = (
                results[:no_of_results]
                if len(results) > no_of_results
                else results[: len(results)]
            )

            end_time = time.time()

            process_time = end_time - time_start

            return JSONResponse(
                content={
                    "message": "Search successful",
                    "allocation_data": allocation_data,
                    "total_obs": len(results),
                    "no_of_results": len(top_results),
                    "process_time": process_time,
                    "results": top_results,
                },
            )
        else:
            time_start = time.time()

            # Retrieve the data from the database
            data_records = await get_op_data(tenant_id, style_type)

            if not data_records:
                raise HTTPException(
                    status_code=404,
                    detail="No data records found for the given tenant and style type",
                )

            results = get_ob_similarity_score(operation_data, data_records)

            # Filter the top results based on the no_of_results
            top_results = (
                results[:no_of_results]
                if len(results) > no_of_results
                else results[: len(results)]
            )

            # Add the allocation data to the results
            top_results_allocation = await add_allocation_data_v2(
                top_results, no_of_allocations
            )

            end_time = time.time()

            process_time = end_time - time_start

            return JSONResponse(
                content={
                    "message": "Search successful",
                    "allocation_data": allocation_data,
                    "total_obs": len(results),
                    "no_of_results": len(top_results),
                    "results": top_results_allocation,
                    "process_time": process_time,
                },
            )

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except Exception as e:
        logger.error(f"Error searching for operations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@search_router.post("/search-ds")
async def search_data_source_2(request: SearchRequestDataSource):

    try:
        tenant_id = request.tenant_id
        style_type = request.style_type
        allocation_data = request.allocation_data
        no_of_results = request.no_of_results
        no_of_allocations = request.no_of_allocations
        operation_data = request.operation_data
        ob_datasource = request.ob_datasource
        allocation_datasource = request.allocation_datasource

        if allocation_data:
            start_time = time.time()

            filtered_data = filter_by_style_type(style_type, ob_datasource)

            results = get_ob_similarity_score_v2(operation_data, filtered_data)

            top_results = (
                results[:no_of_results]
                if len(results) > no_of_results
                else results[: len(results)]
            )

            top_results_allocation = add_allocation_data_ds(
                top_results, allocation_datasource, no_of_allocations
            )

            end_time = time.time()

            process_time = end_time - start_time

            return JSONResponse(
                content={
                    "message": "Search successful",
                    "allocation_data": allocation_data,
                    "total_obs": len(results),
                    "no_of_results": len(top_results),
                    "process_time": process_time,
                    "results": top_results_allocation,
                },
            )
        else:
            print(allocation_data)
            start_time = time.time()

            filtered_data = filter_by_style_type(style_type, ob_datasource)

            results = get_ob_similarity_score(operation_data, filtered_data)

            top_results = (
                results[:no_of_results]
                if len(results) > no_of_results
                else results[: len(results)]
            )

            end_time = time.time()

            process_time = end_time - start_time

            return JSONResponse(
                content={
                    "message": "Search successful",
                    "allocation_data": allocation_data,
                    "total_obs": len(results),
                    "no_of_results": len(top_results),
                    "process_time": process_time,
                    "results": top_results,
                },
            )

    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.errors())
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
