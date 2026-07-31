import os
import sys
from dotenv import load_dotenv

# Cargar variables de entorno (incluye DATABASE_URL, OPENROUTER_API_KEY, etc.)
load_dotenv()

# Añadir el path para importar los módulos app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from langchain_openai import ChatOpenAI
from langchain_community.vectorstores import PGVector
from langchain_core.embeddings import FakeEmbeddings
from app.security import apply_guardrails

def test_database():
    print("--- Probando conexión a Supabase & pgvector ---")
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL no encontrada en .env")
        return False
    
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            # Habilitar extensión
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.commit()
            
            # Verificar
            result = conn.execute(text("SELECT extname FROM pg_extension WHERE extname = 'vector';")).fetchone()
            if result:
                print("[OK] Conexión exitosa a Supabase y extensión pgvector activa.")
                return True
            else:
                print("[FAIL] Conectado, pero extensión pgvector no encontrada.")
                return False
    except Exception as e:
        print(f"[FAIL] Fallo al conectar o ejecutar query en la DB: {e}")
        return False

def test_llm():
    print("\n--- Probando conexión a OpenRouter & LLM ---")
    api_key = os.environ.get("OPENROUTER_API_KEY")
    model = os.environ.get("DEFAULT_LLM_MODEL", "inclusionai/ling-3.0-flash:free")
    
    try:
        llm = ChatOpenAI(
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            model_name=model
        )
        response = llm.invoke("Responde solamente con la palabra 'conectado'")
        if "conectado" in response.content.lower():
            print("[OK] Conexión exitosa al LLM en OpenRouter.")
            return True
        else:
            print(f"? Conexión exitosa, pero el modelo respondió: {response.content}")
            return True
    except Exception as e:
        print(f"[FAIL] Fallo al conectar con OpenRouter: {e}")
        return False

def test_vectorstore():
    print("\n--- Probando integración de Memoria Semántica (VectorStore) ---")
    db_url = os.environ.get("DATABASE_URL")
    try:
        # Usamos FakeEmbeddings dado que sólo queremos probar la inicialización e interacción con Supabase
        embeddings = FakeEmbeddings(size=1536)
        collection_name = "test_memory_phase1"
        vectorstore = PGVector(
            collection_name=collection_name,
            connection_string=db_url,
            embedding_function=embeddings,
        )
        print("[OK] PGVector de LangChain inicializado correctamente con Supabase sin errores.")
        return True
    except Exception as e:
        print(f"[FAIL] Fallo al inicializar PGVector: {e}")
        return False

def test_security():
    print("\n--- Probando Capa de Seguridad Clínica (Guardrails) ---")
    unsafe_response = "Según lo que me dices, tú tienes hipertensión. Te receto que tomes 500mg de un medicamento y vayas a descansar."
    try:
        secured_text = apply_guardrails(unsafe_response)
        
        if "Aviso:" in secured_text or "ALERTA" in secured_text:
            print("[OK] Seguridad Clínica interceptó la respuesta (detectó diagnóstico/receta) y añadió el disclaimer.")
            return True
        else:
            print("[FAIL] Seguridad Clínica no funcionó como se esperaba.")
            return False
    except Exception as e:
        print(f"[FAIL] Fallo al probar Seguridad Clínica: {e}")
        return False

if __name__ == "__main__":
    print("====================================")
    print("VERIFICACIÓN: FASE 1 - SENIOR VITAL")
    print("====================================\n")
    
    db_ok = test_database()
    llm_ok = test_llm()
    vector_ok = test_vectorstore()
    sec_ok = test_security()
    
    print("\n====================================")
    print("RESUMEN DE RESULTADOS")
    print("====================================")
    print(f"DATABASE & PGVECTOR : {'[OK]' if db_ok else '[FAIL]'}")
    print(f"LLM (OpenRouter)    : {'[OK]' if llm_ok else '[FAIL]'}")
    print(f"VECTORSTORE         : {'[OK]' if vector_ok else '[FAIL]'}")
    print(f"SECURITY GUARDRAILS : {'[OK]' if sec_ok else '[FAIL]'}")
    
    if all([db_ok, llm_ok, vector_ok, sec_ok]):
        print("\n---> RESULTADO FINAL: ¡La Fase 1 está 100% LISTA para pasar a la siguiente etapa!")
    else:
        print("\n---> RESULTADO FINAL: Se detectaron fallos. Revisa los logs antes de avanzar.")
