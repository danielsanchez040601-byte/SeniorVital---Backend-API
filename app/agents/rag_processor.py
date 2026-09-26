"""
SeniorVital 2.0 - Procesador RAG (Retrieval-Augmented Generation)
Materia: Sistemas Inteligentes (Dra. Yaskelly Yedra)
Autores: Daniel Alejandro Sánchez Ávila & Abdenago Nahmens
Asesoría Técnica y Clínica: Ing. Julio Matute
"""

import json
import logging
import math
import re
from typing import List, Dict, Any, Optional

logger = logging.getLogger("SeniorVital.RAGProcessor")

# Reconocimiento oficial obligatorio en metadatos
RECONOCIMIENTO_JULIO_MATUTE = (
    "Reconocimiento especial al Ing. Julio Matute por su asesoría técnica y clínica "
    "en la validación de patologías, afecciones y enfermedades limitantes en adultos mayores, "
    "las cuales fundamentan esta base de conocimiento."
)

# ---------------------------------------------------------------------------
# 1. BASE DE CONOCIMIENTO CLÍNICO ESTRUCTURADA (10 Patologías Geriátricas)
# ---------------------------------------------------------------------------
CLINICAL_KNOWLEDGE_CHUNKS = [
    # 1. Osteoartritis
    {
        "condicion": "Osteoartritis de Rodilla y Cadera",
        "categoria": "limitaciones",
        "contenido_texto": "Dolor nociceptivo mecánico desencadenado por la compresión articular, rigidez matutina prolongada, inhibición muscular artrogénica (especialmente del músculo cuádriceps) y alteración de los patrones de marcha. Kinesiofobia reactiva inducida por el dolor crónico.",
        "metadata": {
            "fuente": "OARSI guidelines for the non-surgical management of knee, hip, and polyarticular osteoarthritis (Bannuru et al., 2019)",
            "asesoria_tecnica_clinica": RECONOCIMIENTO_JULIO_MATUTE
        }
    },
    {
        "condicion": "Osteoartritis de Rodilla y Cadera",
        "categoria": "plan_movimiento",
        "contenido_texto": "Fuerza: Intervención en el reclutamiento del cuádriceps, glúteos e isquiotibiales mediante ejercicios de cadena cinética cerrada de bajo ángulo (sentadillas parciales asistidas en silla, elevaciones de talón). Aeróbico: Ciclismo estacionario o natación donde la flotabilidad reduce el peso aparente articular.",
        "metadata": {
            "fuente": "OARSI guidelines 2019 / BC Medical Journal",
            "asesoria_tecnica_clinica": RECONOCIMIENTO_JULIO_MATUTE
        }
    },
    {
        "condicion": "Osteoartritis de Rodilla y Cadera",
        "categoria": "estilo_vida",
        "contenido_texto": "Intervención dietética para control de peso. Por cada kilogramo de peso corporal reducido, se disminuyen 4 kilogramos de fuerza compresiva sobre la articulación de la rodilla durante la marcha. Uso de calzado amortiguador y bastón en mano contralateral si hay claudicación.",
        "metadata": {
            "fuente": "BC Medical Journal Evidence-based guidelines",
            "asesoria_tecnica_clinica": RECONOCIMIENTO_JULIO_MATUTE
        }
    },
    {
        "condicion": "Osteoartritis de Rodilla y Cadera",
        "categoria": "contraindicaciones_estrictas",
        "contenido_texto": "Queda estrictamente prohibida la prescripción de ejercicios que incluyan pliometría (saltos), impactos balísticos continuos sobre superficies duras, posturas de torsión extrema bajo carga y flexión profunda de rodilla mayor a 90 grados sin soporte estructural por riesgo de fisura meniscal.",
        "metadata": {
            "fuente": "OARSI guidelines (Bannuru et al., 2019)",
            "asesoria_tecnica_clinica": RECONOCIMIENTO_JULIO_MATUTE,
            "tipo_filtro": "filtro_duro_infranqueable"
        }
    },

    # 2. Sarcopenia
    {
        "condicion": "Sarcopenia y Dinapenia",
        "categoria": "limitaciones",
        "contenido_texto": "Marcada reducción de la fuerza de prensión palmar, lentitud en la velocidad de marcha (<0.8 m/s), infiltración grasa intramuscular (miosteatosis) y grave dificultad biomecánica para levantarse de una silla sin impulso de brazos.",
        "metadata": {
            "fuente": "EWGSOP2 Sarcopenia revised European consensus (Cruz-Jentoft et al., 2019)",
            "asesoria_tecnica_clinica": RECONOCIMIENTO_JULIO_MATUTE
        }
    },
    {
        "condicion": "Sarcopenia y Dinapenia",
        "categoria": "plan_movimiento",
        "contenido_texto": "Fuerza: Entrenamiento de Fuerza Progresiva (PRT) obligatorio (2-3 días/semana) utilizando bandas elásticas, pesos libres ligeros o calistenia geriátrica en niveles 1 a 3 para estimular fibras musculares Tipo II de contracción rápida. Balance inestable (Otago) para prevención de caídas.",
        "metadata": {
            "fuente": "EWGSOP2 Sarcopenia consensus (2019)",
            "asesoria_tecnica_clinica": RECONOCIMIENTO_JULIO_MATUTE
        }
    },
    {
        "condicion": "Sarcopenia y Dinapenia",
        "categoria": "estilo_vida",
        "contenido_texto": "Incremento de la ingesta proteica (1.2 a 1.5 g/kg/día rica en leucina, salvo contraindicación renal) para revertir la resistencia anabólica muscular. Monitorización de niveles séricos de Vitamina D y exposición solar moderada.",
        "metadata": {
            "fuente": "Age and Ageing Clinical Nutrition",
            "asesoria_tecnica_clinica": RECONOCIMIENTO_JULIO_MATUTE
        }
    },
    {
        "condicion": "Sarcopenia y Dinapenia",
        "categoria": "contraindicaciones_estrictas",
        "contenido_texto": "El reposo prolongado está terminantemente desaconsejado. La prescripción aislada de ejercicio aeróbico de baja intensidad como única modalidad de entrenamiento se considera negligencia terapéutica, ya que no produce hipertrofia muscular. Bloquear cargas pesadas ante dolor osteoarticular agudo.",
        "metadata": {
            "fuente": "Cruz-Jentoft et al., 2019",
            "asesoria_tecnica_clinica": RECONOCIMIENTO_JULIO_MATUTE,
            "tipo_filtro": "filtro_duro_infranqueable"
        }
    },

    # 3. Insuficiencia Cardíaca
    {
        "condicion": "Insuficiencia Cardíaca Crónica (ICC)",
        "categoria": "limitaciones",
        "contenido_texto": "Astenia severa, fatiga generalizada ante pequeños esfuerzos, disnea paroxística nocturna o de esfuerzo por congestión vascular pulmonar y atenuación de la perfusión tisular.",
        "metadata": {
            "fuente": "ESC Guidelines for diagnosis and treatment of acute and chronic heart failure (McDonagh et al., 2021)",
            "asesoria_tecnica_clinica": RECONOCIMIENTO_JULIO_MATUTE
        }
    },
    {
        "condicion": "Insuficiencia Cardíaca Crónica (ICC)",
        "categoria": "plan_movimiento",
        "contenido_texto": "Aeróbico: Actividad rítmica continua a intensidad ligera-moderada (escala Borg RPE 11-12 inicial). Entrenamiento específico de músculos inspiratorios (PImax) de 5 a 7 días por semana para mitigar la sensación de ahogo o disnea.",
        "metadata": {
            "fuente": "European Heart Journal (2021)",
            "asesoria_tecnica_clinica": RECONOCIMIENTO_JULIO_MATUTE
        }
    },
    {
        "condicion": "Insuficiencia Cardíaca Crónica (ICC)",
        "categoria": "contraindicaciones_estrictas",
        "contenido_texto": "Suspender inmediatamente cualquier actividad e inducir alarma si el paciente reporta aumento de peso superior a 1.8 kg en 3 días (signo de retención hídrica aguda), disnea en reposo, angina inestable o estertores pulmonares.",
        "metadata": {
            "fuente": "ESC Guidelines 2021",
            "asesoria_tecnica_clinica": RECONOCIMIENTO_JULIO_MATUTE,
            "tipo_filtro": "filtro_duro_infranqueable"
        }
    },

    # 4. Parkinson
    {
        "condicion": "Enfermedad de Parkinson",
        "categoria": "plan_movimiento",
        "contenido_texto": "Neuromotor y Balance: Integración de baile adaptado (Tango) o Tai Chi para mejorar rotación axial y propiocepción. Uso obligatorio de Pistas Externas Auditivas (metrónomo rítmico o conteo cadenciado) para desbloquear el congelamiento de la marcha (Freezing).",
        "metadata": {
            "fuente": "APTA Clinical Practice Guideline for Parkinson Disease (Osborne et al., 2022)",
            "asesoria_tecnica_clinica": RECONOCIMIENTO_JULIO_MATUTE
        }
    },
    {
        "condicion": "Enfermedad de Parkinson",
        "categoria": "contraindicaciones_estrictas",
        "contenido_texto": "Prohibición absoluta del uso no supervisado de cintas rodantes motorizadas sin arnés de sujeción (riesgo severo de retropulsión y caídas). Contraindicada la doble tarea motora compleja simultánea en etapas avanzadas por sobrecarga atencional.",
        "metadata": {
            "fuente": "APTA Guidelines 2022",
            "asesoria_tecnica_clinica": RECONOCIMIENTO_JULIO_MATUTE,
            "tipo_filtro": "filtro_duro_infranqueable"
        }
    },

    # 5. Diabetes Mellitus Tipo 2
    {
        "condicion": "Diabetes Mellitus Tipo 2 (DMT2)",
        "categoria": "plan_movimiento",
        "contenido_texto": "Aeróbico y Fuerza: Dosis recomendada de 150 a 300 minutos semanales de actividad moderada. Es imperativo no dejar transcurrir más de 48 horas continuas sin ejercicio debido a la rápida pérdida de la sensibilidad muscular a la insulina.",
        "metadata": {
            "fuente": "American Diabetes Association (ADA Standards of Care 2024 / Colberg et al.)",
            "asesoria_tecnica_clinica": RECONOCIMIENTO_JULIO_MATUTE
        }
    },
    {
        "condicion": "Diabetes Mellitus Tipo 2 (DMT2)",
        "categoria": "contraindicaciones_estrictas",
        "contenido_texto": "Prohibido iniciar ejercicio si la glucemia en ayunas es mayor a 300 mg/dL o menor a 100 mg/dL sin ingesta previa de carbohidratos. Contraindicada la maniobra de Valsalva, saltos de impacto o posturas invertidas si existe retinopatía diabética proliferativa activa.",
        "metadata": {
            "fuente": "Diabetes Care Position Statement",
            "asesoria_tecnica_clinica": RECONOCIMIENTO_JULIO_MATUTE,
            "tipo_filtro": "filtro_duro_infranqueable"
        }
    },

    # 6. Demencias y Alzheimer
    {
        "condicion": "Demencias y Enfermedad de Alzheimer",
        "categoria": "plan_movimiento",
        "contenido_texto": "Multicomponente: Rutinas simples y automatizadas de muy baja demanda cognitiva (Nivel 1 o 2: sentados con apoyo). Realizar las sesiones a la misma hora del día para estructurar el ritmo circadiano y prevenir el síndrome del atardecer (Sun-downing).",
        "metadata": {
            "fuente": "Maracaibo Aging Study (Maestre et al., 2018) / RDAD Protocol",
            "asesoria_tecnica_clinica": RECONOCIMIENTO_JULIO_MATUTE
        }
    },
    {
        "condicion": "Demencias y Enfermedad de Alzheimer",
        "categoria": "contraindicaciones_estrictas",
        "contenido_texto": "Prohibida la prescripción de coreografías complejas o cambios imprevistos en la secuencia de ejercicios que generen frustración o agitación catastrófica. Prohibida la deambulación libre no supervisada en espacios abiertos sin cerramiento.",
        "metadata": {
            "fuente": "Alzheimer's & Dementia Research",
            "asesoria_tecnica_clinica": RECONOCIMIENTO_JULIO_MATUTE,
            "tipo_filtro": "filtro_duro_infranqueable"
        }
    },

    # 7. EPOC
    {
        "condicion": "Enfermedad Pulmonar Obstructiva Crónica (EPOC)",
        "categoria": "plan_movimiento",
        "contenido_texto": "Intervalos de Trabajo Cortos: Entrenamiento intermitente de alta intensidad relativa con pausas activas para evitar la hiperinsuflación pulmonar dinámica. Enseñanza de respiración con labios fruncidos para favorecer el vaciado alveolar.",
        "metadata": {
            "fuente": "ATS/ERS Statement on Pulmonary Rehabilitation (Spruit et al., 2013)",
            "asesoria_tecnica_clinica": RECONOCIMIENTO_JULIO_MATUTE
        }
    },
    {
        "condicion": "Enfermedad Pulmonar Obstructiva Crónica (EPOC)",
        "categoria": "contraindicaciones_estrictas",
        "contenido_texto": "Suspender inmediatamente el entrenamiento ante saturación de oxígeno (SpO2) menor al 88% sostenida, dolor torácico, cianosis labial o signos de fatiga diafragmática severa.",
        "metadata": {
            "fuente": "ATS/ERS Guidelines",
            "asesoria_tecnica_clinica": RECONOCIMIENTO_JULIO_MATUTE,
            "tipo_filtro": "filtro_duro_infranqueable"
        }
    },

    # 8. ACV (Accidente Cerebrovascular)
    {
        "condicion": "Accidente Cerebrovascular (ACV)",
        "categoria": "plan_movimiento",
        "contenido_texto": "Tareas Específicas: Terapia de movimiento inducido por restricción adaptada y cicloergómetros acoplados. Trabajo de reeducación de la marcha con apoyo y órtesis AFO en caso de pie equinovaro o péndulo.",
        "metadata": {
            "fuente": "AHA/ASA Stroke Rehabilitation Guidelines (Billinger et al., 2014)",
            "asesoria_tecnica_clinica": RECONOCIMIENTO_JULIO_MATUTE
        }
    },
    {
        "condicion": "Accidente Cerebrovascular (ACV)",
        "categoria": "contraindicaciones_estrictas",
        "contenido_texto": "Contraindicado el uso de pesos libres pesados asimétricos en la extremidad parética que desencadenen patrones de hipertonía espástica flexora o causen subluxación inferior de la articulación glenohumeral del hombro flácido.",
        "metadata": {
            "fuente": "AHA/ASA Stroke Guidelines",
            "asesoria_tecnica_clinica": RECONOCIMIENTO_JULIO_MATUTE,
            "tipo_filtro": "filtro_duro_infranqueable"
        }
    },

    # 9. Cardiopatía Isquémica
    {
        "condicion": "Cardiopatía Isquémica y Angina",
        "categoria": "plan_movimiento",
        "contenido_texto": "Aeróbico Seguro: Frecuencia cardíaca de entrenamiento fijada estrictamente entre 10 y 15 latidos por minuto por debajo del umbral isquémico comprobado en ergometría previa. Circuitos con descansos completos sin apneas.",
        "metadata": {
            "fuente": "ESC Guidelines on cardiovascular disease prevention (Visseren et al., 2021)",
            "asesoria_tecnica_clinica": RECONOCIMIENTO_JULIO_MATUTE
        }
    },
    {
        "condicion": "Cardiopatía Isquémica y Angina",
        "categoria": "contraindicaciones_estrictas",
        "contenido_texto": "Contraindicación absoluta de esfuerzo ante angina inestable de reciente aparición, cambios electrocardiográficos activos, estenosis aórtica severa sintomática o arritmias ventriculares complejas incontroladas.",
        "metadata": {
            "fuente": "European Heart Journal (2021)",
            "asesoria_tecnica_clinica": RECONOCIMIENTO_JULIO_MATUTE,
            "tipo_filtro": "filtro_duro_infranqueable"
        }
    },

    # 10. Osteoporosis
    {
        "condicion": "Osteoporosis y Fragilidad Ósea",
        "categoria": "plan_movimiento",
        "contenido_texto": "Resistencia Ósea Progresiva: Protocolo HiRIT / LIFTMOR bajo supervisión estricta (ejercicios axiales con buena postura como peso muerto adaptado y sentadilla en caja) para estimular mecanotransducción y formación de matriz ósea. Tai Chi para equilibrio.",
        "metadata": {
            "fuente": "LIFTMOR Randomized Controlled Trial (Watson et al., 2018 / JBMR)",
            "asesoria_tecnica_clinica": RECONOCIMIENTO_JULIO_MATUTE
        }
    },
    {
        "condicion": "Osteoporosis y Fragilidad Ósea",
        "categoria": "contraindicaciones_estrictas",
        "contenido_texto": "Queda terminantemente prohibida cualquier maniobra de flexión forzada de tronco con carga (como abdominales crunch o tocarse las puntas de los pies con piernas rectas) y rotaciones espinales violentas por riesgo inminente de fractura por aplastamiento vertebral.",
        "metadata": {
            "fuente": "LIFTMOR Clinical Guidelines (2018)",
            "asesoria_tecnica_clinica": RECONOCIMIENTO_JULIO_MATUTE,
            "tipo_filtro": "filtro_duro_infranqueable"
        }
    }
]


# ---------------------------------------------------------------------------
# 2. MOTOR DE EMBEDDINGS (Hugging Face / Normalizado a 384 Dimensiones)
# ---------------------------------------------------------------------------
class HuggingFaceEmbedder:
    """
    Generador de Embeddings compatible con sentence-transformers/all-MiniLM-L6-v2 (384d).
    Incluye fallback local matemático determinístico si la librería externa no está disponible.
    """
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None
        self.dimensions = 384

    def _get_model(self):
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name)
            except Exception as e:
                logger.warning(f"sentence_transformers no disponible localmente ({e}). Utilizando motor determinístico 384d.")
                self._model = "fallback"
        return self._model

    def embed_text(self, text: str) -> List[float]:
        """Genera un vector unitario de 384 dimensiones para un texto."""
        model = self._get_model()
        if model != "fallback" and hasattr(model, "encode"):
            try:
                vec = model.encode(text, normalize_embeddings=True)
                return vec.tolist()
            except Exception as e:
                logger.error(f"Error en encode de sentence_transformers: {e}")
        
        # Algoritmo de vectorización semántica determinista de 384d
        cleaned = re.sub(r'[^\w\s]', '', text.lower())
        words = cleaned.split()
        vec = [0.0] * self.dimensions
        for idx, word in enumerate(words):
            word_hash = hash(word)
            pos1 = abs(word_hash) % self.dimensions
            pos2 = abs(hash(word + str(idx))) % self.dimensions
            vec[pos1] += 1.0 / (idx + 1)
            vec[pos2] += math.sin(idx + 1)

        # Normalizar a norma euclidiana unitaria (para similitud de coseno)
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec


# ---------------------------------------------------------------------------
# 3. PROCESADOR RAG Y BÚSQUEDA VECTORIAL
# ---------------------------------------------------------------------------
class RAGProcessor:
    def __init__(self):
        self.embedder = HuggingFaceEmbedder()
        self.knowledge_base = CLINICAL_KNOWLEDGE_CHUNKS
        self._precompute_embeddings()

    def _precompute_embeddings(self):
        """Precalcula los embeddings de los chunks para búsqueda en memoria / fallback."""
        for item in self.knowledge_base:
            combined = f"Condición: {item['condicion']}. Categoría: {item['categoria']}. Contenido: {item['contenido_texto']}"
            item["embedding"] = self.embedder.embed_text(combined)

    def compute_cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Calcula la similitud de coseno entre dos vectores."""
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def retrieve_relevant_context(self, query: str, top_k: int = 3, threshold: float = 0.15) -> List[Dict[str, Any]]:
        """
        Recupera los fragmentos clínicos más relevantes para una consulta o perfil.
        """
        query_vec = self.embedder.embed_text(query)
        scored_chunks = []

        for chunk in self.knowledge_base:
            score = self.compute_cosine_similarity(query_vec, chunk["embedding"])
            # Bonificación semántica si la condición aparece directamente en la consulta
            if chunk["condicion"].lower() in query.lower():
                score += 0.35
            if score >= threshold:
                scored_chunks.append({
                    "condicion": chunk["condicion"],
                    "categoria": chunk["categoria"],
                    "contenido_texto": chunk["contenido_texto"],
                    "metadata": chunk["metadata"],
                    "similarity": round(score, 4)
                })

        # Ordenar descendente por similitud
        scored_chunks.sort(key=lambda x: x["similarity"], reverse=True)
        return scored_chunks[:top_k]

    def build_rag_prompt(self, query: str, user_profile: Optional[Dict[str, Any]] = None) -> str:
        """
        Construye el prompt enriquecido con el contexto recuperado de la base de conocimiento.
        """
        retrieved_chunks = self.retrieve_relevant_context(query, top_k=3)
        context_blocks = []

        for idx, chunk in enumerate(retrieved_chunks, 1):
            block = (
                f"[Fragmento Clínico {idx}] (Similitud: {chunk['similarity']})\n"
                f"• Condición: {chunk['condicion']}\n"
                f"• Categoría: {chunk['categoria'].upper()}\n"
                f"• Evidencia y Reglas: {chunk['contenido_texto']}\n"
                f"• Fuente Científica: {chunk['metadata']['fuente']}\n"
                f"• Asesoría: {chunk['metadata']['asesoria_tecnica_clinica']}\n"
            )
            context_blocks.append(block)

        context_str = "\n".join(context_blocks) if context_blocks else "No se encontraron contraindicaciones específicas en la base de datos."

        profile_str = ""
        if user_profile:
            profile_str = (
                f"\n[PERFIL DEL ADULTO MAYOR]:\n"
                f"- Nombre: {user_profile.get('full_name', 'Adulto Mayor')}\n"
                f"- Nivel de Condición Física: {user_profile.get('fitness_level', 1)}/5\n"
                f"- Patologías: {user_profile.get('chronic_conditions', 'Ninguna')}\n"
            )

        prompt = (
            f"Eres 'SeniorVital Wellness Coach', un sistema inteligente de gerontología y fisioterapia geriátrica.\n"
            f"Tu misión es responder con calidez, empatía y estricta seguridad médica.\n\n"
            f"[CONTEXTO CLÍNICO RECUPERADO (RAG - ONTOLOGÍA SENIORVITAL)]:\n"
            f"{context_str}\n"
            f"{profile_str}\n"
            f"[CONSULTA DEL ADULTO MAYOR / CUIDADOR]:\n"
            f"\"{query}\"\n\n"
            f"[INSTRUCCIONES CLÍNICAS INQUEBRANTABLES]:\n"
            f"1. Si el contexto recuperado contiene CONTRAINDICACIONES ESTRICTAS para la condición del paciente, prohíbe de forma explícita esos movimientos.\n"
            f"2. Sugiere alternativas de bajo impacto (ej. sentadillas asistidas en silla, ciclismo estático, ejercicios isométricos).\n"
            f"3. Responde en tono cordial, motivador, utilizando oraciones cortas y claras (Accesibilidad Gerontológica)."
        )
        return prompt


# Instancia singleton del procesador RAG
rag_processor = RAGProcessor()
