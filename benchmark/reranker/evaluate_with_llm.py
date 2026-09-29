import json
import time
from pathlib import Path

from benchmark.llm_judge.judge import get_judge
from benchmark.llm_judge.prompt import build_prompt
from benchmark.llm_judge.utils import call_judge


# ============================
# CONFIG
# ============================

DATA_PATH = Path(r"D:\legal-technology-agentic-rag\benchmark\reranker\results\answer_benchmark_reranker.json")

RESULT_PATH = Path(r"D:\legal-technology-agentic-rag\benchmark\reranker\results\llm_evaluation.json")

PROGRESS_PATH = Path(r"D:\legal-technology-agentic-rag\benchmark\reranker\results\progress.json")

# Số câu muốn chạy trong lần này
NUM_QUESTIONS = 10

# Bao nhiêu câu thì lưu kết quả
SAVE_EVERY = 1


# ============================
# LOAD / SAVE
# ============================

def load_benchmark():

    with open(
        DATA_PATH,
        "r",
        encoding="utf-8",
    ) as f:

        return json.load(f)


def load_progress():

    if not PROGRESS_PATH.exists():

        return 0

    with open(
        PROGRESS_PATH,
        "r",
        encoding="utf-8",
    ) as f:

        progress = json.load(f)

    return progress["completed"]


def save_progress(
    completed,
    total,
):

    progress = {

        "completed": completed,

        "next_question": completed + 1,

        "total": total,

        "status": (
            "completed"
            if completed == total
            else "running"
        )

    }

    with open(
        PROGRESS_PATH,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            progress,
            f,
            ensure_ascii=False,
            indent=4,
        )


def save_result(results):

    with open(
        RESULT_PATH,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            results,
            f,
            ensure_ascii=False,
            indent=4,
        )


# ============================
# EVALUATE ONE QUESTION
# ============================

def evaluate_question(
    llm,
    sample,
):

    start = time.time()

    no_rerank_prompt = build_prompt(

        question=sample["question"],

        ground_truth=sample["ground_truth"],

        retrieved_contexts=[
            ctx["content"]
            for ctx in sample["no_rerank"]["contexts"]
        ],

        answer=sample["no_rerank"]["answer"],

    )

    no_rerank_result = call_judge(
        llm,
        no_rerank_prompt,
    )


    rerank_prompt = build_prompt(

        question=sample["question"],

        ground_truth=sample["ground_truth"],

        retrieved_contexts=[
            ctx["content"]
            for ctx in sample["rerank"]["contexts"]
        ],

        answer=sample["rerank"]["answer"],

    )

    rerank_result = call_judge(
        llm,
        rerank_prompt,
    )


    latency = round(
        time.time() - start,
        2,
    )


    return {

        "id": sample["id"],

        "question": sample["question"],

        "no_rerank": no_rerank_result,

        "rerank": rerank_result,

        "latency_seconds": latency,

    }


# ============================
# MAIN
# ============================

def main():

    dataset = load_benchmark()

    total = len(dataset)

    completed = load_progress()
    end_idx = min(
        completed + NUM_QUESTIONS,
        total,
    )

    results = []

    if RESULT_PATH.exists():

        with open(
            RESULT_PATH,
            "r",
            encoding="utf-8",
        ) as f:

            results = json.load(f)

    print("=" * 80)
    print("LLM JUDGE BENCHMARK")
    print("=" * 80)

    print(f"Total questions: {total}")

    print(f"Resume from: {completed + 1}")

    print("Loading Gemini Judge...")

    llm = get_judge()

    print("Gemini loaded.\n")


    for idx in range(
        completed,
        end_idx,
    ):

        sample = dataset[idx]

        print("=" * 80)

        print(
            f"Running question {idx+1}/{total}"
        )

        print(
            f"Question ID: {sample['id']}"
        )

        print(sample["question"])

        print("=" * 80)

        result = evaluate_question(
            llm,
            sample,
        )

        results.append(result)

        processed = idx - completed + 1

        if (
            processed % SAVE_EVERY == 0
            or idx + 1 == end_idx
        ):

            save_result(results)

            save_progress(
                idx + 1,
                total,
            )

            print()

            print("Progress saved.")

            print()


    print("=" * 80)

    print("Benchmark completed.")

    print("=" * 80)


if __name__ == "__main__":

    main()