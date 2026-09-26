"""
Script de Demostración y Verificación del Pipeline RAG End-to-End con Telemetría Post-Ejecución.
Ejecuta 3 casos representativos:
1. Caso A: Consulta clínica con contraindicaciones estrictas (Osteoartritis).
2. Caso B: Plan de prescripción de ejercicios seguros (Sarcopenia).
3. Caso C: Consulta fuera de dominio (Filtro preventivo de seguridad).
"""
import os
import sys
import json
import asyncio

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.rag.pipeline.rag_pipeline import ClinicalRAGPipeline


async def main():
    print("=" * 85)
    print("SENIORVITAL 2.0 - DEMOSTRACION Y EVALUACION DEL PIPELINE RAG END-TO-END")
    print("=" * 85)

    pipeline = ClinicalRAGPipeline(similarity_threshold=0.40, top_k=3)

    test_cases = [
        {
            "code": "CASO_A",
            "name": "Consulta con Contraindicación Crítica (Osteoartritis de Rodilla)",
            "query": "Tengo osteoartritis severa en rodilla, puedo hacer sentadillas con salto?",
            "expected": "Advertencia médica y prohibición estricta de saltos/pliometría."
        },
        {
            "code": "CASO_B",
            "name": "Prescripción de Plan de Fuerza Seguro (Sarcopenia Leve)",
            "query": "Que ejercicios de fuerza puedo hacer si presento sarcopenia leve?",
            "expected": "Calistenia adaptada, bandas elásticas y progresión Borg 3-4."
        },
        {
            "code": "CASO_C",
            "name": "Consulta Fuera del Dominio Clínico Gerontológico",
            "query": "Como programo un microcontrolador ESP32 en lenguaje C++?",
            "expected": "Activación del guardrail de seguridad por ausencia de contexto clínico."
        }
    ]

    for idx, tc in enumerate(test_cases, 1):
        print(f"\n" + "#" * 85)
        print(f"[TEST {idx}/3: {tc['code']}] {tc['name']}")
        print(f"[Consulta]: \"{tc['query']}\"")
        print(f"[Esperado]: {tc['expected']}")
        print("-" * 85)

        res = await pipeline.run_pipeline(tc["query"])

        print(f"[Estado]: {res['status']}")
        print(f"[Proveedor]: {res['provider']}")
        print(f"[Telemetria Post-Ejecucion]: {json.dumps(res.get('telemetry', {}), indent=2)}")
        
        chunks = res.get("retrieved_chunks", [])
        print(f"[Chunks Recuperados ({len(chunks)})]:")
        for c in chunks:
            sim = c.get("similarity", 0.0)
            print(f"   * Chunk ID: {c.get('chunk_id')} | Condicion: {c.get('condition_id')} | Similitud: {sim:.4f} | Tipo: {c.get('category')}")

        if res.get("context_injected"):
            print(f"\n[Contexto Inyectado (Muestra)]:\n{res['context_injected'][:200]}...")

        resp_clean = res['response'].encode('ascii', 'ignore').decode('ascii')
        print(f"\n[Respuesta Generada]:\n{resp_clean}")
        print("#" * 85)

    print("\n" + "=" * 85)
    print("[SUCCESS] DEMOSTRACION DE FLUJO RAG E2E COMPLETADA CON EXITO")
    print("=" * 85)


if __name__ == "__main__":
    asyncio.run(main())
