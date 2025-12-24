#!/usr/bin/env python3
"""
Interactive test script to manually test the Image Similarity Service.

This script provides an interactive menu to test different endpoints.

Usage:
  python tests/test_interactive.py
  python tests/test_interactive.py --server http://localhost:5000
"""
import sys
import os
import argparse
import requests
import json
from pathlib import Path

# Add project root to path
proj_root = Path(__file__).resolve().parents[1]
if str(proj_root) not in sys.path:
    sys.path.insert(0, str(proj_root))


DEFAULT_SERVER = "http://localhost:5000"


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def print_menu():
    print("\n" + "="*60)
    print("  Image Similarity Service - Interactive Test Menu")
    print("="*60)
    print("""
    1.  Check server health
    2.  Save image (upload + create embedding)
    3.  Find similar tenants (main search)
    4.  Search by image file
    5.  Search by image URL
    6.  Create embeddings from S3
    7.  List S3 images
    8.  Get embedding stats
    9.  Delete image by tenant ID
    10. Upload image only (S3 only, no embedding)
    11. Search and store (search + save image & embedding)
    0.  Exit
    """)


def check_health(server_url):
    print("\n--- Checking Server Health ---")
    try:
        resp = requests.get(f"{server_url}/status", timeout=5)
        print(f"Status: {resp.status_code}")
        print(f"Response: {json.dumps(resp.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")


def save_image(server_url):
    print("\n--- Save Image ---")
    image_path = input("Enter image path: ").strip()
    tenant_id = input("Enter tenant ID: ").strip()
    style_type = input("Enter style type (optional): ").strip() or "default"
    
    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        return
    
    try:
        with open(image_path, "rb") as f:
            files = {"image": (os.path.basename(image_path), f, "image/jpeg")}
            data = {"tenant_id": tenant_id, "style_type": style_type}
            
            print("Uploading and creating embedding...")
            resp = requests.post(f"{server_url}/img/save-image", files=files, data=data, timeout=60)
            
            print(f"Status: {resp.status_code}")
            print(f"Response: {json.dumps(resp.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")


def find_similar_tenants(server_url):
    print("\n--- Find Similar Tenants ---")
    image_path = input("Enter image path: ").strip()
    top_k = input("Number of results (default 10): ").strip() or "10"
    include_data = input("Include image data? (y/n, default n): ").strip().lower() == 'y'
    
    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        return
    
    try:
        with open(image_path, "rb") as f:
            files = {"image": (os.path.basename(image_path), f, "image/jpeg")}
            data = {"top_k": int(top_k), "include_image_data": str(include_data).lower()}
            
            print("Searching for similar tenants...")
            resp = requests.post(f"{server_url}/img/find-similar-tenants", files=files, data=data, timeout=60)
            
            print(f"Status: {resp.status_code}")
            
            if resp.status_code == 200:
                results = resp.json()
                print(f"\nFound {len(results)} similar tenants:\n")
                for r in results:
                    print(f"  #{r['rank']}: tenant_id={r['tenant_id']}")
                    print(f"         similarity={r['similarity_score']:.4f}")
                    print(f"         image_url={r['image_url']}")
                    print()
            else:
                print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")


def search_image(server_url):
    print("\n--- Search by Image File ---")
    image_path = input("Enter image path: ").strip()
    top_k = input("Number of results (default 10): ").strip() or "10"
    
    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        return
    
    try:
        with open(image_path, "rb") as f:
            files = {"image": (os.path.basename(image_path), f, "image/jpeg")}
            data = {"top_k": int(top_k)}
            
            print("Searching...")
            resp = requests.post(f"{server_url}/img/search-image", files=files, data=data, timeout=60)
            
            print(f"Status: {resp.status_code}")
            print(f"Response: {json.dumps(resp.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")


def search_by_url(server_url):
    print("\n--- Search by Image URL ---")
    image_url = input("Enter image URL: ").strip()
    top_k = input("Number of results (default 10): ").strip() or "10"
    
    try:
        data = {"image_url": image_url, "top_k": int(top_k)}
        
        print("Searching...")
        resp = requests.post(f"{server_url}/img/search-by-url", data=data, timeout=60)
        
        print(f"Status: {resp.status_code}")
        print(f"Response: {json.dumps(resp.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")


def create_embeddings_from_s3(server_url):
    print("\n--- Create Embeddings from S3 ---")
    tenant_id = input("Enter tenant ID: ").strip()
    prefix = input("S3 prefix (optional): ").strip()
    limit = input("Limit (0 for all): ").strip() or "0"
    
    try:
        data = {"tenant_id": tenant_id, "prefix": prefix, "limit": int(limit)}
        
        print("Creating embeddings (this may take a while)...")
        resp = requests.post(f"{server_url}/img/create-embeddings-from-s3", data=data, timeout=300)
        
        print(f"Status: {resp.status_code}")
        print(f"Response: {json.dumps(resp.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")


def list_s3_images(server_url):
    print("\n--- List S3 Images ---")
    tenant_id = input("Enter tenant ID: ").strip()
    prefix = input("S3 prefix (optional): ").strip()
    
    try:
        params = {"tenant_id": tenant_id, "prefix": prefix}
        
        resp = requests.get(f"{server_url}/img/list-s3-images", params=params, timeout=30)
        
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            result = resp.json()
            print(f"\nFound {result.get('count', 0)} images:\n")
            for img in result.get('images', []):
                print(f"  - {img['key']} ({img['size']} bytes)")
        else:
            print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")


def get_embedding_stats(server_url):
    print("\n--- Embedding Stats ---")
    tenant_id = input("Enter tenant ID (optional, press Enter for all): ").strip()
    
    try:
        params = {}
        if tenant_id:
            params["tenant_id"] = tenant_id
            
        resp = requests.get(f"{server_url}/img/embedding-stats", params=params, timeout=10)
        
        print(f"Status: {resp.status_code}")
        print(f"Response: {json.dumps(resp.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")


def delete_image(server_url):
    print("\n--- Delete Image by Tenant ID ---")
    tenant_id = input("Enter tenant ID to delete: ").strip()
    
    confirm = input(f"Are you sure you want to delete tenant '{tenant_id}'? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    try:
        data = {"tenant_id": tenant_id}
        resp = requests.delete(f"{server_url}/img/delete-image", data=data, timeout=30)
        
        print(f"Status: {resp.status_code}")
        print(f"Response: {json.dumps(resp.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")


def upload_image_only(server_url):
    print("\n--- Upload Image Only (S3 only, no embedding) ---")
    image_path = input("Enter image path: ").strip()
    tenant_id = input("Enter tenant ID: ").strip()
    
    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        return
    
    try:
        with open(image_path, "rb") as f:
            files = {"image": (os.path.basename(image_path), f, "image/jpeg")}
            data = {"tenant_id": tenant_id}
            
            print("Uploading image to S3...")
            resp = requests.post(f"{server_url}/img/upload-image", files=files, data=data, timeout=60)
            
            print(f"Status: {resp.status_code}")
            print(f"Response: {json.dumps(resp.json(), indent=2)}")
    except Exception as e:
        print(f"Error: {e}")


def search_and_store(server_url):
    print("\n--- Search and Store (Search + Save Image & Embedding) ---")
    image_path = input("Enter image path: ").strip()
    tenant_id = input("Enter tenant ID for new image: ").strip()
    style_type = input("Enter style type (optional): ").strip() or "default"
    top_k = input("Number of similar results (default 10): ").strip() or "10"
    
    if not os.path.exists(image_path):
        print(f"Error: File not found: {image_path}")
        return
    
    try:
        with open(image_path, "rb") as f:
            files = {"image": (os.path.basename(image_path), f, "image/jpeg")}
            data = {
                "tenant_id": tenant_id,
                "style_type": style_type,
                "top_k": int(top_k)
            }
            
            print("Searching for similar images and storing...")
            resp = requests.post(f"{server_url}/img/search-and-store", files=files, data=data, timeout=120)
            
            print(f"Status: {resp.status_code}")
            
            if resp.status_code == 200:
                result = resp.json()
                print(f"\nMessage: {result.get('message')}")
                print(f"Uploaded Tenant ID: {result.get('uploaded_tenant_id')}")
                print(f"Image URL: {result.get('image_url')}")
                
                similar = result.get('similar_images', [])
                print(f"\nFound {len(similar)} similar images:")
                for i, img in enumerate(similar):
                    print(f"  {i+1}. tenant_id={img['tenant_id']}, similarity={img['similarity']:.4f}")
            else:
                print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")


def main():
    parser = argparse.ArgumentParser(description="Interactive test for Image Similarity Service")
    parser.add_argument("--server", default=DEFAULT_SERVER, help=f"Server URL (default: {DEFAULT_SERVER})")
    args = parser.parse_args()
    
    server_url = args.server
    print(f"Using server: {server_url}")
    
    while True:
        print_menu()
        choice = input("Enter choice: ").strip()
        
        if choice == "1":
            check_health(server_url)
        elif choice == "2":
            save_image(server_url)
        elif choice == "3":
            find_similar_tenants(server_url)
        elif choice == "4":
            search_image(server_url)
        elif choice == "5":
            search_by_url(server_url)
        elif choice == "6":
            create_embeddings_from_s3(server_url)
        elif choice == "7":
            list_s3_images(server_url)
        elif choice == "8":
            get_embedding_stats(server_url)
        elif choice == "9":
            delete_image(server_url)
        elif choice == "10":
            upload_image_only(server_url)
        elif choice == "11":
            search_and_store(server_url)
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid choice. Please try again.")
        
        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
