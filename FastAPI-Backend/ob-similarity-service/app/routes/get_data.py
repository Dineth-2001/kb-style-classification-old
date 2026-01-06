from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.utils.get_data import get_operations, get_op_data, get_style_types


data_router = APIRouter()


@data_router.get("/data/{tenant_id, style_type}")
async def get_data(tenant_id: int, style_type: str):
    results = await get_op_data(tenant_id, style_type)
    return JSONResponse(content=results)


@data_router.get("/get-style-types/{tenant_id}")
async def get_styles(tenant_id: int):
    try:
        if tenant_id <= 0:
            raise HTTPException(
                status_code=400, detail="Invalid tenant_id. Must be a positive integer."
            )
        results, no_of_styles = await get_style_types(tenant_id)

        if no_of_styles == 0:
            raise HTTPException(
                status_code=404, detail="No styles found for the given tenant"
            )

        return JSONResponse(content=results)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------------------------------------------------

@data_router.get("/get-ob-by-layout/{tenant_id}/{layout_code}")
async def get_ob_by_layout(tenant_id: int, layout_code: str):
    """Get OB data by tenant_id and layout_code (style_number)"""
    from app.utils.get_data import get_ob_by_layout_code
    result = await get_ob_by_layout_code(tenant_id, layout_code)
    if not result:
        raise HTTPException(status_code=404, detail="OB not found for given layout_code")
    return JSONResponse(content=result)