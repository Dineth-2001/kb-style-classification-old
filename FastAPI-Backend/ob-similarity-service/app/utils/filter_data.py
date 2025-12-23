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
