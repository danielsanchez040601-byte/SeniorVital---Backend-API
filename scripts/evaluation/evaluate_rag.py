"""
Script de Evaluación Automatizada y Cálculo Empírico de Métricas RAG con Telemetría.
Evalúa:
- Bloque A: Métricas de Recuperación (Hit Rate@3, MRR, Precision@3, Latencia).
- Bloque B: Análisis de Generación (Adherencia Clínica y Proveedor LLM en Tiempo Real).
Exporta resultados estructurados a data/evaluation/retrieval_benchmark_results.json.
"""
import os
import sys
import json
import time
import asyncio
from typing import List, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.rag.retriever.retriever import ClinicalRetriever
from src.rag.pipeline.rag_pipeline import ClinicalRAGPipeline


async def main():
    print("=" * 85)
    print("SENIORVITAL 2.0 - EVALUACION Y BENCHMARKING RAG CON TELEMETRIA")
    print("=" * 85)

    dataset_path = os.path.join("data", "evaluation", "rag_eval_dataset.json")
    if not os.path.exists(dataset_path):
        print(f"[ERROR] Dataset no encontrado en {dataset_path}")
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        queries = json.load(f)

    pipeline = ClinicalRAGPipeline(similarity_threshold=0.40, top_k=3)
    retriever = pipeline.retriever

    # Warmup
    await retriever.retrieve_with_telemetry(query="warmup", top_k=1)

    k = 3
    hits = 0
    reciprocal_ranks = []
    precision_scores = []
    latencies = []
    retrieval_details = []
    generation_details = []
    adherent_count = 0

    embedding_modes = set()
    vector_backends = set()
    llm_providers = set()

    print(f"[Dataset]: {len(queries)} consultas clinicas anotadas para benchmarking (Top-K = {k}).\n")
    print(f"{'ID':<5} | {'Condicion':<10} | {'Hit@3':<7} | {'MRR':<6} | {'P@3':<6} | {'Latencia':<10} | {'Top-1 Chunk'}")
    print("-" * 85)

    for item in queries:
        qid = item["id"]
        qtext = item["query"]
        expected = item["expected_chunk_ids"]
        cond = item["condition_id"]

        # Medición de Recuperación (Bloque A)
        start_time = time.perf_counter()
        retrieved, ret_telemetry = await retriever.retrieve_with_telemetry(query=qtext, top_k=k)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        latencies.append(elapsed_ms)

        cur_emb_mode = ret_telemetry.get("embedding_mode", "UNKNOWN")
        cur_vec_backend = ret_telemetry.get("vector_backend", "UNKNOWN")
        embedding_modes.add(cur_emb_mode)
        vector_backends.add(cur_vec_backend)

        retrieved_ids = [r["chunk_id"] for r in retrieved]
        top1_id = retrieved_ids[0] if retrieved_ids else "NONE"

        # 1. Hit Rate @ K
        is_hit = any(cid in expected or cid.startswith(cond) for cid in retrieved_ids)
        if is_hit:
            hits += 1

        # 2. Reciprocal Rank
        rr = 0.0
        for rank, cid in enumerate(retrieved_ids, 1):
            if cid in expected or cid.startswith(cond):
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)

        # 3. Precision @ K
        relevant_in_top_k = sum(1 for cid in retrieved_ids if cid in expected or cid.startswith(cond))
        p_at_k = relevant_in_top_k / k
        precision_scores.append(p_at_k)

        retrieval_details.append({
            "id": qid,
            "query": qtext,
            "expected_chunk_ids": expected,
            "retrieved_chunk_ids": retrieved_ids,
            "hit": is_hit,
            "reciprocal_rank": round(rr, 4),
            "precision_at_k": round(p_at_k, 4),
            "latency_ms": round(elapsed_ms, 2)
        })

        print(f"{qid:<5} | {cond:<10} | {('SI' if is_hit else 'NO'):<7} | {rr:<6.2f} | {p_at_k:<6.2f} | {elapsed_ms:<8.2f} ms | {top1_id}")

        # Evaluación de Generación (Bloque B)
        pipe_res = await pipeline.run_pipeline(qtext)
        gen_telemetry = pipe_res.get("telemetry", {})
        cur_llm_prov = gen_telemetry.get("llm_provider", "unknown")
        llm_providers.add(cur_llm_prov)

        response_text = pipe_res.get("response", "")
        resp_lower = response_text.lower()
        if item.get("category") == "contraindications":
            is_adherent = any(w in resp_lower for w in ["prohibid", "advertencia", "evitar", "riesgo", "precaucion", "no es seguro", "contraindic"])
        else:
            is_adherent = any(w in resp_lower for w in ["recomenda", "ejercicio", "fuerza", "progresion", "adaptad", "guia", "evidencia", "clinica"])
        
        if is_adherent:
            adherent_count += 1

        generation_details.append({
            "id": qid,
            "llm_provider": cur_llm_prov,
            "clinical_adherence": is_adherent,
            "response_sample": response_text[:120].encode('ascii', 'ignore').decode('ascii') + "..."
        })

    total = len(queries)
    hit_rate = (hits / total) * 100.0
    mrr = sum(reciprocal_ranks) / total
    mean_precision = sum(precision_scores) / total
    avg_latency = sum(latencies) / total
    p95_latency = sorted(latencies)[int(0.95 * total)]
    adherence_rate = (adherent_count / total) * 100.0

    emb_mode_final = list(embedding_modes)[0] if len(embedding_modes) == 1 else list(embedding_modes)
    vec_backend_final = list(vector_backends)[0] if len(vector_backends) == 1 else list(vector_backends)
    llm_prov_final = list(llm_providers)[0] if len(llm_providers) == 1 else list(llm_providers)

    print("\n" + "=" * 85)
    print("BLOQUE A: METRICAS DE RECUPERACION (RETRIEVAL QUALITY)")
    print("=" * 85)
    print(f" * Hit Rate @ 3:               {hit_rate:.2f}%  (Meta: >= 85.0%)  -> {'SUPERADA' if hit_rate >= 85 else 'NO ALCANZADA'}")
    print(f" * Mean Reciprocal Rank (MRR): {mrr:.4f}  (Meta: >= 0.80)   -> {'SUPERADA' if mrr >= 0.80 else 'NO ALCANZADA'}")
    print(f" * Precision @ 3:              {mean_precision:.4f}  (Meta: >= 0.70)   -> {'SUPERADA' if mean_precision >= 0.70 else 'NO ALCANZADA'}")
    print(f" * Latencia Promedio:          {avg_latency:.2f} ms")
    print(f" * Latencia P95:               {p95_latency:.2f} ms")
    print(f" * Modo Embeddings:            {emb_mode_final}")
    print(f" * Backend Vectorial:          {vec_backend_final}")

    print("\n" + "=" * 85)
    print("BLOQUE B: ANALISIS DE GENERACION (RESPONSE EVALUATION)")
    print("=" * 85)
    print(f" * Tasa de Adherencia Clinica: {adherence_rate:.2f}% (Meta: >= 90.0%) -> {'SUPERADA' if adherence_rate >= 90 else 'NO ALCANZADA'}")
    print(f" * Proveedor LLM Efectivo:      {llm_prov_final}")
    print(f" * Consultas Evaluadas:         {total}")
    print("=" * 85)

    output_data = {
        "telemetry": {
            "embedding_mode": emb_mode_final,
            "vector_backend": vec_backend_final,
            "llm_provider": llm_prov_final
        },
        "retrieval_metrics": {
            "hit_rate_at_3": round(hit_rate, 2),
            "mrr": round(mrr, 4),
            "precision_at_3": round(mean_precision, 4),
            "avg_latency_ms": round(avg_latency, 2),
            "p95_latency_ms": round(p95_latency, 2),
            "total_queries": total
        },
        "generation_evaluation": {
            "clinical_adherence_rate": round(adherence_rate, 2),
            "llm_provider_used": llm_prov_final,
            "total_evaluated": total
        },
        "retrieval_details": retrieval_details,
        "generation_details": generation_details
    }

    dest_paths = [
        os.path.join("data", "evaluation", "retrieval_benchmark_results.json"),
        os.path.join("docs", "evaluation", "retrieval_benchmark_results.json")
    ]
    for p in dest_paths:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2)
        print(f"[Reporte]: Exportado a {p}")


if __name__ == "__main__":
    asyncio.run(main())
