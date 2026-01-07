from decimal import Decimal
import json
import logging
from typing import List, Optional
from fastapi import HTTPException
from app import database


logger = logging.getLogger(__name__)


async def fetch_from_db(query: str, values: dict):
    try:
        results = await database.fetch_all(query, values)
        if not results:
            return None
        return results
    except Exception as e:
        logger.error(f"Database query failed: {e}")
        raise HTTPException(
            status_code=500, detail="Error retrieving data from the database"
        )


async def get_operations(tenant_id: int, style_type: str):
    style_type = style_type.strip()

    query_styletype_id = """
    SELECT s.styletype_id, s.style_type 
    FROM styletype s 
    WHERE s.tenant_id = :tenant_id 
    AND s.style_type = :style_type;
    """

    results = await fetch_from_db(
        query_styletype_id, {"tenant_id": tenant_id, "style_type": style_type}
    )
    if not results:
        raise HTTPException(
            status_code=404, detail="Style type not found for the given tenant"
        )
    styletype_id = int(results[0]["styletype_id"])

    query_layout_id = """
    SELECT l.layout_id, l.layout_code
    FROM layout l 
    WHERE l.tenant_id = :tenant_id 
    AND l.styletype_id = :styletype_id;
    """

    results = await fetch_from_db(
        query_layout_id, {"tenant_id": tenant_id, "styletype_id": styletype_id}
    )
    if not results:
        raise HTTPException(
            status_code=404, detail="Layout not found for the given tenant"
        )
    layout_ids = [layout["layout_id"] for layout in results]
    return layout_ids


async def get_op_data(tenant_ids: List[int], style_type: Optional[str] = None):
    """
    Fetch operation data for multiple tenants, optionally filtered by style_type.
    
    Args:
        tenant_ids: List of tenant IDs to search across
        style_type: Optional style type filter (if None, returns all style types)
    """
    
    # Build dynamic query based on whether style_type is provided
    if style_type:
        style_type = style_type.strip()
        query = """
        SELECT 
            layout.layout_id,
            layout.layout_code,
            styletype.style_type,
            layout_operation.operation_name,
            layout_operation.operation_seq,
            machine.machine_name
        FROM 
            layout
        JOIN 
            styletype ON layout.styletype_id = styletype.styletype_id
        JOIN 
            layout_operation ON layout.layout_id = layout_operation.layout_id
        JOIN 
            machine ON layout_operation.machine_id = machine.machine_id
        WHERE 
            layout.tenant_id IN :tenant_ids
            AND styletype.style_type = :style_type
        ORDER BY 
            layout.layout_id, 
            layout_operation.operation_seq;
        """
        query_params = {"tenant_ids": tuple(tenant_ids), "style_type": style_type}
    else:
        query = """
        SELECT 
            layout.layout_id,
            layout.layout_code,
            styletype.style_type,
            layout_operation.operation_name,
            layout_operation.operation_seq,
            machine.machine_name
        FROM 
            layout
        JOIN 
            styletype ON layout.styletype_id = styletype.styletype_id
        JOIN 
            layout_operation ON layout.layout_id = layout_operation.layout_id
        JOIN 
            machine ON layout_operation.machine_id = machine.machine_id
        WHERE 
            layout.tenant_id IN :tenant_ids
        ORDER BY 
            layout.layout_id, 
            layout_operation.operation_seq;
        """
        query_params = {"tenant_ids": tuple(tenant_ids)}

    results = await fetch_from_db(query, query_params)
    if not results:
        raise HTTPException(
            status_code=404,
            detail="No operations found for the given tenant(s)" + (f" and style type '{style_type}'" if style_type else ""),
        )
    data = [dict(row) for row in results]
    reorganized_data = {}
    for row in data:
        layout_id = row["layout_id"]
        if layout_id not in reorganized_data:
            reorganized_data[layout_id] = {
                "layout_id": layout_id,
                "layout_code": row["layout_code"],
                "operation_data": [],
            }
        reorganized_data[layout_id]["operation_data"].append(
            (row["operation_name"], row["machine_name"], row["operation_seq"])
        )
    data_records = list(reorganized_data.values())

    return data_records


async def get_style_types(tenant_id: int):
    try:
        query = """
        SELECT style_type 
        FROM styletype 
        WHERE tenant_id = :tenant_id;
        """

        results = await fetch_from_db(query, {"tenant_id": tenant_id})
        if not results:
            raise HTTPException(
                status_code=404, detail="No style types found for the given tenant"
            )
        style_types = [row["style_type"] for row in results]
        no_of_style_types = len(style_types)
        return style_types, no_of_style_types
    except Exception as e:
        logger.error(f"Error fetching style types: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error retrieving style types from the database",
        )


async def add_allocation_data(top_results: dict, no_of_allocations: int):
    try:
        layout_ids = [int(result["layout_id"]) for result in top_results]
        logger.info(f"Layout IDs: {layout_ids}")

        query = """
        SELECT 
            layout_id,
            allocation_id,
            allocation_name,
            hourly_target,
            run_efficiency
        FROM
            allocation
        WHERE
            layout_id IN :layout_ids;
        """

        values = {"layout_ids": tuple(layout_ids)}
        allocation_data = await fetch_from_db(query, values)

        if not allocation_data:
            raise HTTPException(
                status_code=404,
                detail="Error retrieving allocation data from the database",
            )

        allocation_data_dict = [dict(row) for row in allocation_data]

        for result in top_results:
            layout_id_result = result["layout_id"]
            allocation_data = []
            for allocation in allocation_data_dict:
                layout_id_allocation = allocation["layout_id"]
                if layout_id_result == layout_id_allocation:
                    allocation_data.append(allocation)

            allocation_data.sort(
                key=lambda x: (
                    x["run_efficiency"] is None,
                    (
                        x["run_efficiency"]
                        if x["run_efficiency"] is not None
                        else Decimal("-Infinity")
                    ),
                ),
                reverse=True,
            )

            for allocation in allocation_data[:3]:
                if allocation["run_efficiency"] is not None:
                    allocation["run_efficiency"] = float(allocation["run_efficiency"])

            result["allocation_data"] = allocation_data[:no_of_allocations]

        return top_results

    except Exception as e:
        logger.error(f"Error fetching allocation data: {e}")
        raise HTTPException(
            status_code=500, detail="Error retrieving allocation data from the database"
        )


async def add_allocation_data_v2(top_results: dict, no_of_allocations: int):
    try:
        layout_ids = [int(result["layout_id"]) for result in top_results]
        logger.info(f"Layout IDs: {layout_ids}")

        query = """
        SELECT 
            layout_id,
            allocation_id,
            allocation_name,
            line_id,
            hourly_target,
            run_efficiency
        FROM
            allocation
        WHERE
            layout_id IN :layout_ids
        ORDER BY
            run_efficiency DESC
        LIMIT :no_of_allocations;
        """

        query_params = {
            "layout_ids": tuple(layout_ids),
            "no_of_allocations": no_of_allocations + 1,
        }
        allocation_data = await fetch_from_db(query, query_params)

        if not allocation_data:
            raise HTTPException(
                status_code=404,
                detail="Error retrieving allocation data from the database",
            )

        allocation_data_dict = [dict(row) for row in allocation_data]

        for result in top_results:
            layout_id_result = result["layout_id"]
            allocation_data = []
            for allocation in allocation_data_dict:
                layout_id_allocation = allocation["layout_id"]
                if layout_id_result == layout_id_allocation:
                    allocation_data.append(allocation)

            for allocation in allocation_data:
                if allocation["run_efficiency"] is not None:
                    allocation["run_efficiency"] = float(allocation["run_efficiency"])

            result["allocation_data"] = allocation_data

        return top_results

    except Exception as e:
        logger.error(f"Error fetching allocation data: {e}")
        raise HTTPException(
            status_code=500, detail="Error retrieving allocation data from the database"
        )


def add_allocation_data_ds(
    top_results: dict, allocation_datasource: list, no_of_allocations: int
):
    try:
        for result in top_results:
            layout_id_result = result["layout_id"]
            allocation_data = []
            for allocation in allocation_datasource:
                layout_id_allocation = allocation["layout_id"]
                if layout_id_result == layout_id_allocation:
                    allocation_data.append(allocation)

            for allocation in allocation_data:
                if allocation["run_efficiency"] is not None:
                    allocation["run_efficiency"] = float(allocation["run_efficiency"])

            result["allocation_data"] = allocation_data[:no_of_allocations]

        return top_results

    except Exception as e:
        logger.error(f"Error fetching allocation data: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error adding allocation data to the results by datasource",
        )

# -------------------------------------------------------------------------------- #

async def get_ob_by_layout_code(tenant_id: int, layout_code: str):
    """Fetch OB data for a specific layout_code (style_number from image service)"""
    layout_code = layout_code.strip()
    
    query = """
    SELECT 
        layout.layout_id,
        layout.layout_code,
        styletype.style_type,
        layout_operation.operation_name,
        layout_operation.operation_seq,
        machine.machine_name
    FROM 
        layout layout
    JOIN 
        styletype styletype ON layout.styletype_id = styletype.styletype_id
    JOIN 
        layout_operation layout_operation ON layout.layout_id = layout_operation.layout_id
    JOIN 
        machine machine ON layout_operation.machine_id = machine.machine_id
    WHERE 
        layout.tenant_id = :tenant_id
        AND layout.layout_code = :layout_code
    ORDER BY 
        layout_operation.operation_seq;
    """
    results = await fetch_from_db(query, {"tenant_id": tenant_id, "layout_code": layout_code})
    if not results:
        return None
    
    # Reorganize into structured format
    data = [dict(row) for row in results]
    ob_data = {
        "layout_id": data[0]["layout_id"],
        "layout_code": data[0]["layout_code"],
        "style_type": data[0]["style_type"],
        "operation_data": [
            {
                "operation_name": row["operation_name"],
                "machine_name": row["machine_name"],
                "sequence_number": row["operation_seq"]
            }
            for row in data
        ]
    }
    return ob_data