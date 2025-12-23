#!/usr/bin/env python3
"""Demo script: compute a CLIP embedding from a local image path or URL.

Usage:
  python tests/run_embedding_demo.py /path/to/image.jpg
  python tests/run_embedding_demo.py https://example.com/image.jpg
"""
import sys
import os
import requests
from io import BytesIO
import numpy as np

# When this script is run directly, Python sets sys.path[0] to the
# `tests/` directory which prevents `app` (at the project root) from
# being importable. Insert the project root (parent of `tests`) into
# `sys.path` so `from app...` works both when run as a script and as
# a module.
from pathlib import Path
proj_root = Path(__file__).resolve().parents[1]
proj_root_str = str(proj_root)
if proj_root_str not in sys.path:
    sys.path.insert(0, proj_root_str)

from app.utils.feature_extraction import get_feature_vector_pretrained


def load_image_input(path_or_url: str):
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        resp = requests.get(path_or_url, timeout=15)
        resp.raise_for_status()
        return BytesIO(resp.content)
    else:
        return open(path_or_url, "rb")


def main():
    if len(sys.argv) < 2:
        print("Provide a path or URL to an image")
        return
    src = sys.argv[1]
    with load_image_input(src) as fh:
        vec = get_feature_vector_pretrained(fh, i_type=None)

    print("embedding length:", len(vec))
    print("dtype:", vec.dtype)
    print("L2 norm:", np.linalg.norm(vec))


if __name__ == '__main__':
    main()
