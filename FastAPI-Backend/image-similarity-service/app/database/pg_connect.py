import os
import json
from datetime import datetime
from typing import List, Dict, Optional
import psycopg2
from psycopg2.extras import RealDictCursor
from config import settings


def get_conn():
    # expects settings to provide POSTGRES_URL or build from parts
    dsn = os.getenv('POSTGRES_DSN') or os.getenv('DATABASE_URL') or getattr(settings, 'POSTGRES_DSN', None)
    if not dsn:
        # fallback to components
        user = os.getenv('POSTGRES_USER', 'postgres')
        password = os.getenv('POSTGRES_PASSWORD', '')
        host = os.getenv('POSTGRES_HOST', 'localhost')
        port = os.getenv('POSTGRES_PORT', '5432')
        db = os.getenv('POSTGRES_DB', 'postgres')
        dsn = f"postgresql://{user}:{password}@{host}:{port}/{db}"
    return psycopg2.connect(dsn)


def init_table():
    """Create table for vectors if not exists. Requires pgvector extension enabled in DB."""
    sql = """
    CREATE TABLE IF NOT EXISTS fvector_pg (
        id SERIAL PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        style_number TEXT,
        image_url TEXT,
        feature_vector vector,
        date_created TIMESTAMP DEFAULT now()
    );
    CREATE INDEX IF NOT EXISTS idx_fvector_tenant_id ON fvector_pg(tenant_id);
    """
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
    finally:
        conn.close()


def upsert_vector(tenant_id, style_number, image_url, vector):
    """Insert vector into Postgres. `vector` is a 1D numpy array or list of floats.
    Returns the id of the inserted row.
    """
    vec_list = list(map(float, vector))
    vec_text = '[' + ','.join(f"{v:.6f}" for v in vec_list) + ']'

    sql = """
    INSERT INTO fvector_pg (tenant_id, style_number, image_url, feature_vector, date_created)
    VALUES (%s, %s, %s, %s::vector, now())
    RETURNING id;
    """
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (tenant_id, style_number, image_url, vec_text))
                result = cur.fetchone()
                return result[0] if result else None
    finally:
        conn.close()


def fetch_vectors(tenant_id: Optional[str] = None, style_number: Optional[str] = None) -> List[Dict]:
    """Return list of rows with columns: tenant_id, style_type, image_url, vec_text (string).
    
    Args:
        tenant_id: Optional tenant ID to filter by
        style_type: Optional style type to filter by
    """
    conditions = []
    params = []
    
    if tenant_id:
        conditions.append("tenant_id = %s")
        params.append(tenant_id)
    if style_number:
        conditions.append("style_number = %s")
        params.append(style_number)
    
    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    sql = f"SELECT id, tenant_id, style_number, image_url, feature_vector::text as vec_text FROM fvector_pg{where_clause}"

    conn = get_conn()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params if params else None)
                rows = cur.fetchall()
    finally:
        conn.close()
    return rows


def search_similar_vectors(query_vector, top_k: int = 10, style_number: Optional[str] = None, exclude_tenant_id: Optional[str] = None) -> List[Dict]:
    """
    Search for similar vectors using cosine similarity in PostgreSQL with pgvector.
    Searches ACROSS ALL tenants to find the most similar images.
    
    Args:
        query_vector: 1D numpy array or list of floats (the query embedding)
        top_k: Number of top similar results to return
        style_type: Optional style type to filter by
        exclude_tenant_id: Optional tenant ID to exclude from results 
        
    Returns:
        List of dicts with tenant_id, style_type, image_url, similarity_score, rank
    """
    vec_list = list(map(float, query_vector))
    vec_text = '[' + ','.join(f"{v:.6f}" for v in vec_list) + ']'
    
    # Build query with cosine similarity (1 - cosine_distance)
    # pgvector's <=> operator computes cosine distance, so similarity = 1 - distance
    conditions = []
    params = []
    
    if exclude_tenant_id:
        conditions.append("tenant_id != %s")
        params.append(exclude_tenant_id)
    
    if style_number:
        conditions.append("style_number = %s")
        params.append(style_number)
    
    where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
    
    sql = f"""
    SELECT 
        id,
        tenant_id,
        style_number,
        image_url,
        1 - (feature_vector <=> %s::vector) as similarity_score
    FROM fvector_pg
    {where_clause}
    ORDER BY feature_vector <=> %s::vector
    LIMIT %s;
    """
    
    conn = get_conn()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, [vec_text] + params + [vec_text, top_k])
                rows = cur.fetchall()
    finally:
        conn.close()
    
    # Add rank to results
    results = []
    for rank, row in enumerate(rows, start=1):
        results.append({
            'id': row['id'],
            'tenant_id': row['tenant_id'],
            'style_number': row.get('style_number'),
            'image_url': row['image_url'],
            'similarity_score': float(row['similarity_score']),
            'rank': rank
        })
    
    return results


def delete_vector(image_id: int) -> Optional[str]:
    """Delete a vector row by id.
    Returns the deleted row's image_url or None if not found.
    """
    sql_select = "SELECT image_url FROM fvector_pg WHERE id = %s"
    sql_delete = "DELETE FROM fvector_pg WHERE id = %s"

    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql_select, (image_id,))
                row = cur.fetchone()
                if not row:
                    return None
                image_url = row[0]
                cur.execute(sql_delete, (image_id,))
    finally:
        conn.close()
    return image_url


def update_vector(image_id: int, tenant_id: str, style_number: str, image_url: str, vector):
    """Update an existing vector by id.
    Returns True if successful, False if image_id not found.
    """
    vec_list = list(map(float, vector))
    vec_text = '[' + ','.join(f"{v:.6f}" for v in vec_list) + ']'
    
    sql = """
    UPDATE fvector_pg 
    SET tenant_id = %s, 
        style_number = %s, 
        image_url = %s, 
        feature_vector = %s::vector, 
        date_created = now()
    WHERE id = %s
    RETURNING image_url;
    """
    
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (tenant_id, style_number, image_url, vec_text, image_id))
                result = cur.fetchone()
                return result is not None
    finally:
        conn.close()


def get_vector_count(tenant_id: Optional[str] = None) -> int:
    """Get the total count of vectors in the database.
    
    Args:
        tenant_id: Optional tenant ID to filter count
        
    Returns:
        Count of vectors
    """
    if tenant_id:
        sql = "SELECT COUNT(*) FROM fvector_pg WHERE tenant_id = %s"
        params = (tenant_id,)
    else:
        sql = "SELECT COUNT(*) FROM fvector_pg"
        params = None
    
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                count = cur.fetchone()[0]
    finally:
        conn.close()
    return count


def bulk_upsert_vectors(vectors_data: List[Dict]):
    """
    Bulk insert multiple vectors into the database.
    
    Args:
        vectors_data: List of dicts with keys: tenant_id, style_number, image_url, feature_vector
    
    Returns:
        List of inserted IDs
    """
    if not vectors_data:
        return []
    
    sql = """
    INSERT INTO fvector_pg (tenant_id, style_number, image_url, feature_vector, date_created)
    VALUES (%s, %s, %s, %s::vector, now())
    RETURNING id;
    """
    
    conn = get_conn()
    inserted_ids = []
    try:
        with conn:
            with conn.cursor() as cur:
                for data in vectors_data:
                    vec_list = list(map(float, data['feature_vector']))
                    vec_text = '[' + ','.join(f"{v:.6f}" for v in vec_list) + ']'
                    cur.execute(sql, (
                        data['tenant_id'],
                        data.get('style_number', ''),
                        data['image_url'],
                        vec_text
                    ))
                    result = cur.fetchone()
                    if result:
                        inserted_ids.append(result[0])
    finally:
        conn.close()
    
    return inserted_ids
