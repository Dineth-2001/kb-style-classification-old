#!/usr/bin/env python3
"""Download images from S3, compute CLIP embeddings (image_size=224), and upsert into Vector Database.

Assumptions:
- S3 object keys are like `<tenant_id>/<...>/<layout_code>.<ext>` or `<tenant_id>/<layout_code>.<ext>`.
- `style_type` will be inferred from the second path segment if present (otherwise left empty).
"""
import argparse
import os
from datetime import datetime

import boto3
from tqdm import tqdm

from config import settings
from app.utils.embedding_extractor import compute_clip_embedding
from app.database import pg_connect


IMG_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}


def is_image_key(key: str) -> bool:
    _, ext = os.path.splitext(key.lower())
    return ext in IMG_EXTS


def parse_key(key: str):
    parts = key.split('/')
    tenant_id = parts[0] if parts else 'unknown'
    layout_code = os.path.splitext(os.path.basename(key))[0]
    style_type = parts[1] if len(parts) > 2 else ''
    return tenant_id, layout_code, style_type


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--prefix', default='', help='S3 prefix to scan')
    p.add_argument('--limit', type=int, default=0, help='Max objects to process (0 = all)')
    p.add_argument('--dry-run', action='store_true')
    args = p.parse_args()

    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION,
    )

    bucket = settings.AWS_BUCKET_NAME

    # Postgres (pgvector)
    pg_connect.init_table()

    paginator = s3.get_paginator('list_objects_v2')
    page_iterator = paginator.paginate(Bucket=bucket, Prefix=args.prefix)

    processed = 0
    for page in page_iterator:
        for obj in page.get('Contents', []):
            key = obj['Key']
            if not is_image_key(key):
                continue

            tenant_id, layout_code, style_type = parse_key(key)
            image_url = f"https://{bucket}.s3.amazonaws.com/{key}"

            if args.dry_run:
                print('DRY:', key, tenant_id, layout_code, style_type)
            else:
                try:
                    resp = s3.get_object(Bucket=bucket, Key=key)
                    data = resp['Body'].read()
                    emb = compute_clip_embedding(data, image_size=224)

                    # upsert into Postgres pgvector table
                    pg_connect.upsert_vector(tenant_id, style_type or '', image_url, emb)
                    print('Upserted:', tenant_id, layout_code)
                except Exception as e:
                    print('Error processing', key, e)

            processed += 1
            if args.limit and processed >= args.limit:
                print('Reached limit', args.limit)
                return

    print('Done. Processed', processed)


if __name__ == '__main__':
    main()
