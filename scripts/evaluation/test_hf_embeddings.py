"""
Script de Evaluación y Verificación de Embeddings Semánticos Hugging Face.
Ejecuta la vectorización de 3 fragmentos clínicos reales y comprueba dimensiones, normas L2 y modo post-ejecución.
"""
import os
import sys
import math

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.rag.embeddings.hf_embeddings import HuggingFaceEmbeddingsGenerator


def compute_l2_norm(vec):
    return math.sqrt(sum(x * x for x in vec))


def main():
    print("=" * 80)
    print("SENIORVITAL 2.0 - EVALUACION EMPIRICA DE EMBEDDINGS HUGGING FACE")
    print("=" * 80)

    generator = HuggingFaceEmbeddingsGenerator()
    print(f"[Config] Modelo Configurado: {generator.model_name}")
    print(f"[Config] Dimension Esperada: {generator.dimension}")
    print("-" * 80)

    test_samples = [
        {
            "id": "OA-01_SAMPLE",
            "condicion": "Osteoartritis de Rodilla y Cadera",
            "text": "Queda estrictamente prohibida la prescripcion de ejercicios que incluyan pliometria (saltos), impacto sobre superficies duras y flexion profunda de rodilla mayor a 90 grados por riesgo articular."
        },
        {
            "id": "SAR-02_SAMPLE",
            "condicion": "Sarcopenia y Dinapenia Geriatrica",
            "text": "Prescripcion de entrenamiento de fuerza progresiva (PRT) al 40-80% 1-RM con bandas elasticas y sentadillas asistidas en silla para estimular hipertrofia miofibrilar."
        },
        {
            "id": "ICC-04_SAMPLE",
            "condicion": "Insuficiencia Cardiaca Cronica e Hipertension",
            "text": "Monitoreo cardiovascular estricto con escala Borg 11-12. Prohibido ejercicio si hay ganancia de peso mayor a 1.8 kg en 3 dias o disnea paroxistica en reposo."
        }
    ]

    for idx, sample in enumerate(test_samples, 1):
        print(f"\n[Muestra {idx}/3]: {sample['id']} - {sample['condicion']}")
        print(f"[Texto]: \"{sample['text'][:85]}...\"")
        
        vector, mode = generator.embed_query_with_telemetry(sample['text'])
        dim = len(vector)
        norm = compute_l2_norm(vector)
        first_five = [round(v, 6) for v in vector[:5]]

        print(f"[Modo Post-Ejecucion]: [{mode}]")
        print(f"[Tensor] Dimension: {dim} float32 (Esperado: 384)")
        print(f"[Norma] Euclidiana L2: {norm:.4f} (Vector Unitario Normalizado)")
        print(f"[Floats] Primeros 5 Valores: {first_five}")
        assert dim == 384, f"Error: Dimension invalida {dim}"
        assert abs(norm - 1.0) < 0.01, f"Error: Vector no normalizado (norma={norm})"

    print("\n" + "=" * 80)
    print("[SUCCESS] TODAS LAS PRUEBAS DE REPRESENTACION VECTORIAL (384d) SUPERADAS")
    print("=" * 80)


if __name__ == "__main__":
    main()
