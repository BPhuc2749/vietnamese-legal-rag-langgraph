"""Compare two complete reranker configurations on one saved candidate pool.

This benchmark intentionally does not run retrieval, generate answers, call an
LLM judge, or import the production reranker implementation.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import statistics
import subprocess
import sys
import tempfile
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


REPO_ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = REPO_ROOT / "data" / "data_test" / "data_test.json"
CANDIDATE_PATH = (
    REPO_ROOT
    / "benchmark"
    / "reranker"
    / "results"
    / "retrieval_results.json"
)
OUTPUT_DIR = (
    REPO_ROOT / "benchmark" / "reranker" / "results" / "comparison"
)

CROSSENCODER_MODEL = "BAAI/bge-reranker-v2-m3"
DEFAULT_FLASHRANK_MODEL = "ms-marco-MultiBERT-L-12"
TOP_K = 4
CROSSENCODER_BATCH_SIZE = 16

QUALITY_KEYS = (
    "hit_rate_at_4",
    "expected_document_recall_at_4",
    "precision_at_4",
    "mrr_at_4",
    "binary_ndcg_at_4",
    "evidence_coverage_at_4",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare BAAI/bge-reranker-v2-m3 and the configured FlashRank "
            "model using saved retrieval candidates."
        )
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Run only the first N aligned questions (for smoke tests).",
    )
    parser.add_argument(
        "--reranker",
        choices=("crossencoder", "flashrank", "both"),
        default="both",
        help="Run one configuration or both configurations (default: both).",
    )
    parser.add_argument(
        "--worker",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, ensure_ascii=False, indent=2)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    return " ".join(normalized.split())


def normalize_document_name(value: str) -> str:
    normalized = normalize_text(value)
    if normalized.endswith(".pdf"):
        normalized = normalized[:-4]
    return normalized.strip()


def configured_flashrank_model() -> str:
    environment_value = os.getenv("RERANKER_MODEL", "").strip()
    if environment_value:
        return environment_value

    env_path = REPO_ROOT / ".env"
    if env_path.exists():
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() == "RERANKER_MODEL" and value.strip():
                return value.strip().strip("\"").strip("'")

    return DEFAULT_FLASHRANK_MODEL


def validate_and_prepare(limit: int | None) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    dataset = load_json(DATASET_PATH)
    candidate_rows = load_json(CANDIDATE_PATH)

    if not isinstance(dataset, list) or not isinstance(candidate_rows, list):
        raise ValueError("Dataset and candidate pool must both be JSON arrays.")
    if len(dataset) != len(candidate_rows):
        raise ValueError(
            "Row count mismatch: "
            f"dataset={len(dataset)}, candidates={len(candidate_rows)}"
        )
    if limit is not None and (limit < 1 or limit > len(dataset)):
        raise ValueError(f"--limit must be between 1 and {len(dataset)}.")

    dataset_ids = [str(item.get("id", "")) for item in dataset]
    candidate_ids = [str(item.get("id", "")) for item in candidate_rows]
    if len(set(dataset_ids)) != len(dataset_ids):
        raise ValueError("Dataset contains duplicate question IDs.")
    if len(set(candidate_ids)) != len(candidate_ids):
        raise ValueError("Candidate pool contains duplicate question IDs.")

    prepared_rows: list[dict[str, Any]] = []
    total_candidates = 0

    for row_index, (dataset_row, candidate_row) in enumerate(
        zip(dataset, candidate_rows, strict=True)
    ):
        question_id = str(dataset_row.get("id", ""))
        if question_id != str(candidate_row.get("id", "")):
            raise ValueError(
                f"ID mismatch at row {row_index}: "
                f"dataset={question_id!r}, candidate={candidate_row.get('id')!r}"
            )

        for field in ("question", "ground_truth", "evidence"):
            if dataset_row.get(field) != candidate_row.get(field):
                raise ValueError(
                    f"Field {field!r} differs for question ID {question_id}."
                )

        question = dataset_row.get("question")
        evidence = dataset_row.get("evidence")
        expected_documents = dataset_row.get("documents")
        candidates = candidate_row.get("candidates")

        if not isinstance(question, str) or not question.strip():
            raise ValueError(f"Question {question_id} has no usable query text.")
        if not isinstance(evidence, list):
            raise ValueError(f"Question {question_id} has invalid evidence.")
        if not isinstance(expected_documents, list):
            raise ValueError(
                f"Question {question_id} has invalid expected document labels."
            )
        if not isinstance(candidates, list) or not candidates:
            raise ValueError(f"Question {question_id} has no candidates.")

        prepared_candidates: list[dict[str, Any]] = []
        for original_index, candidate in enumerate(candidates):
            content = candidate.get("content")
            metadata = candidate.get("metadata")
            if not isinstance(content, str) or not content.strip():
                raise ValueError(
                    f"Question {question_id}, candidate {original_index} "
                    "has no content."
                )
            if not isinstance(metadata, dict) or not metadata.get("document"):
                raise ValueError(
                    f"Question {question_id}, candidate {original_index} "
                    "has no document metadata."
                )

            stable_id = f"q{question_id}_c{original_index:03d}"
            prepared_candidates.append(
                {
                    "candidate_id": stable_id,
                    "original_index": original_index,
                    "content": content,
                    "content_sha256": sha256_text(content),
                    "metadata": metadata,
                    "source": list(candidate.get("source", [])),
                }
            )

        fingerprint_payload = [
            {
                "candidate_id": candidate["candidate_id"],
                "content_sha256": candidate["content_sha256"],
            }
            for candidate in prepared_candidates
        ]
        candidate_fingerprint = sha256_text(
            json.dumps(fingerprint_payload, ensure_ascii=False, separators=(",", ":"))
        )

        prepared_rows.append(
            {
                "question_id": question_id,
                "query": question,
                "evidence": evidence,
                "expected_documents": expected_documents,
                "candidate_fingerprint": candidate_fingerprint,
                "candidates": prepared_candidates,
            }
        )
        total_candidates += len(prepared_candidates)

    selected_rows = prepared_rows[:limit] if limit is not None else prepared_rows
    validation = {
        "dataset_rows": len(dataset),
        "candidate_rows": len(candidate_rows),
        "selected_rows": len(selected_rows),
        "selected_candidates": sum(len(row["candidates"]) for row in selected_rows),
        "all_candidates": total_candidates,
        "row_alignment_valid": True,
        "dataset_sha256": sha256_file(DATASET_PATH),
        "candidate_pool_sha256": sha256_file(CANDIDATE_PATH),
    }
    return selected_rows, validation


def package_version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def collect_environment() -> dict[str, Any]:
    torch_threads: int | None = None
    torch_interop_threads: int | None = None
    torch_cuda_available = False
    torch_cuda_version: str | None = None
    torch_cuda_device_count = 0
    torch_cuda_device_name: str | None = None
    try:
        import torch

        torch_threads = torch.get_num_threads()
        torch_interop_threads = torch.get_num_interop_threads()
        torch_cuda_available = torch.cuda.is_available()
        torch_cuda_version = torch.version.cuda
        torch_cuda_device_count = torch.cuda.device_count()
        if torch_cuda_available and torch_cuda_device_count:
            torch_cuda_device_name = torch.cuda.get_device_name(0)
    except ImportError:
        pass

    return {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "processor": platform.processor() or os.getenv("PROCESSOR_IDENTIFIER", ""),
        "logical_cpu_count": os.cpu_count(),
        "torch_version": package_version("torch"),
        "sentence_transformers_version": package_version("sentence-transformers"),
        "flashrank_version": package_version("flashrank"),
        "torch_num_threads": torch_threads,
        "torch_num_interop_threads": torch_interop_threads,
        "torch_cuda_available": torch_cuda_available,
        "torch_cuda_version": torch_cuda_version,
        "torch_cuda_device_count": torch_cuda_device_count,
        "torch_cuda_device_name": torch_cuda_device_name,
        "thread_environment": {
            key: os.getenv(key)
            for key in (
                "OMP_NUM_THREADS",
                "MKL_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "NUMEXPR_NUM_THREADS",
            )
        },
    }


def crossencoder_device(limit: int | None) -> tuple[str, dict[str, Any]]:
    try:
        import torch
    except ImportError as error:
        raise RuntimeError("Missing dependency: torch is required.") from error

    cuda_available = torch.cuda.is_available()
    if not cuda_available and limit is None:
        raise RuntimeError(
            "Full CrossEncoder benchmark requires CUDA, but "
            "torch.cuda.is_available() is False. Refusing to run the full "
            "CrossEncoder dataset on CPU. Install a CUDA-enabled PyTorch build "
            "and verify the GPU environment, or use --limit for a CPU smoke test."
        )

    device = "cuda" if cuda_available else "cpu"
    details = {
        "cuda_available": cuda_available,
        "cuda_runtime_version": torch.version.cuda,
        "cuda_device_name": (
            torch.cuda.get_device_name(0) if cuda_available else None
        ),
        "cpu_fallback_for_smoke_test": not cuda_available,
    }
    return device, details


def load_crossencoder(limit: int | None) -> tuple[Any, float, dict[str, Any]]:
    if package_version("sentence-transformers") is None:
        raise RuntimeError(
            "Missing dependency: sentence-transformers is required."
        )
    try:
        from sentence_transformers import CrossEncoder
    except ImportError as error:
        raise RuntimeError(
            f"Failed to import sentence-transformers: {error}"
        ) from error

    requested_device, device_details = crossencoder_device(limit)
    started = time.perf_counter()
    model = CrossEncoder(CROSSENCODER_MODEL, device=requested_device)
    load_time = time.perf_counter() - started
    device = str(getattr(model, "device", requested_device))
    if requested_device == "cuda" and not device.startswith("cuda"):
        raise RuntimeError(
            "CrossEncoder CUDA was requested but the loaded model reports "
            f"device={device!r}."
        )
    if requested_device == "cpu" and not device.startswith("cpu"):
        raise RuntimeError(
            "CrossEncoder CPU smoke fallback was requested but the loaded "
            f"model reports device={device!r}."
        )
    return model, load_time, {
        "implementation": "sentence_transformers.CrossEncoder",
        "model": CROSSENCODER_MODEL,
        "backend": "PyTorch",
        "device": device,
        "batch_size": CROSSENCODER_BATCH_SIZE,
        **device_details,
    }


def rerank_crossencoder(
    model: Any,
    query: str,
    candidates: list[dict[str, Any]],
) -> list[tuple[int, float]]:
    pairs = [(query, candidate["content"]) for candidate in candidates]
    scores = model.predict(
        pairs,
        batch_size=CROSSENCODER_BATCH_SIZE,
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    score_values = scores.tolist() if hasattr(scores, "tolist") else list(scores)
    if any(isinstance(score, (list, tuple)) for score in score_values):
        raise RuntimeError("CrossEncoder returned non-scalar scores.")
    indexed_scores = [
        (index, float(score)) for index, score in enumerate(score_values)
    ]
    return sorted(indexed_scores, key=lambda item: (-item[1], item[0]))


def load_flashrank() -> tuple[Any, float, dict[str, Any]]:
    if package_version("flashrank") is None:
        raise RuntimeError("Missing dependency: flashrank is required.")
    try:
        from flashrank import Ranker
    except ImportError as error:
        raise RuntimeError(f"Failed to import flashrank: {error}") from error

    model_name = configured_flashrank_model()
    cache_dir = Path(tempfile.gettempdir()) / "legal-rag-flashrank"
    started = time.perf_counter()
    model = Ranker(
        model_name=model_name,
        cache_dir=str(cache_dir),
        max_length=512,
    )
    load_time = time.perf_counter() - started

    providers: list[str] = []
    session = getattr(model, "session", None)
    if session is not None and hasattr(session, "get_providers"):
        providers = list(session.get_providers())

    if any(provider.startswith("CUDAExecutionProvider") for provider in providers):
        device = "cuda"
    elif any(provider.startswith("CPUExecutionProvider") for provider in providers):
        device = "cpu"
    else:
        device = "provider-dependent" if providers else "unknown"

    return model, load_time, {
        "implementation": "flashrank.Ranker",
        "model": model_name,
        "backend": "ONNX Runtime",
        "device": device,
        "max_length": 512,
        "cache_location": "system temporary directory",
        "onnx_providers": providers,
    }


def rerank_flashrank(
    model: Any,
    query: str,
    candidates: list[dict[str, Any]],
) -> list[tuple[int, float]]:
    from flashrank import RerankRequest

    passages = [
        {"id": index, "text": candidate["content"]}
        for index, candidate in enumerate(candidates)
    ]
    results = model.rerank(RerankRequest(query=query, passages=passages))
    ranking = [
        (int(item["id"]), float(item["score"]))
        for item in results
    ]
    ranked_indexes = [index for index, _ in ranking]
    if len(ranking) != len(candidates) or set(ranked_indexes) != set(
        range(len(candidates))
    ):
        raise RuntimeError("FlashRank did not return every input candidate exactly once.")
    return ranking


def is_expected_document(candidate: dict[str, Any], expected: set[str]) -> bool:
    candidate_document = normalize_document_name(
        str(candidate["metadata"].get("document", ""))
    )
    return candidate_document in expected


def evidence_is_covered(evidence: str, candidate_texts: list[str]) -> bool:
    normalized_evidence = normalize_text(evidence)
    if not normalized_evidence:
        return False
    return any(
        normalized_evidence in candidate_text
        or candidate_text in normalized_evidence
        for candidate_text in candidate_texts
        if candidate_text
    )


def binary_dcg(relevances: list[int]) -> float:
    return sum(
        relevance / math.log2(rank + 1)
        for rank, relevance in enumerate(relevances, start=1)
    )


def calculate_query_metrics(
    row: dict[str, Any],
    ranked_indexes: list[int],
) -> dict[str, float | None]:
    candidates = row["candidates"]
    top_indexes = ranked_indexes[:TOP_K]
    top_candidates = [candidates[index] for index in top_indexes]
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
        (rank for rank, relevance in enumerate(top_relevances, start=1) if relevance),
        None,
    )
    ideal_relevances = [1] * min(all_relevant_count, TOP_K)
    ideal_relevances.extend([0] * (TOP_K - len(ideal_relevances)))
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
        "hit_rate_at_4": (
            float(any(top_relevances)) if has_document_labels else None
        ),
        "expected_document_recall_at_4": (
            len(represented_documents) / len(expected_documents)
            if has_document_labels
            else None
        ),
        "precision_at_4": (
            sum(top_relevances) / len(top_candidates)
            if has_document_labels and top_candidates
            else None
        ),
        "mrr_at_4": (
            (1.0 / first_relevant_rank if first_relevant_rank else 0.0)
            if has_document_labels
            else None
        ),
        "binary_ndcg_at_4": (
            (binary_dcg(top_relevances) / ideal_dcg if ideal_dcg else 0.0)
            if has_document_labels
            else None
        ),
        "evidence_coverage_at_4": (
            covered_evidence / len(evidence_items) if evidence_items else None
        ),
    }


def aggregate_quality(
    query_results: list[dict[str, Any]],
) -> tuple[dict[str, float | None], dict[str, int]]:
    metrics: dict[str, float | None] = {}
    query_counts: dict[str, int] = {}
    for key in QUALITY_KEYS:
        values = [
            result["quality_metrics"][key]
            for result in query_results
            if result["quality_metrics"][key] is not None
        ]
        query_counts[key] = len(values)
        metrics[key] = statistics.fmean(values) if values else None
    return metrics, query_counts


def percentile_nearest_rank(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def aggregate_latency(latencies: list[float]) -> dict[str, float]:
    return {
        "total_rerank_time_seconds": sum(latencies),
        "mean_latency_seconds_per_query": statistics.fmean(latencies),
        "median_latency_seconds_per_query": statistics.median(latencies),
        "min_latency_seconds_per_query": min(latencies),
        "max_latency_seconds_per_query": max(latencies),
        "p95_latency_seconds_per_query": percentile_nearest_rank(latencies, 0.95),
    }


def output_suffix(limit: int | None) -> str:
    return f"_limit{limit}" if limit is not None else ""


def ranking_path(reranker_name: str, limit: int | None) -> Path:
    return OUTPUT_DIR / f"{reranker_name}_rankings{output_suffix(limit)}.json"


def summary_path(limit: int | None) -> Path:
    return OUTPUT_DIR / f"summary{output_suffix(limit)}.json"


def run_reranker(reranker_name: str, limit: int | None) -> Path:
    rows, validation = validate_and_prepare(limit)
    environment = collect_environment()

    if reranker_name == "crossencoder":
        model, model_load_time, configuration = load_crossencoder(limit)
        rerank_function: Callable[
            [Any, str, list[dict[str, Any]]], list[tuple[int, float]]
        ] = rerank_crossencoder
    elif reranker_name == "flashrank":
        model, model_load_time, configuration = load_flashrank()
        rerank_function = rerank_flashrank
    else:
        raise ValueError(f"Unsupported reranker: {reranker_name}")

    warmup_started = time.perf_counter()
    rerank_function(model, rows[0]["query"], rows[0]["candidates"])
    warmup_time = time.perf_counter() - warmup_started

    query_results: list[dict[str, Any]] = []
    latencies: list[float] = []

    for position, row in enumerate(rows, start=1):
        started = time.perf_counter()
        full_ranking = rerank_function(model, row["query"], row["candidates"])
        latency = time.perf_counter() - started
        latencies.append(latency)

        ranked_indexes = [index for index, _ in full_ranking]
        if len(ranked_indexes) != len(row["candidates"]):
            raise RuntimeError(
                f"{reranker_name} returned an incomplete ranking for "
                f"question {row['question_id']}."
            )

        top_ranking = []
        for rank, (candidate_index, score) in enumerate(
            full_ranking[:TOP_K], start=1
        ):
            candidate = row["candidates"][candidate_index]
            top_ranking.append(
                {
                    "rank": rank,
                    "candidate_id": candidate["candidate_id"],
                    "original_candidate_index": candidate["original_index"],
                    "content_sha256": candidate["content_sha256"],
                    "document": candidate["metadata"].get("document"),
                    "source": candidate["source"],
                    "model_specific_score": score,
                }
            )

        query_result = {
            "question_id": row["question_id"],
            "query": row["query"],
            "candidate_count": len(row["candidates"]),
            "candidate_fingerprint": row["candidate_fingerprint"],
            "input_candidate_ids": [
                candidate["candidate_id"] for candidate in row["candidates"]
            ],
            "rerank_latency_seconds": latency,
            "top_k_ranking": top_ranking,
            "quality_metrics": calculate_query_metrics(row, ranked_indexes),
        }
        query_results.append(query_result)
        print(
            f"[{reranker_name}] {position}/{len(rows)} "
            f"question_id={row['question_id']} latency={latency:.4f}s",
            flush=True,
        )

    quality_metrics, quality_metric_query_counts = aggregate_quality(query_results)
    payload = {
        "schema_version": 2,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "reranker": reranker_name,
        "configuration": configuration,
        "top_k": TOP_K,
        "limit": limit,
        "validation": validation,
        "environment": environment,
        "timing": {
            "model_load_time_seconds": model_load_time,
            "warmup_time_seconds": warmup_time,
            **aggregate_latency(latencies),
        },
        "quality_metrics": quality_metrics,
        "quality_metric_query_counts": quality_metric_query_counts,
        "metric_notes": {
            "expected_document_matching": (
                "Proxy binary relevance derived from dataset document names; "
                "it is not human-labelled chunk relevance. Questions without "
                "document labels are excluded from document-based metrics."
            ),
            "evidence_coverage": (
                "Fraction of reference evidence passages with normalized exact "
                "containment overlap in at least one top-k candidate. Questions "
                "without evidence passages are excluded from this metric."
            ),
            "model_specific_score": (
                "Scores are retained only to reproduce each model's ordering "
                "and must not be compared across reranker configurations."
            ),
        },
        "queries": query_results,
    }

    destination = ranking_path(reranker_name, limit)
    save_json(destination, payload)
    print(f"Saved {destination.relative_to(REPO_ROOT)}", flush=True)
    return destination


def validate_comparable_outputs(
    crossencoder: dict[str, Any],
    flashrank: dict[str, Any],
) -> None:
    for field in ("dataset_sha256", "candidate_pool_sha256", "selected_rows"):
        if crossencoder["validation"][field] != flashrank["validation"][field]:
            raise ValueError(f"Reranker outputs differ on validation field {field}.")
    if crossencoder["top_k"] != flashrank["top_k"]:
        raise ValueError("Reranker outputs use different top-k values.")
    if crossencoder["limit"] != flashrank["limit"]:
        raise ValueError("Reranker outputs use different limits.")

    cross_queries = crossencoder["queries"]
    flash_queries = flashrank["queries"]
    if len(cross_queries) != len(flash_queries):
        raise ValueError("Reranker outputs contain different query counts.")

    for cross_query, flash_query in zip(cross_queries, flash_queries, strict=True):
        for field in (
            "question_id",
            "query",
            "candidate_fingerprint",
            "input_candidate_ids",
        ):
            if cross_query[field] != flash_query[field]:
                raise ValueError(
                    f"Reranker input mismatch for field {field}, "
                    f"question {cross_query['question_id']}."
                )


def safe_ratio(
    numerator: float | None,
    denominator: float | None,
) -> float | None:
    return numerator / denominator if numerator is not None and denominator else None


def create_summary(limit: int | None) -> Path:
    crossencoder = load_json(ranking_path("crossencoder", limit))
    flashrank = load_json(ranking_path("flashrank", limit))
    validate_comparable_outputs(crossencoder, flashrank)

    retention_metrics = (
        "expected_document_recall_at_4",
        "evidence_coverage_at_4",
        "mrr_at_4",
    )
    quality_retention = {
        metric: safe_ratio(
            flashrank["quality_metrics"][metric],
            crossencoder["quality_metrics"][metric],
        )
        for metric in retention_metrics
    }

    cross_mean = crossencoder["timing"]["mean_latency_seconds_per_query"]
    flash_mean = flashrank["timing"]["mean_latency_seconds_per_query"]
    mean_reduction = cross_mean - flash_mean

    compact_configurations: dict[str, dict[str, Any]] = {}
    for name, result in (
        ("crossencoder", crossencoder),
        ("flashrank", flashrank),
    ):
        configuration = result["configuration"]
        timing = result["timing"]
        compact_configurations[name] = {
            "model": configuration["model"],
            "implementation": configuration["implementation"],
            "backend": configuration["backend"],
            "device": configuration["device"],
            "mean_latency_seconds_per_query": timing[
                "mean_latency_seconds_per_query"
            ],
            "median_latency_seconds_per_query": timing[
                "median_latency_seconds_per_query"
            ],
            "p95_latency_seconds_per_query": timing[
                "p95_latency_seconds_per_query"
            ],
            "quality_metrics": result["quality_metrics"],
        }

    same_device = (
        crossencoder["configuration"]["device"]
        == flashrank["configuration"]["device"]
    )
    same_backend = (
        crossencoder["configuration"]["backend"]
        == flashrank["configuration"]["backend"]
    )

    summary = {
        "schema_version": 2,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "comparison_scope": (
            "Two complete reranker configurations with different underlying "
            "models, evaluated on identical saved candidate pools."
        ),
        "top_k": TOP_K,
        "limit": limit,
        "input_validation": crossencoder["validation"],
        "configurations": {
            "crossencoder": crossencoder["configuration"],
            "flashrank": flashrank["configuration"],
        },
        "configuration_summary": compact_configurations,
        "execution_environments": {
            "crossencoder": crossencoder["environment"],
            "flashrank": flashrank["environment"],
        },
        "quality_metrics": {
            "crossencoder": crossencoder["quality_metrics"],
            "flashrank": flashrank["quality_metrics"],
        },
        "quality_metric_query_counts": {
            "crossencoder": crossencoder["quality_metric_query_counts"],
            "flashrank": flashrank["quality_metric_query_counts"],
        },
        "latency_metrics": {
            "crossencoder": crossencoder["timing"],
            "flashrank": flashrank["timing"],
        },
        "quality_retention_flashrank_over_crossencoder": quality_retention,
        "latency_tradeoff": {
            "mean_latency_reduction_seconds_per_query": mean_reduction,
            "mean_latency_reduction_percent": (
                mean_reduction / cross_mean * 100 if cross_mean else None
            ),
            "crossencoder_over_flashrank_mean_latency_ratio": safe_ratio(
                cross_mean, flash_mean
            ),
        },
        "latency_comparability": {
            "same_device": same_device,
            "same_backend": same_backend,
            "hardware_equivalent_benchmark": same_device and same_backend,
            "note": (
                "Latency is reported with each reranker's actual execution "
                "environment. Do not interpret it as hardware-equivalent when "
                "the device or backend differs."
            ),
        },
        "quality_comparability": {
            "direct_comparison_valid": True,
            "note": (
                "Both rerankers were validated against identical queries, "
                "candidate IDs, candidate ordering, and candidate fingerprints."
            ),
        },
        "limitations": [
            (
                "Expected-document matching is a proxy relevance label and is "
                "not human-labelled chunk relevance. Questions without expected "
                "document labels are excluded from document-based metrics."
            ),
            (
                "Precision@4 and binary nDCG@4 inherit the same document-level "
                "proxy limitation and may reward multiple chunks from one document."
            ),
            (
                "Evidence Coverage@4 uses normalized exact containment overlap; "
                "it does not measure semantic equivalence. Questions without "
                "evidence passages are excluded."
            ),
            (
                "The comparison attributes results to the complete model plus "
                "implementation configuration, not solely to either framework."
            ),
            (
                "Rerankers cannot recover relevant evidence that is absent from "
                "the saved retrieval candidate pool."
            ),
        ],
    }

    destination = summary_path(limit)
    save_json(destination, summary)
    print(f"Saved {destination.relative_to(REPO_ROOT)}", flush=True)
    return destination


def run_isolated_workers(limit: int | None) -> None:
    for reranker_name in ("crossencoder", "flashrank"):
        command = [
            sys.executable,
            str(Path(__file__).resolve()),
            "--reranker",
            reranker_name,
            "--worker",
        ]
        if limit is not None:
            command.extend(["--limit", str(limit)])
        print(f"Starting isolated {reranker_name} process...", flush=True)
        subprocess.run(command, cwd=REPO_ROOT, check=True)
    create_summary(limit)


def main() -> None:
    args = parse_args()
    rows, validation = validate_and_prepare(args.limit)
    print(
        "Validated inputs: "
        f"rows={validation['selected_rows']}, "
        f"candidates={validation['selected_candidates']}, "
        f"top_k={TOP_K}, "
        f"flashrank_model={configured_flashrank_model()}",
        flush=True,
    )
    del rows

    if args.reranker in ("crossencoder", "both"):
        device, device_details = crossencoder_device(args.limit)
        print(
            "CrossEncoder execution policy: "
            f"device={device}, cuda_available={device_details['cuda_available']}, "
            "cpu_fallback_for_smoke_test="
            f"{device_details['cpu_fallback_for_smoke_test']}",
            flush=True,
        )

    if args.reranker == "both":
        if args.worker:
            raise ValueError("Internal worker mode requires one reranker.")
        run_isolated_workers(args.limit)
        return

    run_reranker(args.reranker, args.limit)

    if args.worker:
        return

    counterpart = "flashrank" if args.reranker == "crossencoder" else "crossencoder"
    if ranking_path(counterpart, args.limit).exists():
        create_summary(args.limit)


if __name__ == "__main__":
    main()
