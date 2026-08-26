import os
from langchain_huggingface import HuggingFaceEndpointEmbeddings


def get_embeddings():
    """Inicialización diferida (Lazy Initialization) para evitar bloqueos durante el arranque de FastAPI."""
    return HuggingFaceEndpointEmbeddings(
        model="sentence-transformers/all-MiniLM-L6-v2",
        huggingfacehub_api_token=os.environ.get("HF_TOKEN")
    )

