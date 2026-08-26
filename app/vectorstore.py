import os
from langchain_huggingface import HuggingFaceEndpointEmbeddings

# Delegar el cómputo a la API externa Serverless para no saturar la RAM de Render (<512MB)
embeddings = HuggingFaceEndpointEmbeddings(
    model="sentence-transformers/all-MiniLM-L6-v2",
    huggingfacehub_api_token=os.environ.get("HF_TOKEN")
)
