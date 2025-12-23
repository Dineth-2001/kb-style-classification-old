import os
import json
from datetime import datetime
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
        style_type TEXT,
        image_url TEXT,
        feature_vector vector,
        date_created TIMESTAMP DEFAULT now(),
        UNIQUE (tenant_id)
    );
    """
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql)
    finally:
        conn.close()


def upsert_vector(tenant_id, style_type, image_url, vector):
    """Upsert vector into Postgres. `vector` is a 1D numpy array or list of floats."""
    vec_list = list(map(float, vector))
    vec_text = '[' + ','.join(f"{v:.6f}" for v in vec_list) + ']'

    sql = """
    INSERT INTO fvector_pg (tenant_id, style_type, image_url, feature_vector, date_created)
    VALUES (%s, %s, %s, %s, %s::vector, now())
    ON CONFLICT (tenant_id) DO UPDATE SET
        style_type = EXCLUDED.style_type,
        image_url = EXCLUDED.image_url,
        feature_vector = EXCLUDED.feature_vector,
        date_created = now();
    """
    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql, (tenant_id, style_type, image_url, vec_text))
    finally:
        conn.close()


def fetch_vectors(style_type=None):
    """Return list of rows with columns: tenant_id, image_url, vec_text (string)."""
    if style_type:
        sql = "SELECT tenant_id, image_url, feature_vector::text as vec_text FROM fvector_pg WHERE style_type = %s"
        params = (style_type,)
    else:
        sql = "SELECT tenant_id, image_url, feature_vector::text as vec_text FROM fvector_pg"
        params = None

    conn = get_conn()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
    finally:
        conn.close()
    return rows


def delete_vector(tenant_id, layout_code):
    """Delete a vector row by tenant_id and layout_code (stored in style_type column).
    Returns the deleted row's image_url or None if not found.
    """
    sql_select = "SELECT image_url FROM fvector_pg WHERE tenant_id = %s AND style_type = %s LIMIT 1"
    sql_delete = "DELETE FROM fvector_pg WHERE tenant_id = %s AND style_type = %s"

    conn = get_conn()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(sql_select, (tenant_id, layout_code))
                row = cur.fetchone()
                if not row:
                    return None
                image_url = row[0]
                cur.execute(sql_delete, (tenant_id, layout_code))
    finally:
        conn.close()
    return image_url
