#!/usr/bin/env python3
"""
Test suite for the Image Similarity Service API.

This script tests the main functionalities:
1. Save image with embedding (store in S3 + vector DB)
2. Create embeddings from S3 images
3. Find similar tenants by uploading an image
4. Search images by URL

Usage:
  # Run all tests
  python tests/test_api.py

  # Run specific test
  python tests/test_api.py test_find_similar_tenants

  # Run with custom server URL
  python tests/test_api.py --server http://localhost:5000
"""
import sys
import os
import argparse
import requests
import json
from pathlib import Path
from io import BytesIO
import time

# Add project root to path
proj_root = Path(__file__).resolve().parents[1]
if str(proj_root) not in sys.path:
    sys.path.insert(0, str(proj_root))


# Default server URL
DEFAULT_SERVER = "http://localhost:5000"


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_success(msg):
    print(f"{Colors.GREEN}✓ {msg}{Colors.RESET}")


def print_error(msg):
    print(f"{Colors.RED}✗ {msg}{Colors.RESET}")


def print_info(msg):
    print(f"{Colors.BLUE}ℹ {msg}{Colors.RESET}")


def print_header(msg):
    print(f"\n{Colors.BOLD}{Colors.YELLOW}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.YELLOW}{msg}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.YELLOW}{'='*60}{Colors.RESET}\n")


def get_test_image():
    """Get a test image. Downloads a sample image if none exists locally."""
    test_images_dir = proj_root / "tests" / "test_images"
    test_images_dir.mkdir(exist_ok=True)
    
    test_image_path = test_images_dir / "test_image.jpg"
    
    if not test_image_path.exists():
        # Download a sample image
        print_info("Downloading sample test image...")
        sample_url = "https://picsum.photos/224/224"
        try:
            resp = requests.get(sample_url, timeout=30)
            resp.raise_for_status()
            with open(test_image_path, "wb") as f:
                f.write(resp.content)
            print_success(f"Downloaded test image to {test_image_path}")
        except Exception as e:
            print_error(f"Failed to download test image: {e}")
            # Create a simple test image using PIL if available
            try:
                from PIL import Image
                import numpy as np
                img_array = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
                img = Image.fromarray(img_array)
                img.save(test_image_path)
                print_success(f"Created random test image at {test_image_path}")
            except ImportError:
                print_error("PIL not available. Please provide a test image.")
                return None
    
    return test_image_path


def test_server_health(server_url):
    """Test if the server is running"""
    print_header("Testing Server Health")
    
    try:
        resp = requests.get(f"{server_url}/status", timeout=5)
        if resp.status_code == 200:
            print_success(f"Server is running at {server_url}")
            print(f"   Response: {resp.json()}")
            return True
        else:
            print_error(f"Server returned status {resp.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_error(f"Cannot connect to server at {server_url}")
        print_info("Make sure the server is running: python server.py")
        return False
    except Exception as e:
        print_error(f"Error checking server health: {e}")
        return False


def test_save_image(server_url, image_path, tenant_id, style_type="test"):
    """Test saving an image with embedding"""
    print_header("Testing Save Image Endpoint")
    
    try:
        with open(image_path, "rb") as f:
            files = {"image": ("test_image.jpg", f, "image/jpeg")}
            data = {
                "tenant_id": tenant_id,
                "style_number": style_type
            }
            
            print_info(f"Saving image for tenant_id: {tenant_id}")
            start_time = time.time()
            
            resp = requests.post(
                f"{server_url}/img/save-image",
                files=files,
                data=data,
                timeout=60
            )
            
            elapsed = time.time() - start_time
            
            if resp.status_code == 200:
                result = resp.json()
                print_success(f"Image saved successfully in {elapsed:.2f}s")
                print(f"   Response: {json.dumps(result, indent=2)}")
                return True
            else:
                print_error(f"Failed to save image: {resp.status_code}")
                print(f"   Response: {resp.text}")
                return False
                
    except Exception as e:
        print_error(f"Error saving image: {e}")
        return False


def test_create_embeddings_from_s3(server_url, tenant_id, prefix="", limit=5):
    """Test creating embeddings from S3 images"""
    print_header("Testing Create Embeddings from S3")
    
    try:
        data = {
            "tenant_id": tenant_id,
            "prefix": prefix,
            "limit": limit
        }
        
        print_info(f"Creating embeddings for tenant_id: {tenant_id}")
        start_time = time.time()
        
        resp = requests.post(
            f"{server_url}/img/create-embeddings-from-s3",
            data=data,
            timeout=300  # 5 min timeout for batch processing
        )
        
        elapsed = time.time() - start_time
        
        if resp.status_code == 200:
            result = resp.json()
            print_success(f"Embeddings created in {elapsed:.2f}s")
            print(f"   Status: {result.get('status')}")
            print(f"   Processed: {result.get('processed_count')}")
            print(f"   Failed: {result.get('failed_count')}")
            return True
        else:
            print_error(f"Failed to create embeddings: {resp.status_code}")
            print(f"   Response: {resp.text}")
            return False
            
    except Exception as e:
        print_error(f"Error creating embeddings: {e}")
        return False


def test_find_similar_tenants(server_url, image_path, top_k=10, include_image_data=False):
    """Test finding similar tenants by uploading an image"""
    print_header("Testing Find Similar Tenants")
    
    try:
        with open(image_path, "rb") as f:
            files = {"image": ("query_image.jpg", f, "image/jpeg")}
            data = {
                "top_k": top_k,
                "include_image_data": str(include_image_data).lower()
            }
            
            print_info(f"Searching for top {top_k} similar tenants...")
            start_time = time.time()
            
            resp = requests.post(
                f"{server_url}/img/find-similar-tenants",
                files=files,
                data=data,
                timeout=60
            )
            
            elapsed = time.time() - start_time
            
            if resp.status_code == 200:
                results = resp.json()
                print_success(f"Found {len(results)} similar tenants in {elapsed:.2f}s")
                
                if results:
                    print("\n   Top results:")
                    for r in results[:5]:  # Show top 5
                        print(f"   #{r['rank']}: tenant_id={r['tenant_id']}, "
                              f"similarity={r['similarity_score']:.4f}, "
                              f"url={r['image_url'][:50]}...")
                else:
                    print_info("No similar images found in database")
                    
                return True
            else:
                print_error(f"Failed to find similar tenants: {resp.status_code}")
                print(f"   Response: {resp.text}")
                return False
                
    except Exception as e:
        print_error(f"Error finding similar tenants: {e}")
        return False


def test_search_image(server_url, image_path, top_k=10):
    """Test search image endpoint"""
    print_header("Testing Search Image")
    
    try:
        with open(image_path, "rb") as f:
            files = {"image": ("query_image.jpg", f, "image/jpeg")}
            data = {"top_k": top_k}
            
            print_info(f"Searching for top {top_k} similar images...")
            start_time = time.time()
            
            resp = requests.post(
                f"{server_url}/img/search-image",
                files=files,
                data=data,
                timeout=60
            )
            
            elapsed = time.time() - start_time
            
            if resp.status_code == 200:
                results = resp.json()
                print_success(f"Found {len(results)} similar images in {elapsed:.2f}s")
                
                if results:
                    print("\n   Results:")
                    for r in results[:5]:
                        print(f"   #{r['rank']}: tenant_id={r['tenant_id']}, "
                              f"similarity={r['similarity_score']:.4f}")
                        
                return True
            else:
                print_error(f"Failed to search: {resp.status_code}")
                print(f"   Response: {resp.text}")
                return False
                
    except Exception as e:
        print_error(f"Error searching: {e}")
        return False


def test_list_s3_images(server_url, tenant_id):
    """Test listing S3 images for a tenant"""
    print_header("Testing List S3 Images")
    
    try:
        params = {"tenant_id": tenant_id}
        
        print_info(f"Listing images for tenant_id: {tenant_id}")
        
        resp = requests.get(
            f"{server_url}/img/list-s3-images",
            params=params,
            timeout=30
        )
        
        if resp.status_code == 200:
            result = resp.json()
            print_success(f"Found {result.get('count', 0)} images")
            
            images = result.get('images', [])
            if images:
                print("\n   Images:")
                for img in images[:5]:
                    print(f"   - {img['key']} ({img['size']} bytes)")
                    
            return True
        else:
            print_error(f"Failed to list images: {resp.status_code}")
            print(f"   Response: {resp.text}")
            return False
            
    except Exception as e:
        print_error(f"Error listing images: {e}")
        return False


def test_embedding_stats(server_url, tenant_id=None):
    """Test getting embedding statistics"""
    print_header("Testing Embedding Stats")
    
    try:
        params = {}
        if tenant_id:
            params["tenant_id"] = tenant_id
            
        resp = requests.get(
            f"{server_url}/img/embedding-stats",
            params=params,
            timeout=10
        )
        
        if resp.status_code == 200:
            result = resp.json()
            print_success("Got embedding statistics")
            print(f"   Total embeddings: {result.get('total_embeddings')}")
            if tenant_id:
                print(f"   Tenant embeddings: {result.get('tenant_embeddings')}")
            return True
        else:
            print_error(f"Failed to get stats: {resp.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error getting stats: {e}")
        return False


def test_upload_image_only(server_url, image_path, tenant_id):
    """Test uploading an image to S3 only (no embedding)"""
    print_header("Testing Upload Image Only Endpoint")
    
    try:
        with open(image_path, "rb") as f:
            files = {"image": ("upload_test.jpg", f, "image/jpeg")}
            data = {"tenant_id": tenant_id}
            
            print_info(f"Uploading image for tenant_id: {tenant_id}")
            start_time = time.time()
            
            resp = requests.post(
                f"{server_url}/img/upload-image",
                files=files,
                data=data,
                timeout=60
            )
            
            elapsed = time.time() - start_time
            
            if resp.status_code == 200:
                result = resp.json()
                print_success(f"Image uploaded successfully in {elapsed:.2f}s")
                print(f"   Message: {result.get('message')}")
                print(f"   Tenant ID: {result.get('tenant_id')}")
                print(f"   Image URL: {result.get('image_url')}")
                return True
            else:
                print_error(f"Failed to upload image: {resp.status_code}")
                print(f"   Response: {resp.text}")
                return False
                
    except Exception as e:
        print_error(f"Error uploading image: {e}")
        return False


def test_search_and_store(server_url, image_path, tenant_id, style_type="modern", top_k=5):
    """Test searching for similar images and storing the uploaded image"""
    print_header("Testing Search and Store Endpoint")
    
    try:
        with open(image_path, "rb") as f:
            files = {"image": ("search_store_test.jpg", f, "image/jpeg")}
            data = {
                "tenant_id": tenant_id,
                "style_number": style_type,
                "top_k": top_k
            }
            
            print_info(f"Searching and storing image for tenant_id: {tenant_id}")
            start_time = time.time()
            
            resp = requests.post(
                f"{server_url}/img/search-and-store",
                files=files,
                data=data,
                timeout=120
            )
            
            elapsed = time.time() - start_time
            
            if resp.status_code == 200:
                result = resp.json()
                print_success(f"Search and store completed in {elapsed:.2f}s")
                print(f"   Message: {result.get('message')}")
                print(f"   Uploaded Tenant ID: {result.get('uploaded_tenant_id')}")
                print(f"   Image URL: {result.get('image_url')}")
                
                similar = result.get('similar_images', [])
                print(f"   Similar Images Found: {len(similar)}")
                
                if similar:
                    print("\n   Top similar images:")
                    for i, img in enumerate(similar[:3]):
                        print(f"      {i+1}. tenant_id={img['tenant_id']}, "
                              f"similarity={img['similarity']:.4f}, "
                              f"style={img.get('style_type', 'N/A')}")
                return True
            else:
                print_error(f"Failed to search and store: {resp.status_code}")
                print(f"   Response: {resp.text}")
                return False
                
    except Exception as e:
        print_error(f"Error in search and store: {e}")
        return False


def run_all_tests(server_url, tenant_id="test_tenant_001"):
    """Run all tests"""
    print(f"\n{Colors.BOLD}Image Similarity Service - API Tests{Colors.RESET}")
    print(f"Server: {server_url}")
    print(f"Test Tenant ID: {tenant_id}")
    
    # Get test image
    test_image = get_test_image()
    if not test_image:
        print_error("No test image available. Exiting.")
        return False
    
    results = {}
    
    # Test 1: Server health
    results["server_health"] = test_server_health(server_url)
    if not results["server_health"]:
        print_error("Server not available. Skipping remaining tests.")
        return False
    
    # Test 2: Embedding stats (before adding data)
    results["embedding_stats_before"] = test_embedding_stats(server_url)
    
    # Test 3: Save image
    results["save_image"] = test_save_image(server_url, test_image, tenant_id)
    
    # Test 4: Save another image with different tenant
    results["save_image_2"] = test_save_image(server_url, test_image, f"{tenant_id}_2", "casual")
    
    # Test 5: Embedding stats (after adding data)
    results["embedding_stats_after"] = test_embedding_stats(server_url, tenant_id)
    
    # Test 6: Find similar tenants
    results["find_similar_tenants"] = test_find_similar_tenants(server_url, test_image, top_k=5)
    
    # Test 7: Search image
    results["search_image"] = test_search_image(server_url, test_image, top_k=5)
    
    # Test 8: List S3 images
    results["list_s3_images"] = test_list_s3_images(server_url, tenant_id)
    
    # Test 9: Upload image only (no embedding)
    results["upload_image_only"] = test_upload_image_only(server_url, test_image, f"{tenant_id}_upload")
    
    # Test 10: Search and store
    results["search_and_store"] = test_search_and_store(server_url, test_image, f"{tenant_id}_search_store")
    
    # Summary
    print_header("Test Summary")
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = f"{Colors.GREEN}PASSED{Colors.RESET}" if passed_test else f"{Colors.RED}FAILED{Colors.RESET}"
        print(f"   {test_name}: {status}")
    
    print(f"\n   Total: {passed}/{total} tests passed")
    
    return passed == total


def main():
    parser = argparse.ArgumentParser(description="Test Image Similarity Service API")
    parser.add_argument("test", nargs="?", default="all", 
                       help="Specific test to run (default: all)")
    parser.add_argument("--server", default=DEFAULT_SERVER,
                       help=f"Server URL (default: {DEFAULT_SERVER})")
    parser.add_argument("--tenant-id", default="test_tenant_001",
                       help="Tenant ID to use for tests")
    parser.add_argument("--image", default=None,
                       help="Path to test image")
    
    args = parser.parse_args()
    
    # Get test image
    if args.image:
        test_image = Path(args.image)
        if not test_image.exists():
            print_error(f"Image not found: {test_image}")
            sys.exit(1)
    else:
        test_image = get_test_image()
        if not test_image:
            print_error("No test image available.")
            sys.exit(1)
    
    # Run tests
    if args.test == "all":
        success = run_all_tests(args.server, args.tenant_id)
    elif args.test == "health":
        success = test_server_health(args.server)
    elif args.test == "save":
        success = test_save_image(args.server, test_image, args.tenant_id)
    elif args.test == "similar":
        success = test_find_similar_tenants(args.server, test_image)
    elif args.test == "search":
        success = test_search_image(args.server, test_image)
    elif args.test == "stats":
        success = test_embedding_stats(args.server, args.tenant_id)
    elif args.test == "list":
        success = test_list_s3_images(args.server, args.tenant_id)
    elif args.test == "upload":
        success = test_upload_image_only(args.server, test_image, args.tenant_id)
    elif args.test == "searchstore":
        success = test_search_and_store(args.server, test_image, args.tenant_id)
    else:
        print_error(f"Unknown test: {args.test}")
        print("Available tests: all, health, save, similar, search, stats, list, upload, searchstore")
        sys.exit(1)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
