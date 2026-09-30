"""Analyze FlashRank quality sensitivity at top-k 4, 5, and 6.

The previous comparison output stores only top-4, so this script reranks the
saved candidate pool once and persists the complete candidate ordering for
future top-k analyses. It never runs retrieval or imports production RAG code.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from benchmark.reranker.compare_rerankers import (  # noqa: E402
    OUTPUT_DIR,
    aggregate_latency,
    binary_dcg,
    collect_environment,
    evidence_is_covered,
    is_expected_document,
    load_flashrank,
    normalize_document_name,
    normalize_text,
    rerank_flashrank,
    validate_and_prepare,
)


TOP_K_VALUES = (4, 5, 6)
OUTPUT_PATH = OUTPUT_DIR / "topk_sensitivity.json"
CROSSENCODER_RESULT_PATH = OUTPUT_DIR / "crossencoder_rankings.json"
FLASHRANK_RESULT_PATH = OUTPUT_DIR / "flashrank_rankings.json"

METRIC_NAMES = (
    "hit_rate",
    "expected_document_recall",
    "precision",
    "mrr",
    "binary_ndcg",
    "evidence_coverage",
)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def calculate_metrics(
    row: dict[str, Any],
    ranked_indexes: list[int],
    top_k: int,
) -> dict[str, float | None]:
    candidates = row["candidates"]
    top_candidates = [candidates[index] for index in ranked_indexes[:top_k]]
    expected_documents = {
        normalize_document_name(str(document))
        for document in row["expected_documents"]
        if normalize_document_name(str(document))
    }

    top_relevances = [
        int(is_expected_document(candidate, expected_documents))
        for candidate in top_candidates
    ]
    represented_documents = {
        normalize_document_name(str(candidate["metadata"].get("document", "")))
        for candidate in top_candidates
        if is_expected_document(candidate, expected_documents)
    }
    all_relevant_count = sum(
        is_expected_document(candidate, expected_documents)
        for candidate in candidates
    )
    first_relevant_rank = next(
        (rank for rank, relevant in enumerate(top_relevances, start=1) if relevant),
        None,
    )
    ideal_relevances = [1] * min(all_relevant_count, top_k)
    ideal_relevances.extend([0] * (top_k - len(ideal_relevances)))
    ideal_dcg = binary_dcg(ideal_relevances)

    normalized_top_texts = [
        normalize_text(candidate["content"]) for candidate in top_candidates
    ]
    evidence_items = [
        str(item) for item in row["evidence"] if normalize_text(str(item))
    ]
    covered_evidence = sum(
        evidence_is_covered(item, normalized_top_texts) for item in evidence_items
    )

    has_document_labels = bool(expected_documents)
    return {
        "hit_rate": float(any(top_relevances)) if has_document_labels else None,
        "expected_document_recall": (
            len(represented_documents) / len(expected_documents)
            if has_document_labels
            else None
        ),
        "precision": (
            sum(top_relevances) / len(top_candidates)
            if has_document_labels and top_candidates
            else None
        ),
        "mrr": (
            (1.0 / first_relevant_rank if first_relevant_rank else 0.0)
            if has_document_labels
            else None
        ),
        "binary_ndcg": (
            (binary_dcg(top_relevances) / ideal_dcg if ideal_dcg else 0.0)
            if has_document_labels
            else None
        ),
        "evidence_coverage": (
            covered_evidence / len(evidence_items) if evidence_items else None
        ),
    }


def aggregate_metrics(
    query_metrics: list[dict[str, float | None]],
) -> tuple[dict[str, float | None], dict[str, int]]:
    aggregate: dict[str, float | None] = {}
    counts: dict[str, int] = {}
    for metric in METRIC_NAMES:
        values = [
            item[metric] for item in query_metrics if item[metric] is not None
        ]
        counts[metric] = len(values)
        aggregate[metric] = statistics.fmean(values) if values else None
    return aggregate, counts


def metric_delta(
    later: dict[str, float | None],
    earlier: dict[str, float | None],
) -> dict[str, float | None]:
    return {
        metric: (
            later[metric] - earlier[metric]
            if later[metric] is not None and earlier[metric] is not None
            else None
        )
        for metric in METRIC_NAMES
    }


def crossencoder_baseline() -> dict[str, Any] | None:
    if not CROSSENCODER_RESULT_PATH.exists():
        return None
    result = load_json(CROSSENCODER_RESULT_PATH)
    return {
        "model": result["configuration"]["model"],
        "backend": result["configuration"]["backend"],
        "device": result["configuration"]["device"],
        "top_k": result["top_k"],
        "quality_metrics": result["quality_metrics"],
        "quality_metric_query_counts": result["quality_metric_query_counts"],
    }


def main() -> None:
    rows, validation = validate_and_prepare(limit=None)
    previous_flashrank = load_json(FLASHRANK_RESULT_PATH)
    saved_lengths = {
        len(query["top_k_ranking"]) for query in previous_flashrank["queries"]
    }
    if saved_lengths != {4}:
        raise ValueError(
            "Expected the previous FlashRank result to contain only top-4; "
            f"found saved lengths {sorted(saved_lengths)}."
        )

    model, model_load_time, configuration = load_flashrank()
    if configuration["model"] != "ms-marco-MultiBERT-L-12":
        raise RuntimeError(f"Unexpected FlashRank model: {configuration['model']}")
    if configuration["backend"] != "ONNX Runtime":
        raise RuntimeError(f"Unexpected backend: {configuration['backend']}")
    if "CPUExecutionProvider" not in configuration["onnx_providers"]:
        raise RuntimeError(
            "FlashRank is not using CPUExecutionProvider: "
            f"{configuration['onnx_providers']}"
        )

    warmup_started = time.perf_counter()
    rerank_flashrank(model, rows[0]["query"], rows[0]["candidates"])
    warmup_time = time.perf_counter() - warmup_started

    latencies: list[float] = []
    query_outputs: list[dict[str, Any]] = []
    metrics_by_k: dict[int, list[dict[str, float | None]]] = {
        top_k: [] for top_k in TOP_K_VALUES
    }

    for position, row in enumerate(rows, start=1):
        started = time.perf_counter()
        ranking = rerank_flashrank(model, row["query"], row["candidates"])
        latency = time.perf_counter() - started
        latencies.append(latency)
        ranked_indexes = [index for index, _ in ranking]

        if len(ranked_indexes) != len(row["candidates"]):
            raise RuntimeError(
                f"Incomplete ranking for question {row['question_id']}."
            )

        per_k: dict[str, dict[str, float | None]] = {}
        for top_k in TOP_K_VALUES:
            metrics = calculate_metrics(row, ranked_indexes, top_k)
            metrics_by_k[top_k].append(metrics)
            per_k[str(top_k)] = metrics

        query_outputs.append(
            {
                "question_id": row["question_id"],
                "candidate_fingerprint": row["candidate_fingerprint"],
                "candidate_count": len(row["candidates"]),
                "full_ranking": [
                    {
                        "rank": rank,
                        "candidate_id": row["candidates"][index]["candidate_id"],
                        "original_candidate_index": index,
                        "model_specific_score": score,
                    }
                    for rank, (index, score) in enumerate(ranking, start=1)
                ],
                "metrics_by_top_k": per_k,
            }
        )
        print(
            f"[flashrank top-k] {position}/{len(rows)} "
            f"question_id={row['question_id']} latency={latency:.4f}s",
            flush=True,
        )

    aggregate_by_k: dict[str, dict[str, float | None]] = {}
    counts_by_k: dict[str, dict[str, int]] = {}
    for top_k in TOP_K_VALUES:
        aggregate, counts = aggregate_metrics(metrics_by_k[top_k])
        aggregate_by_k[str(top_k)] = aggregate
        counts_by_k[str(top_k)] = counts

    candidate_counts = [len(row["candidates"]) for row in rows]
    payload = {
        "schema_version": 1,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "analysis": "FlashRank top-k sensitivity using one complete reranking run.",
        "evaluated_queries": len(rows),
        "top_k_values": list(TOP_K_VALUES),
        "rerank_required": True,
        "rerank_reason": (
            "The previous full benchmark output stored only top-4 for every "
            "query, not the complete candidate ordering required for top-5/top-6."
        ),
        "input_validation": validation,
        "configuration": configuration,
        "environment": collect_environment(),
        "candidate_statistics": {
            "total_candidates": sum(candidate_counts),
            "minimum_per_query": min(candidate_counts),
            "maximum_per_query": max(candidate_counts),
            "mean_per_query": statistics.fmean(candidate_counts),
        },
        "context_count": {
            "flashrank_at_4_mean_chunks": 4,
            "flashrank_at_5_mean_chunks": 5,
            "flashrank_at_6_mean_chunks": 6,
            "at_5_vs_at_4_absolute_increase": 1,
            "at_5_vs_at_4_percent_increase": 25.0,
            "at_6_vs_at_4_absolute_increase": 2,
            "at_6_vs_at_4_percent_increase": 50.0,
        },
        "quality_metrics_by_top_k": aggregate_by_k,
        "quality_metric_query_counts_by_top_k": counts_by_k,
        "absolute_deltas": {
            "at_4_to_at_5": metric_delta(aggregate_by_k["5"], aggregate_by_k["4"]),
            "at_5_to_at_6": metric_delta(aggregate_by_k["6"], aggregate_by_k["5"]),
            "at_4_to_at_6": metric_delta(aggregate_by_k["6"], aggregate_by_k["4"]),
        },
        "crossencoder_at_4_baseline": crossencoder_baseline(),
        "rerank_execution": {
            "note": (
                "Latency is independent of output top-k because FlashRank reranked "
                "the complete saved candidate pool once. Increasing top-k changes "
                "downstream context size, not reranking work in this analysis."
            ),
            "model_load_time_seconds": model_load_time,
            "warmup_time_seconds": warmup_time,
            **aggregate_latency(latencies),
        },
        "limitations": [
            (
                "Expected-document matching is proxy relevance, not human-labelled "
                "chunk relevance; document metrics exclude rows without labels."
            ),
            (
                "Precision and binary nDCG inherit the document-level proxy "
                "limitation and may reward multiple chunks from one document."
            ),
            (
                "Evidence Coverage uses normalized exact containment overlap, "
                "not semantic equivalence; rows without evidence are excluded."
            ),
            (
                "Increasing top-k increases downstream LLM context count; this "
                "analysis does not estimate token count or answer quality."
            ),
        ],
        "queries": query_outputs,
    }
    save_json(OUTPUT_PATH, payload)
    print(f"Saved {OUTPUT_PATH.relative_to(REPO_ROOT)}", flush=True)


if __name__ == "__main__":
    main()
