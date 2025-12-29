# app/s3_helper.py

import boto3
import os
from botocore.exceptions import NoCredentialsError, ClientError
from config import settings
from typing import List, Dict, Optional

# Initialize the S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)

BUCKET_NAME = settings.AWS_BUCKET_NAME

# Supported image extensions
IMG_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif', '.webp'}


def upload_to_s3(file_bytes, object_name):
    """
    Uploads a file to S3 and returns the file URL.
    """
    try:
        # Upload the file to S3
        s3_client.put_object(Bucket=BUCKET_NAME, Key=object_name, Body=file_bytes)
        # Create the file URL
        s3_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{object_name}"
        return s3_url
    except NoCredentialsError:
        raise Exception("AWS credentials not available")


def delete_from_s3(object_name):
    """
    Deletes a file from S3.
    """
    try:
        # Delete the file from S3
        s3_client.delete_object(Bucket=BUCKET_NAME, Key=object_name)
    except NoCredentialsError:
        raise Exception("AWS credentials not available")


def download_from_s3(object_name: str) -> bytes:
    """
    Downloads a file from S3 and returns the file bytes.
    
    Args:
        object_name: The S3 object key to download
        
    Returns:
        File content as bytes
    """
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=object_name)
        return response['Body'].read()
    except NoCredentialsError:
        raise Exception("AWS credentials not available")
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            raise Exception(f"Object {object_name} not found in bucket {BUCKET_NAME}")
        raise Exception(f"Error downloading from S3: {e}")


def download_from_s3_url(image_url: str) -> bytes:
    """
    Downloads a file from S3 using the full S3 URL.
    
    Args:
        image_url: Full S3 URL (e.g., https://bucket.s3.amazonaws.com/key)
        
    Returns:
        File content as bytes
    """
    # Extract object key from URL
    object_name = image_url.split(f"{BUCKET_NAME}.s3.amazonaws.com/")[-1]
    return download_from_s3(object_name)


def list_images_from_s3(prefix: str = "", tenant_id: Optional[str] = None) -> List[Dict]:
    """
    Lists all image files from S3 bucket with optional prefix and tenant_id filter.
    
    Args:
        prefix: S3 prefix to filter objects (e.g., 'images/' or 'tenant123/')
        tenant_id: Optional tenant ID to filter images. If provided, will look for images
                   in the path structure: <tenant_id>/... or filter by key prefix
        
    Returns:
        List of dicts containing: key, url, tenant_id, style_type, size, last_modified
    """
    try:
        # If tenant_id is provided and no prefix, use tenant_id as prefix
        search_prefix = prefix
        if tenant_id and not prefix:
            search_prefix = f"{tenant_id}/"
        elif tenant_id and prefix:
            search_prefix = f"{prefix}{tenant_id}/"
        
        paginator = s3_client.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=BUCKET_NAME, Prefix=search_prefix)
        
        images = []
        for page in page_iterator:
            for obj in page.get('Contents', []):
                key = obj['Key']
                # Check if it's an image file
                _, ext = os.path.splitext(key.lower())
                if ext not in IMG_EXTS:
                    continue
                
                # Parse tenant_id and style_type from key
                parsed_tenant_id, style_type = parse_s3_key(key)
                
                # Filter by tenant_id if specified
                if tenant_id and parsed_tenant_id != tenant_id:
                    continue
                
                image_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{key}"
                images.append({
                    'key': key,
                    'url': image_url,
                    'tenant_id': parsed_tenant_id,
                    'style_type': style_type,
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'].isoformat()
                })
        
        return images
        
    except NoCredentialsError:
        raise Exception("AWS credentials not available")
    except ClientError as e:
        raise Exception(f"Error listing S3 objects: {e}")


def parse_s3_key(key: str) -> tuple:
    """
    Parse S3 object key to extract tenant_id and style_type.
    
    Expected key formats:
    - <tenant_id>/<filename>.<ext>
    - <tenant_id>/<style_type>/<filename>.<ext>
    - <tenant_id>/<style_type>/<...>/<filename>.<ext>
    
    Args:
        key: S3 object key
        
    Returns:
        Tuple of (tenant_id, style_type)
    """
    parts = key.split('/')
    tenant_id = parts[0] if parts else 'unknown'
    style_type = parts[1] if len(parts) > 2 else ''
    return tenant_id, style_type


def get_image_url(object_key: str) -> str:
    """
    Generate the full S3 URL for an object key.
    
    Args:
        object_key: The S3 object key
        
    Returns:
        Full S3 URL
    """
    return f"https://{BUCKET_NAME}.s3.amazonaws.com/{object_key}"


def get_image_by_tenant_id(tenant_id: str) -> Optional[bytes]:
    """
    Fetch an image from S3 using the tenant_id.
    
    Images are expected to be stored under the tenant_id prefix:
    - <tenant_id>/<filename>.<ext>
    - <tenant_id>/<style_type>/<filename>.<ext>
    
    This function finds the first image under the tenant's prefix and returns it.
    
    Args:
        tenant_id: The tenant ID to fetch image for
        
    Returns:
        Image bytes if found, None otherwise
    """
    try:
        # List images under tenant_id prefix
        images = list_images_from_s3(tenant_id=tenant_id)
        
        if not images:
            return None
        
        # Get the first image
        first_image = images[0]
        image_key = first_image['key']
        
        # Download and return the image
        return download_from_s3(image_key)
        
    except Exception as e:
        raise Exception(f"Error fetching image for tenant {tenant_id}: {e}")


def get_images_by_tenant_ids(tenant_ids: List[str]) -> Dict[str, Optional[bytes]]:
    """
    Fetch images from S3 for multiple tenant_ids.
    
    Args:
        tenant_ids: List of tenant IDs to fetch images for
        
    Returns:
        Dict mapping tenant_id to image bytes (or None if not found)
    """
    result = {}
    for tenant_id in tenant_ids:
        try:
            result[tenant_id] = get_image_by_tenant_id(tenant_id)
        except Exception:
            result[tenant_id] = None
    return result


# def list_all_images_from_s3(prefix: str = "") -> List[Dict]:
#     """
#     Lists ALL image files from S3 bucket (no tenant filter).
    
#     Args:
#         prefix: Optional S3 prefix to filter objects
        
#     Returns:
#         List of dicts containing: key, url, tenant_id, style_type, size, last_modified
#     """
#     try:
#         paginator = s3_client.get_paginator('list_objects_v2')
#         page_iterator = paginator.paginate(Bucket=BUCKET_NAME, Prefix=prefix)
        
#         images = []
#         for page in page_iterator:
#             for obj in page.get('Contents', []):
#                 key = obj['Key']
#                 # Check if it's an image file
#                 _, ext = os.path.splitext(key.lower())
#                 if ext not in IMG_EXTS:
#                     continue
                
#                 # Parse tenant_id and style_type from key
#                 parsed_tenant_id, style_type = parse_s3_key(key)
                
#                 image_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{key}"
#                 images.append({
#                     'key': key,
#                     'url': image_url,
#                     'tenant_id': parsed_tenant_id,
#                     'style_type': style_type,
#                     'size': obj['Size'],
#                     'last_modified': obj['LastModified'].isoformat()
#                 })
        
#         return images
        
#     except NoCredentialsError:
#         raise Exception("AWS credentials not available")
#     except ClientError as e:
#         raise Exception(f"Error listing S3 objects: {e}")
