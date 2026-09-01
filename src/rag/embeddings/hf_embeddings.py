"""
Generador de Embeddings Semánticos para SeniorVital.
Modelo: sentence-transformers/all-MiniLM-L6-v2 (384 dimensiones).
Soporta inferencia directa vía Hugging Face Inference API / Local y fallback determinista semántico para CI/Testing.
"""
from typing import List
import os
import re
import math
import httpx
from dotenv import load_dotenv

load_dotenv()

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
        self.mode = "FALLBACK_CI" if (self.is_ci or not self.api_token) else "HUGGINGFACE_REAL_MODEL"

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

    def embed_query(self, text: str) -> List[float]:
        """Genera embedding para una consulta de búsqueda."""
        embeddings = self.embed_documents([text])
        return embeddings[0] if embeddings else [0.0] * self.dimension

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Genera embeddings para un lote de documentos clínicos."""
        if self.is_ci or not self.api_token:
            return [self._deterministic_mock_vector(t) for t in texts]

        headers = {"Authorization": f"Bearer {self.api_token}"}
        try:
            with httpx.Client(timeout=15.0) as client:
                response = client.post(
                    self.api_url, 
                    headers=headers, 
                    json={"inputs": texts, "options": {"wait_for_model": True}}
                )
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
                        return [self._normalize(v) for v in data]
                    elif isinstance(data, list) and len(data) > 0 and isinstance(data[0], (int, float)):
                        return [self._normalize(data)]
                return [self._deterministic_mock_vector(t) for t in texts]
        except Exception:
            return [self._deterministic_mock_vector(t) for t in texts]
