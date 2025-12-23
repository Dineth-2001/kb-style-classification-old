import io
import time
import json
import numpy as np
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from app.utils.feature_extraction import get_feature_vector_pretrained
from app.database import pg_connect

class SearchResponse(BaseModel):
    tenant_id: str
    image_url: str
    similarity_score: float
    rank: int


router = APIRouter()


@router.post('/img/search-image')
async def search_image(tenant_id: str = Form(...),
                       image: UploadFile = File(...),
                       top_k: int = Form(10)):
    """Search for similar images using the provided image file.
    Returns a list of similar images with similarity scores.
    """
    try:
        data = await image.read()
        # get embedding for the uploaded image
        query_vec = get_feature_vector_pretrained(data, 'clip')

        # fetch all vectors from postgres
        rows = pg_connect.fetch_vectors()
        if not rows:
            return []

        # compute similarity scores
        vecs = []
        meta = []
        for row in rows:
            tenant = row.get('tenant_id')
            layout_code = row.get('layout_code')
            img_url = row.get('image_url')
            vec_text = row.get('vec_text')
            if not vec_text:
                continue
            # vec_text expected to be JSON array string or postgres text like '[0.1,0.2]'
            try:
                # try JSON first
                arr = json.loads(vec_text)
                vec = np.array(arr, dtype=np.float32)
            except Exception:
                try:
                    vec = np.fromstring(vec_text.strip('[]'), sep=',', dtype=np.float32)
                except Exception:
                    continue
            vecs.append(vec)
            meta.append({'tenant_id': tenant, 'layout_code': layout_code, 'image_url': img_url})

        if len(vecs) == 0:
            return []

        # stack vectors and filter by tenant id
        vecs = np.vstack(vecs)
        mask = [m['tenant_id'] == tenant_id for m in meta]
        if not any(mask):
            return []

        filtered_vecs = vecs[mask]
        filtered_meta = [m for i, m in enumerate(meta) if mask[i]]

        # normalize
        q = query_vec / (np.linalg.norm(query_vec) + 1e-10)
        fv = filtered_vecs / (np.linalg.norm(filtered_vecs, axis=1, keepdims=True) + 1e-10)

        sims = (fv @ q).tolist()

        # get top_k
        idxs = np.argsort(sims)[::-1][:top_k]
        results = []
        for rank, idx in enumerate(idxs, start=1):
            m = filtered_meta[idx]
            results.append(SearchResponse(tenant_id=m['tenant_id'],
                                          image_url=m['image_url'],
                                          similarity_score=float(sims[idx]),
                                          rank=rank))

        return results

    except Exception as e:
        raise HTTPException(500, str(e))
        idx = np.argsort(-sims)[:no_of_results]

        response_data = {}
        for rank, i in enumerate(idx):
            response_data[ids[i]] = {
                "tenant_id": tenants[i],
                "image_url": urls[i],
                "similarity_score": float(sims[i]),
                "rank": int(rank + 1),
            }

        end_time = time.time()
        process_time = end_time - start_time
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Error processing images: " + str(e)
        )

    return {
        "status": "success",
        "message": "Images searched successfully",
        "style_type": form_data.style_type,
        "tenant_id": form_data.tenant_id,
        "no_of_results": no_of_results,
        "total_images": count_fvectors,
        "process_time": process_time,
        "results": response_data,
    }
