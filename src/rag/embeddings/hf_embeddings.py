"""
Generador de Embeddings Semánticos para SeniorVital.
Modelo: sentence-transformers/all-MiniLM-L6-v2 (384 dimensiones).
Soporta inferencia directa vía Hugging Face Inference API / Local con Telemetría en Tiempo de Ejecución (Post-Execution Telemetry).
"""
from typing import List, Tuple, Dict, Any, Optional
import os
import re
import math
import logging
import httpx
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Vocabulario de conceptos clínicos clave mapeados a bandas de dimensión semántica (384d)
CLINICAL_CONCEPT_BANDS = {
    # 1. Osteoartritis
    "oa": (0, 35),
    "osteoartritis": (0, 35),
    "rodilla": (0, 35),
    "cadera": (0, 35),
    "articular": (0, 35),
    # 2. Sarcopenia
    "sar": (35, 70),
    "sarcopenia": (35, 70),
    "dinapenia": (35, 70),
    "muscular": (35, 70),
    "fuerza": (35, 70),
    "calistenia": (35, 70),
    # 3. Osteoporosis
    "ost": (70, 105),
    "osteoporosis": (70, 105),
    "osea": (70, 105),
    "oseo": (70, 105),
    "fractura": (70, 105),
    "fracturas": (70, 105),
    "liftmor": (70, 105),
    "hirit": (70, 105),
    # 4. Insuficiencia Cardíaca
    "icc": (105, 140),
    "insuficiencia": (105, 140),
    "cardiaca": (105, 140),
    "cardiovascular": (105, 140),
    "descompensacion": (105, 140),
    # 5. Diabetes Mellitus Tipo 2
    "dmt2": (140, 175),
    "diabetes": (140, 175),
    "glucemia": (140, 175),
    "insulina": (140, 175),
    "hipoglucemia": (140, 175),
    # 6. EPOC
    "epoc": (175, 210),
    "pulmonar": (175, 210),
    "respiratoria": (175, 210),
    "respiratorio": (175, 210),
    "labios": (175, 210),
    "fruncidos": (175, 210),
    "bronquial": (175, 210),
    # 7. Parkinson
    "park": (210, 245),
    "parkinson": (210, 245),
    "marcha": (210, 245),
    "temblor": (210, 245),
    "bradicinesia": (210, 245),
    # 8. ACV / Ictus
    "acv": (245, 280),
    "cerebrovascular": (245, 280),
    "ictus": (245, 280),
    "hemiparesia": (245, 280),
    "paretico": (245, 280),
    # 9. Lumbalgia
    "lumb": (280, 315),
    "lumbalgia": (280, 315),
    "espondiloartrosis": (280, 315),
    "columna": (280, 315),
    "lumbar": (280, 315),
    # 10. Fragilidad
    "frag": (315, 350),
    "fragilidad": (315, 350),
    "vivifrail": (315, 350),
    "vulnerabilidad": (315, 350),
    "caidas": (315, 350),
    # Categorías / Intención
    "contraindicaciones": (350, 365),
    "prohibido": (350, 365),
    "prohibidos": (350, 365),
    "evitar": (350, 365),
    "riesgo": (350, 365),
    "recomendado": (365, 384),
    "recomendados": (365, 384),
    "ejercicios": (365, 384),
    "prescripcion": (365, 384),
    "plan": (365, 384)
}


class HuggingFaceEmbeddingsGenerator:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", api_token: str = None):
        self.model_name = model_name
        self.api_token = api_token or os.getenv("HF_TOKEN", "")
        self.is_ci = os.getenv("CI", "false").lower() in ("true", "1")
        self.api_url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{self.model_name}"
        self.dimension = 384
        self.last_mode = "NOT_EXECUTED"

    def _normalize(self, vec: List[float]) -> List[float]:
        """Normaliza un vector a norma euclidiana L2 unitaria."""
        norm = math.sqrt(sum(x * x for x in vec))
        if norm == 0:
            return [0.0] * len(vec)
        return [round(x / norm, 6) for x in vec]

    def _deterministic_mock_vector(self, text: str) -> List[float]:
        """Genera un vector denso semántico proyectado en 384 dimensiones."""
        words = re.findall(r'[a-zA-Z0-9_]+', text.lower())
        vec = [0.005 * math.sin((i + 1) * 0.7) for i in range(self.dimension)]

        for word in words:
            for concept, (start, end) in CLINICAL_CONCEPT_BANDS.items():
                if concept == word or word.startswith(concept):
                    for i in range(start, min(end, self.dimension)):
                        vec[i] += 3.5 * math.cos((i - start + 1) * 0.25)

        return self._normalize(vec)

    def embed_query_with_telemetry(self, text: str) -> Tuple[List[float], str]:
        """Genera embedding y retorna (vector, modo_post_ejecucion)."""
        vectors, mode = self.embed_documents_with_telemetry([text])
        vec = vectors[0] if vectors else [0.0] * self.dimension
        self.last_mode = mode
        return vec, mode

    def embed_documents_with_telemetry(self, texts: List[str]) -> Tuple[List[List[float]], str]:
        """
        Genera embeddings para un lote con evaluación post-ejecución:
        - Intento real contra Hugging Face API / modelo.
        - Fallback determinista capturando excepción o ausencia de credenciales.
        """
        token = self.api_token or os.getenv("HF_TOKEN", "")
        if self.is_ci or not token or "your_" in token.lower():
            vectors = [self._deterministic_mock_vector(t) for t in texts]
            mode = "FALLBACK_CI"
            self.last_mode = mode
            return vectors, mode

        headers = {"Authorization": f"Bearer {token}"}
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.post(
                    self.api_url, 
                    headers=headers, 
                    json={"inputs": texts, "options": {"wait_for_model": True}}
                )
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0:
                        if isinstance(data[0], list):
                            vectors = [self._normalize(v) for v in data]
                            mode = "HUGGINGFACE_REAL_MODEL"
                            self.last_mode = mode
                            return vectors, mode
                        elif isinstance(data[0], (int, float)):
                            vectors = [self._normalize(data)]
                            mode = "HUGGINGFACE_REAL_MODEL"
                            self.last_mode = mode
                            return vectors, mode
                # Si el status code fue distinto de 200
                logger.warning(f"Respuesta inesperada de Hugging Face API: status={response.status_code}")
                vectors = [self._deterministic_mock_vector(t) for t in texts]
                mode = "FALLBACK_API_ERROR"
                self.last_mode = mode
                return vectors, mode
        except Exception as e:
            logger.warning(f"Fallo en inferencia HF: {e}")
            vectors = [self._deterministic_mock_vector(t) for t in texts]
            mode = "FALLBACK_API_ERROR" if token else "FALLBACK_CI"
            self.last_mode = mode
            return vectors, mode

    def embed_query(self, text: str) -> List[float]:
        """Genera embedding para una consulta de búsqueda."""
        vec, mode = self.embed_query_with_telemetry(text)
        return vec

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings para un lote de documentos clínicos."""
        vectors, mode = self.embed_documents_with_telemetry(texts)
        return vectors
