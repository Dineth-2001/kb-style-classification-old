# OB-Similarity Service - Expected API Responses

This guide shows you what to expect when testing each endpoint using FastAPI Swagger Docs (`http://localhost:8001/docs`).

---

## 1. GET `/status`

**Purpose**: Check if the service is running

### Expected Response (200 OK):
```json
{
  "service_status": "UP",
  "description": "Operation breakdown similarity search engine is up and running"
}
```

---

## 2. GET `/ob/get-style-types/{tenant_id}`

**Purpose**: Get all available style types for a specific tenant

### Example Request:
- URL: `/ob/get-style-types/3`
- tenant_id: `3`

### Expected Response (200 OK):
```json
[
  "LADIES BRIEF - TEZENIS BEACHWEAR",
  "MENS T-SHIRT - CASUAL",
  "LADIES BRA - SPORTS",
  "LADIES PANTY - BASIC",
  ...
]
```

### Possible Errors:
- **400 Bad Request**: If tenant_id is invalid (≤ 0)
- **404 Not Found**: If no style types exist for the tenant
- **500 Internal Server Error**: Database connection issues

---

## 3. GET `/ob/get-ob-by-layout/{tenant_id}/{layout_code}`

**Purpose**: Get operation breakdown data for a specific layout code

### Example Request:
- URL: `/ob/get-ob-by-layout/3/ABC123`
- tenant_id: `3`
- layout_code: `ABC123`

### Expected Response (200 OK):
```json
{
  "layout_id": 456,
  "layout_code": "ABC123",
  "style_type": "LADIES BRIEF - TEZENIS BEACHWEAR",
  "operations": [
    {
      "operation_name": "TACK SIDE SEAMS UPPER+UNDER",
      "machine_name": "Zig Zag Machine",
      "sequence_number": 1
    },
    {
      "operation_name": "ATTACH ELASTIC AT WAISTLINE",
      "machine_name": "Coverstitch Machine",
      "sequence_number": 2
    }
  ]
}
```

### Possible Errors:
- **404 Not Found**: Layout code doesn't exist for the given tenant

---

## 4. POST `/ob/search` (WITHOUT allocation_data)

**Purpose**: Find similar operation breakdowns without allocation data

### Example Request Body:
```json
{
  "tenant_id": 3,
  "style_type": "LADIES BRIEF - TEZENIS BEACHWEAR",
  "allocation_data": false,
  "no_of_results": 5,
  "no_of_allocations": 3,
  "operation_data": [
    {
      "operation_name": "TACK SIDE SEAMS UPPER+UNDER",
      "machine_name": "Zig Zag Machine",
      "sequence_number": 1
    },
    {
      "operation_name": "ATTACH ELASTIC AT WAISTLINE",
      "machine_name": "Coverstitch Machine",
      "sequence_number": 2
    }
  ]
}
```

### Expected Response (200 OK):
```json
{
  "message": "Search successful",
  "allocation_data": false,
  "total_obs": 47,
  "no_of_results": 5,
  "process_time": 0.234,
  "results": [
    {
      "layout_id": 123,
      "layout_code": "ABC001",
      "similarity_score": 95.5,
      "operation_data": [
        ["TACK SIDE SEAMS UPPER+UNDER", "Zig Zag Machine", 1],
        ["ATTACH ELASTIC AT WAISTLINE", "Coverstitch Machine", 2],
        ["TRIM EXCESS THREADS", "Manual", 3]
      ]
    },
    {
      "layout_id": 124,
      "layout_code": "ABC002",
      "similarity_score": 89.2,
      "operation_data": [
        ["TACK SIDE SEAMS", "Zig Zag Machine", 1],
        ["ATTACH ELASTIC", "Coverstitch Machine", 2]
      ]
    }
    // ... up to 5 results
  ]
}
```

### Response Fields Explained:
- `message`: Status message
- `allocation_data`: Whether allocation data is included (false)
- `total_obs`: Total number of OBs found in database matching the style type
- `no_of_results`: Number of results returned (top N by similarity)
- `process_time`: Time taken to process the request (in seconds)
- `results`: Array of matching layouts sorted by similarity score (highest first)
  - `layout_id`: Unique ID of the layout
  - `layout_code`: Code/identifier for the layout
  - `similarity_score`: Similarity percentage (0-100)
  - `operation_data`: Array of [operation_name, machine_name, sequence]

### Possible Errors:
- **404 Not Found**: No data found for the tenant/style type combination
- **422 Unprocessable Entity**: Invalid request body format
- **500 Internal Server Error**: Processing error

---

## 5. POST `/ob/search` (WITH allocation_data)

**Purpose**: Find similar operation breakdowns WITH allocation data

### Example Request Body:
```json
{
  "tenant_id": 3,
  "style_type": "LADIES BRIEF - TEZENIS BEACHWEAR",
  "allocation_data": true,
  "no_of_results": 5,
  "no_of_allocations": 3,
  "operation_data": [
    {
      "operation_name": "TACK SIDE SEAMS UPPER+UNDER",
      "machine_name": "Zig Zag Machine",
      "sequence_number": 1
    },
    {
      "operation_name": "ATTACH ELASTIC AT WAISTLINE",
      "machine_name": "Coverstitch Machine",
      "sequence_number": 2
    }
  ]
}
```

### Expected Response (200 OK):
```json
{
  "message": "Search successful",
  "allocation_data": true,
  "total_obs": 47,
  "no_of_results": 5,
  "process_time": 0.456,
  "results": [
    {
      "layout_id": 123,
      "layout_code": "ABC001",
      "similarity_score": 95.5,
      "operation_data": [
        ["TACK SIDE SEAMS UPPER+UNDER", "Zig Zag Machine", 1],
        ["ATTACH ELASTIC AT WAISTLINE", "Coverstitch Machine", 2]
      ],
      "allocation_data": [
        {
          "layout_id": 123,
          "allocation_id": 501,
          "allocation_name": "Line A - Shift 1",
          "hourly_target": 120,
          "run_efficiency": 95.5
        },
        {
          "layout_id": 123,
          "allocation_id": 502,
          "allocation_name": "Line B - Shift 2",
          "hourly_target": 110,
          "run_efficiency": 92.3
        },
        {
          "layout_id": 123,
          "allocation_id": 503,
          "allocation_name": "Line C - Shift 1",
          "hourly_target": 100,
          "run_efficiency": 88.7
        }
      ]
    }
    // ... up to 5 results, each with allocation data
  ]
}
```

### Additional Fields When allocation_data=true:
- `allocation_data`: Array of allocations for each layout (sorted by efficiency)
  - `allocation_id`: Unique ID of the allocation
  - `allocation_name`: Name of the allocation/line
  - `hourly_target`: Target production per hour
  - `run_efficiency`: Efficiency percentage (can be null)
  - Limited to `no_of_allocations` (default: 3)

### Note:
- Process time is longer when requesting allocation data
- Allocations are sorted by `run_efficiency` (highest first)
- If `run_efficiency` is null, those allocations appear last

---

## 6. POST `/ob/search-ds` (Search with DataSource)

**Purpose**: Search using custom datasources instead of database

### Example Request Body:
```json
{
  "tenant_id": 3,
  "style_type": "LADIES BRIEF - TEZENIS BEACHWEAR",
  "allocation_data": true,
  "no_of_results": 5,
  "no_of_allocations": 3,
  "operation_data": [
    {
      "operation_name": "TACK SIDE SEAMS",
      "machine_name": "Zig Zag Machine",
      "sequence_number": 1
    }
  ],
  "ob_datasource": [
    {
      "layout_id": 100,
      "layout_code": "TEST001",
      "style_type": "LADIES BRIEF - TEZENIS BEACHWEAR",
      "operation_data": [
        ["TACK SIDE SEAMS", "Zig Zag Machine", 1],
        ["ATTACH ELASTIC", "Coverstitch Machine", 2]
      ]
    }
  ],
  "allocation_datasource": [
    {
      "layout_id": 100,
      "allocation_id": 1,
      "allocation_name": "Test Line",
      "hourly_target": 100,
      "run_efficiency": 90.0
    }
  ]
}
```

### Expected Response (200 OK):
Same format as `/ob/search` but uses the provided datasources instead of querying the database.

### Use Case:
- Testing with custom data
- When you want to provide your own OB and allocation datasets
- Useful for scenarios where data isn't in the database yet

---

## 7. POST `/ob/save`

**Purpose**: Save endpoint (NOT YET IMPLEMENTED)

### Expected Response (200 OK):
```json
{
  "message": "Save API"
}
```

### Note:
This endpoint is a placeholder and doesn't perform any actual save operation yet.

---

## Common HTTP Status Codes

| Code | Meaning | When It Occurs |
|------|---------|----------------|
| 200 | OK | Successful request |
| 400 | Bad Request | Invalid parameters (e.g., tenant_id ≤ 0) |
| 404 | Not Found | Data not found in database |
| 422 | Unprocessable Entity | Invalid JSON format or missing required fields |
| 500 | Internal Server Error | Database errors, processing errors |

---

## Tips for Testing in FastAPI Docs

1. **Start with `/status`**: Verify the service is running

2. **Get Style Types First**: Use `/ob/get-style-types/3` to see what style types are available in your database

3. **Use Valid Style Types**: Copy a style type from the previous step to use in search

4. **Start Simple**: Test `/ob/search` with `allocation_data: false` first

5. **Adjust Parameters**:
   - `no_of_results`: Controls how many matches to return (default: 10)
   - `no_of_allocations`: Controls allocations per result (default: 3)

6. **Watch Response Times**: 
   - Without allocation data: ~0.1-0.5 seconds
   - With allocation data: ~0.3-1.0 seconds (depends on data volume)

7. **Check Process Time**: Included in response to help you understand performance

---

## Troubleshooting Expected Responses

### If you get 404 errors:
- Your database might be empty
- Check if the tenant_id exists
- Verify the style_type name exactly matches (case-sensitive)

### If you get 500 errors:
- Check database connection in `.env` file
- Ensure database service is running
- Check logs for detailed error messages

### If similarity_score seems wrong:
- The algorithm compares operation names and machine names
- Higher scores = better matches
- Scores are based on text similarity algorithms

---

## Example Test Sequence

```
1. GET /status 
   → Expect: {"service_status": "UP", ...}

2. GET /ob/get-style-types/3
   → Expect: Array of style type strings

3. POST /ob/search with allocation_data=false
   → Expect: Array of results with similarity scores

4. POST /ob/search with allocation_data=true
   → Expect: Same results + allocation_data arrays

5. GET /ob/get-ob-by-layout/3/{layout_code from step 3}
   → Expect: Detailed OB data for that layout
```

This should give you a complete picture of what the API returns!
