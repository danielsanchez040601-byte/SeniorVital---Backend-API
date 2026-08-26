import os
from langchain_huggingface import HuggingFaceEmbeddings

# Inicialización de embeddings nativos de Hugging Face
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)

# ---------------------------------------------------------
# Configuración de Base de Datos
# ---------------------------------------------------------
DB_CONFIG = {
    "dbname": "seniorvital_db",
    "user": "postgres",
    "password": "your_password",
    "host": "localhost",
    "port": "5432"
}

# ---------------------------------------------------------
# Funciones para Embeddings Semánticos
# ---------------------------------------------------------
def get_embedding(text: str) -> list[float]:
    """Genera vector semántico usando HuggingFace all-MiniLM-L6-v2 (384 dimensiones)."""
    try:
        return embeddings.embed_query(text)
    except Exception as e:
        print(f"Error generando embedding con HuggingFace: {e}")
        return [0.0] * 384

# ---------------------------------------------------------
# Lógica Principal
# ---------------------------------------------------------
def init_db():
    print("Conectando a PostgreSQL...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # 1. Asegurar que la extensión pgvector está instalada
    print("Habilitando extensión vector...")
    cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")

    # 2. Crear tabla principal con dimensión 384 para all-MiniLM-L6-v2
    print("Creando tabla seniorvital_chunks...")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS seniorvital_chunks (
            id SERIAL PRIMARY KEY,
            condicion VARCHAR(255) NOT NULL,
            categoria VARCHAR(100) NOT NULL,
            contenido_texto TEXT NOT NULL,
            metadata JSONB,
            embedding vector(384)
        );
    """)
    conn.commit()
    return conn, cur

def load_and_chunk_data(filepath: str):
    print(f"Cargando datos desde {filepath}...")
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Estrategia de Chunking Lógico:
    # Como la data ya está estructurada jerárquicamente en el JSON (por condición y categoría),
    # y los textos son atómicos y específicos (no exceden los 1000 tokens), 
    # trataremos cada entrada del JSON como un "chunk" lógico semánticamente denso.
    # Si los textos fueran páginas completas, usaríamos RecursiveCharacterTextSplitter aquí.
    
    chunks = []
    for entry in data:
        # Enriquecemos el texto del chunk con el contexto para el embedding
        text_for_embedding = f"Condición: {entry['condicion']}. Categoría: {entry['categoria']}. Contenido: {entry['contenido_texto']}"
        
        chunks.append({
            "condicion": entry["condicion"],
            "categoria": entry["categoria"],
            "contenido_texto": entry["contenido_texto"],
            "metadata": entry["metadata"],
            "text_for_embedding": text_for_embedding
        })
    
    return chunks

def insert_chunks(conn, cur, chunks):
    print(f"Iniciando procesamiento e inserción de {len(chunks)} chunks...")
    
    insert_query = """
        INSERT INTO seniorvital_chunks 
        (condicion, categoria, contenido_texto, metadata, embedding) 
        VALUES (%s, %s, %s, %s, %s);
    """
    
    for i, chunk in enumerate(chunks):
        # Generar embedding
        emb = get_embedding(chunk["text_for_embedding"])
        
        # Insertar en DB
        cur.execute(insert_query, (
            chunk["condicion"],
            chunk["categoria"],
            chunk["contenido_texto"],
            Json(chunk["metadata"]), # Insertar como JSONB
            emb
        ))
        
        if (i + 1) % 10 == 0:
            print(f"Insertados {i + 1} chunks...")
            
    conn.commit()
    print("Carga de base de datos RAG completada exitosamente.")

if __name__ == "__main__":
    try:
        connection, cursor = init_db()
        chunks_data = load_and_chunk_data("rag_knowledge_base.json")
        insert_chunks(connection, cursor, chunks_data)
    except Exception as e:
        print(f"Error durante el proceso: {e}")
    finally:
        if 'cursor' in locals() and cursor:
            cursor.close()
        if 'connection' in locals() and connection:
            connection.close()
            print("Conexión cerrada.")
