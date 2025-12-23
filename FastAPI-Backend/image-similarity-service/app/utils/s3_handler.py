# app/s3_helper.py

import boto3
import os
from botocore.exceptions import NoCredentialsError
from config import settings

# Initialize the S3 client
s3_client = boto3.client(
    "s3",
    aws_access_key_id=settings.AWS_ACCESS_KEY,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_REGION,
)

BUCKET_NAME = settings.AWS_BUCKET_NAME


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
