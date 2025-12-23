import numpy as np
import io
from PIL import Image

import torch
from transformers import CLIPModel, CLIPProcessor


# --- CLIP extractor -------------------------------------------------
def _load_clip_model(model_name: str = "openai/clip-vit-large-patch14", device: str = None):
    """Lazy-load CLIP model and processor. Returns (model, processor, device)."""
    global _clip_model, _clip_processor, _clip_device, _clip_model_name
    try:
        _clip_model
    except NameError:
        _clip_model = None
        _clip_processor = None
        _clip_device = None
        _clip_model_name = None

    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    if _clip_model is None or _clip_model_name != model_name or _clip_device != device:
        _clip_model = CLIPModel.from_pretrained(model_name).to(device)
        _clip_processor = CLIPProcessor.from_pretrained(model_name)
        _clip_device = device
        _clip_model_name = model_name

    return _clip_model, _clip_processor, _clip_device


def compute_clip_embedding(image_input, image_size: int = 224, model_name: str = "openai/clip-vit-large-patch14"):
    """Compute CLIP image embedding for a single image.

    image_input: PIL.Image, numpy array (H,W,3), bytes, or BytesIO
    Returns: 1-D numpy.float32 L2-normalized vector
    """
    model, processor, device = _load_clip_model(model_name)

    # Normalize input to PIL Image
    if isinstance(image_input, (bytes, bytearray)):
        img = Image.open(io.BytesIO(image_input)).convert("RGB")
    elif hasattr(image_input, "read"):
        img = Image.open(image_input).convert("RGB")
    elif isinstance(image_input, Image.Image):
        img = image_input.convert("RGB")
    else:
        # assume numpy array
        img = Image.fromarray(image_input.astype("uint8"), mode="RGB")

    # Processor will resize/center-crop as needed
    inputs = processor(images=img, return_tensors="pt")
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        img_feats = model.get_image_features(**{"pixel_values": inputs["pixel_values"]})
        img_feats = img_feats / img_feats.norm(p=2, dim=-1, keepdim=True)
        vec = img_feats.cpu().numpy().reshape(-1).astype(np.float32)

    # ensure L2-normalized
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec

