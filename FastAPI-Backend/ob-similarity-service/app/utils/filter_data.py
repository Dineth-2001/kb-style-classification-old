from typing import List, Optional


def filter_by_style_type(style_type: str, ob_datasource_json: list) -> list:
    """
    Filter the ob_datasource_json based on the style_type
    """
    filtered_data = list()
    for record in ob_datasource_json:
        if record["style_type"] == style_type:
            filtered_data.append(record)

    reorganized_data = {}
    for row in filtered_data:
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

    filtered_data = list(reorganized_data.values())

    return filtered_data


def filter_by_tenant_and_style(
    tenant_ids: List[int], 
    style_type: Optional[str], 
    ob_datasource_json: list
) -> list:
    """
    Filter the ob_datasource_json based on tenant_ids and optionally style_type.
    
    Args:
        tenant_ids: List of tenant IDs to filter by
        style_type: Optional style type filter (if None, returns all style types)
        ob_datasource_json: The OB datasource data to filter
    
    Returns:
        Filtered and reorganized data grouped by layout_id
    """
    filtered_data = list()
    for record in ob_datasource_json:
        # Check if record's tenant_id is in the list of tenant_ids
        record_tenant_id = record.get("tenant_id")
        if record_tenant_id in tenant_ids:
            # If style_type is provided, also filter by it
            if style_type is None or record.get("style_type") == style_type:
                filtered_data.append(record)

    reorganized_data = {}
    for row in filtered_data:
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

    filtered_data = list(reorganized_data.values())

    return filtered_data
