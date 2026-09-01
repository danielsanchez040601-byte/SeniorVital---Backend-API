"""
Script de Evaluación Automatizada y Cálculo Empírico de Métricas RAG.
Evalúa Hit Rate@3, MRR, Precision@3 y Latencia sobre data/evaluation/rag_eval_dataset.json.
Genera reporte estructurado de resultados en docs/evaluation/.
"""
import os
import sys
import json
import time
import asyncio
from typing import List, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.rag.retriever.retriever import ClinicalRetriever


async def main():
    print("=" * 85)
    print("SENIORVITAL 2.0 - EVALUACION AUTOMATIZADA DE METRICAS DE RECUPERACION (RAG)")
    print("=" * 85)

    dataset_path = os.path.join("data", "evaluation", "rag_eval_dataset.json")
    if not os.path.exists(dataset_path):
        print(f"[ERROR] Dataset no encontrado en {dataset_path}")
        return

    with open(dataset_path, "r", encoding="utf-8") as f:
        queries = json.load(f)

    retriever = ClinicalRetriever()
    # Warmup
    await retriever.retrieve(query="warmup", top_k=1)

    k = 3
    hits = 0
    reciprocal_ranks = []
    precision_scores = []
    latencies = []
    results_detail = []

    print(f"[Dataset]: {len(queries)} consultas clinicas anotadas para benchmarking (Top-K = {k}).\n")
    print(f"{'ID':<5} | {'Condicion':<10} | {'Hit@3':<7} | {'MRR':<6} | {'P@3':<6} | {'Latencia':<10} | {'Top-1 Chunk'}")
    print("-" * 85)

    for item in queries:
        qid = item["id"]
        qtext = item["query"]
        expected = item["expected_chunk_ids"]
        cond = item["condition_id"]

        start_time = time.perf_counter()
        retrieved = await retriever.retrieve(query=qtext, top_k=k)
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        latencies.append(elapsed_ms)

        retrieved_ids = [r["chunk_id"] for r in retrieved]
        top1_id = retrieved_ids[0] if retrieved_ids else "NONE"

        # 1. Hit Rate @ K (Al menos 1 chunk esperado o de la condicion en Top-K)
        is_hit = any(cid in expected or cid.startswith(cond) for cid in retrieved_ids)
        if is_hit:
            hits += 1

        # 2. Reciprocal Rank (Posición inversa del primer relevante)
        rr = 0.0
        for rank, cid in enumerate(retrieved_ids, 1):
            if cid in expected or cid.startswith(cond):
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)

        # 3. Precision @ K (Fracción de chunks relevantes en Top-K)
        relevant_in_top_k = sum(1 for cid in retrieved_ids if cid in expected or cid.startswith(cond))
        p_at_k = relevant_in_top_k / k
        precision_scores.append(p_at_k)

        results_detail.append({
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

    total = len(queries)
    hit_rate = (hits / total) * 100.0
    mrr = sum(reciprocal_ranks) / total
    mean_precision = sum(precision_scores) / total
    avg_latency = sum(latencies) / total
    p95_latency = sorted(latencies)[int(0.95 * total)]

    print("\n" + "=" * 85)
    print("RESUMEN GENERAL DE METRICAS EMPIRICAS CALCULADAS:")
    print("=" * 85)
    print(f" * Hit Rate @ 3:             {hit_rate:.2f}%  (Meta: >= 85.0%)  -> {'SUPERADA' if hit_rate >= 85 else 'NO ALCANZADA'}")
    print(f" * Mean Reciprocal Rank:     {mrr:.4f}  (Meta: >= 0.80)   -> {'SUPERADA' if mrr >= 0.80 else 'NO ALCANZADA'}")
    print(f" * Precision @ 3:            {mean_precision:.4f}  (Meta: >= 0.70)   -> {'SUPERADA' if mean_precision >= 0.70 else 'NO ALCANZADA'}")
    print(f" * Latencia Promedio:        {avg_latency:.2f} ms")
    print(f" * Latencia P95:             {p95_latency:.2f} ms (Meta: <= 100 ms)  -> {'SUPERADA' if p95_latency <= 100 else 'NO ALCANZADA'}")
    print("=" * 85)

    # Guardar reporte en JSON
    output_dir = os.path.join("docs", "evaluation")
    os.makedirs(output_dir, exist_ok=True)
    report_json_path = os.path.join(output_dir, "retrieval_benchmark_results.json")
    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump({
            "metrics": {
                "hit_rate_at_3": round(hit_rate, 2),
                "mrr": round(mrr, 4),
                "precision_at_3": round(mean_precision, 4),
                "avg_latency_ms": round(avg_latency, 2),
                "p95_latency_ms": round(p95_latency, 2),
                "total_queries_evaluated": total
            },
            "detailed_results": results_detail
        }, f, indent=2)

    print(f"\n[Reporte]: Resultados exportados a {report_json_path}")


if __name__ == "__main__":
    asyncio.run(main())
