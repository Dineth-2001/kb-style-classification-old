# OB-Similarity Service - Testing Guide

## Quick Start

### 1. Start the Service

Make sure the service is running on port 8001:

```bash
# Activate virtual environment
venv\Scripts\activate

# Run the service
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

Or check the README for Docker instructions.

---

## Testing Methods

### Method 1: Using Python Test Script (Recommended)

Run the automated test script:

```bash
python test_endpoints.py
```

This will test all endpoints and give you a detailed report.

---

### Method 2: Using FastAPI Interactive Docs

Open your browser and navigate to:
- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

These provide interactive API documentation where you can test endpoints directly.

---

### Method 3: Using cURL Commands

#### 1. Check Service Status
```bash
curl http://localhost:8001/status
```

#### 2. Get Style Types for a Tenant
```bash
curl http://localhost:8001/ob/get-style-types/3
```

#### 3. Get OB by Layout Code
```bash
curl http://localhost:8001/ob/get-ob-by-layout/3/EXAMPLE001
```

#### 4. Search for Similar OBs (Basic)
```bash
curl -X POST http://localhost:8001/ob/search ^
  -H "Content-Type: application/json" ^
  -d "{\"tenant_id\": 3, \"style_type\": \"LADIES BRIEF - TEZENIS BEACHWEAR\", \"allocation_data\": false, \"no_of_results\": 5, \"no_of_allocations\": 3, \"operation_data\": [{\"operation_name\": \"TACK SIDE SEAMS UPPER+UNDER\", \"machine_name\": \"Zig Zag Machine\", \"sequence_number\": 1}, {\"operation_name\": \"ATTACH ELASTIC AT WAISTLINE\", \"machine_name\": \"Coverstitch Machine\", \"sequence_number\": 2}]}"
```

#### 5. Search with Allocation Data
```bash
curl -X POST http://localhost:8001/ob/search ^
  -H "Content-Type: application/json" ^
  -d "{\"tenant_id\": 3, \"style_type\": \"LADIES BRIEF - TEZENIS BEACHWEAR\", \"allocation_data\": true, \"no_of_results\": 5, \"no_of_allocations\": 3, \"operation_data\": [{\"operation_name\": \"TACK SIDE SEAMS UPPER+UNDER\", \"machine_name\": \"Zig Zag Machine\", \"sequence_number\": 1}]}"
```

#### 6. Save Endpoint
```bash
curl -X POST http://localhost:8001/ob/save ^
  -H "Content-Type: application/json" ^
  -d "{}"
```

---

### Method 4: Using PowerShell

#### Check Status
```powershell
Invoke-RestMethod -Uri "http://localhost:8001/status" -Method Get
```

#### Get Style Types
```powershell
Invoke-RestMethod -Uri "http://localhost:8001/ob/get-style-types/3" -Method Get
```

#### Search for Similar OBs
```powershell
$body = @{
    tenant_id = 3
    style_type = "LADIES BRIEF - TEZENIS BEACHWEAR"
    allocation_data = $false
    no_of_results = 5
    no_of_allocations = 3
    operation_data = @(
        @{
            operation_name = "TACK SIDE SEAMS UPPER+UNDER"
            machine_name = "Zig Zag Machine"
            sequence_number = 1
        },
        @{
            operation_name = "ATTACH ELASTIC AT WAISTLINE"
            machine_name = "Coverstitch Machine"
            sequence_number = 2
        }
    )
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:8001/ob/search" -Method Post -Body $body -ContentType "application/json"
```

---

## Available Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/status` | Check if service is running |
| GET | `/ob/get-style-types/{tenant_id}` | Get all style types for a tenant |
| GET | `/ob/get-ob-by-layout/{tenant_id}/{layout_code}` | Get OB data by layout code |
| POST | `/ob/search` | Search for similar operation breakdowns |
| POST | `/ob/search-datasource` | Search with custom datasource |
| POST | `/ob/save` | Save endpoint (not fully implemented) |

---

## Request/Response Examples

### POST /ob/search Request Body
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

### Expected Response
```json
{
  "message": "Search successful",
  "allocation_data": false,
  "total_obs": 25,
  "no_of_results": 5,
  "process_time": 0.234,
  "results": [
    {
      "layout_id": 123,
      "style_number": "ABC001",
      "similarity_score": 95.5,
      "operations": [...]
    }
  ]
}
```

---

## Troubleshooting

### Service Not Running
**Error**: `Connection refused` or `Could not connect`

**Solution**: Make sure the service is running:
```bash
cd d:\Kingslake\kb-style-classification-old\FastAPI-Backend\ob-similarity-service
venv\Scripts\activate
uvicorn server:app --host 0.0.0.0 --port 8001 --reload
```

### Database Connection Error
**Error**: Database related errors

**Solution**: 
1. Check your `.env` file has the correct `DATABASE_URL`
2. Ensure the database is running (if using Docker: `docker-compose up`)
3. Verify database credentials

### Port Already in Use
**Error**: `Address already in use: 8001`

**Solution**: Change the port or kill the existing process:
```bash
# Change port
uvicorn server:app --host 0.0.0.0 --port 8002

# Or find and kill the process (PowerShell)
Get-Process -Id (Get-NetTCPConnection -LocalPort 8001).OwningProcess | Stop-Process
```

### Missing Dependencies
**Error**: `ModuleNotFoundError`

**Solution**: Install dependencies:
```bash
pip install -r requirements.txt
```

---

## Notes

- Default port is **8001** (configured in server.py)
- The service requires a database connection to work properly
- Make sure your `.env` file is configured correctly (copy from `.env.example`)
- Some endpoints may return 404 if the data doesn't exist in the database
