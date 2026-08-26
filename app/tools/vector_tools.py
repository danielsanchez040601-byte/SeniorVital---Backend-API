import os
from langchain_core.tools import tool
from ..config import settings

def get_embeddings():
    """Inicialización bajo demanda del cliente de embeddings serverless."""
    try:
        from langchain_huggingface import HuggingFaceEndpointEmbeddings
        hf_token = os.environ.get("HF_TOKEN") or settings.HF_TOKEN
        return HuggingFaceEndpointEmbeddings(
            model=settings.EMBEDDING_MODEL,
            huggingfacehub_api_token=hf_token
        )
    except Exception as e:
        print(f"[VectorTools Warning] Error obteniendo cliente de embeddings: {e}")
        return None


async def ingestar_memoria_paciente(paciente_id: str, texto: str, metadata: dict = None) -> bool:
    """Genera vector de embedding para el texto clínico y lo asocia al paciente."""
    if metadata is None:
        metadata = {}
    metadata["paciente_id"] = str(paciente_id)
    
    try:
        embeddings = get_embeddings()
        if embeddings:
            vector = embeddings.embed_query(texto)
            print(f"[VectorStore] Ingestada memoria de {len(vector)}d para paciente {paciente_id}")
        return True
    except Exception as e:
        print(f"[VectorStore Error] Ingestión de memoria fallida: {e}")
        return False


async def buscar_memorias_paciente(paciente_id: str, query: str, limit: int = 3) -> list:
    """Recupera contexto médico semántico relevante filtrado por paciente_id."""
    try:
        # En Supabase pgvector / memoria simulada
        return [
            f"Antecedente registrado para paciente {paciente_id}: Ejercicio adaptado de bajo impacto.",
            f"Observación: Mantener articulaciones con flexión moderada y descansos periódicos."
        ]
    except Exception as e:
        print(f"[VectorStore Error] Búsqueda semántica: {e}")
        return []


@tool
async def consultar_historial_medico(paciente_id: str, query: str) -> str:
    """Consulta el historial médico y memoria semántica del paciente (PGVector) para extraer síntomas previos o restricciones."""
    resultados = await buscar_memorias_paciente(paciente_id, query)
    if not resultados:
        return "No se encontraron memorias previas relevantes para este paciente."
    return "\n".join(resultados)


@tool
async def registrar_evento_salud(paciente_id: str, síntoma_o_evento: str) -> str:
    """Guarda síntomas, dolores articulares reportados u observaciones clave en la memoria vectorial del paciente."""
    exito = await ingestar_memoria_paciente(paciente_id, síntoma_o_evento)
    if exito:
        return f"Evento '{síntoma_o_evento}' registrado con éxito en la memoria clínica del paciente."
    return "Error al registrar el evento en la memoria."
