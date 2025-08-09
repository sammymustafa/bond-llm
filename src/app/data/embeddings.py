
from sentence_transformers import SentenceTransformer
import numpy as np
from ..config import EMBEDDING_MODEL

_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model

def embed_texts(texts):
    model = get_model()
    v = model.encode(texts, normalize_embeddings=True)
    return np.asarray(v, dtype=np.float32)
