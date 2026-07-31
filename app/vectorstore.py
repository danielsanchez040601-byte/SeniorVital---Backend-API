import os
from langchain_community.vectorstores import PGVector
from langchain_openai import OpenAIEmbeddings

# Obtenemos la conexión de la BD y la API Key de OpenRouter
db_url = os.environ.get("DATABASE_URL")
openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")

if not db_url or not openrouter_api_key:
    raise ValueError("DATABASE_URL y OPENROUTER_API_KEY son requeridas en .env")

# Forzar el uso del driver psycopg3 para sqlalchemy sincrónico en PGVector
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+psycopg://", 1)

from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

# Configuramos FastEmbed para ejecutar el modelo de embeddings localmente (Optimizado para bajo consumo de RAM - ideal para 512MB)
embeddings = FastEmbedEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

collection_name = "seniorvital_memory"

# Inicializamos la conexión con Supabase a través de PGVector
vectorstore = PGVector(
    collection_name=collection_name,
    connection_string=db_url,
    embedding_function=embeddings,
)

async def ingestar_memoria_paciente(paciente_id: str, texto: str, metadata: dict = None) -> bool:
    """Genera embeddings para el texto y lo almacena asociado al paciente_id."""
    if metadata is None:
        metadata = {}
    metadata["paciente_id"] = paciente_id
    
    try:
        # Añadimos el documento sincrónicamente (PGVector en community es sincrónico)
        vectorstore.add_texts(texts=[texto], metadatas=[metadata])
        print(f"[VectorStore] Ingestada memoria para {paciente_id}: {texto}")
        return True
    except Exception as e:
        print(f"[VectorStore] Error ingestando memoria: {e}")
        return False

async def buscar_memorias_paciente(paciente_id: str, query: str, limit: int = 3) -> list:
    """Recupera contexto relevante filtrado estrictamente por paciente_id."""
    try:
        # Hacemos la búsqueda limitando a los documentos que pertenezcan a este paciente_id
        # LangChain PGVector usa filter={"paciente_id": paciente_id}
        docs = vectorstore.similarity_search(
            query=query, 
            k=limit, 
            filter={"paciente_id": paciente_id}
        )
        print(f"[VectorStore] Encontradas {len(docs)} memorias para {paciente_id}")
        return [doc.page_content for doc in docs]
    except Exception as e:
        print(f"[VectorStore] Error buscando memorias: {e}")
        return []
