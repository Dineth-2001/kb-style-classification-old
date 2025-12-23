#!/usr/bin/env python3
"""Test S3 upload/delete using botocore Stubber without real AWS creds."""
import boto3
from botocore.stub import Stubber
from io import BytesIO

from app.utils import s3_handler


def test_upload_and_delete():
    # create a client and attach a Stubber
    client = boto3.client('s3', region_name='us-east-1')
    stubber = Stubber(client)

    # replace the module client with our stubbed client
    s3_handler.s3_client = client

    # stubbed responses
    stubber.add_response('put_object', {}, {'Bucket': s3_handler.BUCKET_NAME, 'Key': 'test/key.jpg', 'Body': b'abc'})
    stubber.add_response('delete_object', {}, {'Bucket': s3_handler.BUCKET_NAME, 'Key': 'test/key.jpg'})

    stubber.activate()
    try:
        url = s3_handler.upload_to_s3(b'abc', 'test/key.jpg')
        print('upload returned URL:', url)
        s3_handler.delete_from_s3('test/key.jpg')
        print('delete called successfully')
    finally:
        stubber.deactivate()


if __name__ == '__main__':
    test_upload_and_delete()
