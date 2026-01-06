"""
Test script for OB-Similarity Service endpoints
"""

import requests
import json
from typing import Dict, Any

# Base URL for the service
BASE_URL = "http://localhost:8001"  

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def print_test_header(test_name: str):
    """Print a formatted test header"""
    print(f"\n{BLUE}{'='*60}")
    print(f"Testing: {test_name}")
    print(f"{'='*60}{RESET}\n")


def print_success(message: str):
    """Print success message"""
    print(f"{GREEN}✓ {message}{RESET}")


def print_error(message: str):
    """Print error message"""
    print(f"{RED}✗ {message}{RESET}")


def print_info(message: str):
    """Print info message"""
    print(f"{YELLOW}ℹ {message}{RESET}")


def pretty_print_json(data: Dict[Any, Any]):
    """Pretty print JSON data"""
    print(json.dumps(data, indent=2))


# =====================================================================
# Test 1: Status Endpoint
# =====================================================================
def test_status():
    print_test_header("GET /status")
    
    try:
        response = requests.get(f"{BASE_URL}/status", timeout=5)
        
        if response.status_code == 200:
            print_success(f"Status code: {response.status_code}")
            print_info("Response:")
            pretty_print_json(response.json())
            return True
        else:
            print_error(f"Failed with status code: {response.status_code}")
            print(response.text)
            return False
    except requests.exceptions.ConnectionError:
        print_error("Could not connect to the service. Is it running?")
        return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


# =====================================================================
# Test 2: Get Style Types
# =====================================================================
def test_get_style_types(tenant_id: int = 3):
    print_test_header(f"GET /ob/get-style-types/{tenant_id}")
    
    try:
        response = requests.get(
            f"{BASE_URL}/ob/get-style-types/{tenant_id}",
            timeout=10
        )
        
        if response.status_code == 200:
            print_success(f"Status code: {response.status_code}")
            data = response.json()
            print_info(f"Found {len(data)} style types")
            print_info("Response (first 3 items):")
            pretty_print_json(data[:3] if len(data) > 3 else data)
            return True, data
        else:
            print_error(f"Failed with status code: {response.status_code}")
            print(response.text)
            return False, None
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False, None


# =====================================================================
# Test 3: Get OB by Layout
# =====================================================================
def test_get_ob_by_layout(tenant_id: int = 3, layout_code: str = "EXAMPLE001"):
    print_test_header(f"GET /ob/get-ob-by-layout/{tenant_id}/{layout_code}")
    
    try:
        response = requests.get(
            f"{BASE_URL}/ob/get-ob-by-layout/{tenant_id}/{layout_code}",
            timeout=10
        )
        
        if response.status_code == 200:
            print_success(f"Status code: {response.status_code}")
            print_info("Response:")
            pretty_print_json(response.json())
            return True, response.json()
        elif response.status_code == 404:
            print_info(f"Layout code '{layout_code}' not found (404)")
            return False, None
        else:
            print_error(f"Failed with status code: {response.status_code}")
            print(response.text)
            return False, None
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False, None


# =====================================================================
# Test 4: Search Endpoint (without allocation data)
# =====================================================================
def test_search_basic():
    print_test_header("POST /ob/search (Basic Search)")
    
    payload = {
        "tenant_id": 3,
        "style_type": "LADIES BRIEF - TEZENIS BEACHWEAR",
        "allocation_data": False,
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
    
    print_info("Request payload:")
    pretty_print_json(payload)
    
    try:
        response = requests.post(
            f"{BASE_URL}/ob/search",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            print_success(f"Status code: {response.status_code}")
            data = response.json()
            print_info(f"Total OBs: {data.get('total_obs', 'N/A')}")
            print_info(f"Results returned: {data.get('no_of_results', 'N/A')}")
            print_info(f"Process time: {data.get('process_time', 'N/A')} seconds")
            print_info("First result:")
            if data.get('results'):
                pretty_print_json(data['results'][0])
            return True, data
        else:
            print_error(f"Failed with status code: {response.status_code}")
            print(response.text)
            return False, None
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False, None


# =====================================================================
# Test 5: Search Endpoint (with allocation data)
# =====================================================================
def test_search_with_allocation():
    print_test_header("POST /ob/search (With Allocation Data)")
    
    payload = {
        "tenant_id": 3,
        "style_type": "LADIES BRIEF - TEZENIS BEACHWEAR",
        "allocation_data": True,
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
    
    print_info("Request payload:")
    pretty_print_json(payload)
    
    try:
        response = requests.post(
            f"{BASE_URL}/ob/search",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            print_success(f"Status code: {response.status_code}")
            data = response.json()
            print_info(f"Total OBs: {data.get('total_obs', 'N/A')}")
            print_info(f"Results returned: {data.get('no_of_results', 'N/A')}")
            print_info(f"Process time: {data.get('process_time', 'N/A')} seconds")
            print_info("First result (with allocation):")
            if data.get('results'):
                pretty_print_json(data['results'][0])
            return True, data
        else:
            print_error(f"Failed with status code: {response.status_code}")
            print(response.text)
            return False, None
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False, None


# =====================================================================
# Test 6: Save Endpoint
# =====================================================================
def test_save():
    print_test_header("POST /ob/save")
    
    try:
        response = requests.post(
            f"{BASE_URL}/ob/save",
            json={},
            timeout=10
        )
        
        if response.status_code == 200:
            print_success(f"Status code: {response.status_code}")
            print_info("Response:")
            pretty_print_json(response.json())
            print_info("Note: This endpoint is not fully implemented yet")
            return True
        else:
            print_error(f"Failed with status code: {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


# =====================================================================
# Main Test Runner
# =====================================================================
def main():
    print(f"\n{BLUE}{'='*60}")
    print("OB-SIMILARITY SERVICE - ENDPOINT TESTING")
    print(f"{'='*60}{RESET}\n")
    print(f"Base URL: {BASE_URL}\n")
    
    results = {
        "passed": 0,
        "failed": 0,
        "total": 0
    }
    
    # Test 1: Status
    results["total"] += 1
    if test_status():
        results["passed"] += 1
    else:
        results["failed"] += 1
        print_error("Service is not running. Please start it first.")
        print_info("Run: uvicorn server:app --host 0.0.0.0 --port 8001")
        return
    
    # Test 2: Get Style Types
    results["total"] += 1
    success, style_types = test_get_style_types(tenant_id=3)
    if success:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 3: Get OB by Layout (will likely fail without valid layout_code)
    results["total"] += 1
    if test_get_ob_by_layout(tenant_id=3, layout_code="EXAMPLE001")[0]:
        results["passed"] += 1
    else:
        results["failed"] += 1
        print_info("This may fail if the layout_code doesn't exist in the database")
    
    # Test 4: Basic Search
    results["total"] += 1
    if test_search_basic()[0]:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 5: Search with Allocation
    results["total"] += 1
    if test_search_with_allocation()[0]:
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Test 6: Save
    results["total"] += 1
    if test_save():
        results["passed"] += 1
    else:
        results["failed"] += 1
    
    # Print summary
    print(f"\n{BLUE}{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}{RESET}")
    print(f"Total Tests: {results['total']}")
    print(f"{GREEN}Passed: {results['passed']}{RESET}")
    print(f"{RED}Failed: {results['failed']}{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")


if __name__ == "__main__":
    main()
