import numpy as np
from app.utils.embedding_extractor import compute_clip_embedding


def get_feature_vector_pretrained(image, i_type):
    """Return a CLIP embedding for the provided image.

    `image` may be a PIL Image, numpy array, bytes, or file-like object.
    `i_type` is kept for API compatibility but is not used by CLIP.
    Returns a 1D numpy.float32 L2-normalized vector.
    """
    return compute_clip_embedding(image, image_size=224)


def get_cosine_similarity(image_vector, vector):
    dot_product = np.dot(image_vector, vector)
    norm_image_vector = np.linalg.norm(image_vector)
    norm_vector = np.linalg.norm(vector)
    if norm_image_vector == 0 or norm_vector == 0:
        return 0.0
    return float(dot_product / (norm_image_vector * norm_vector))
