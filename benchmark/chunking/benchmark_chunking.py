import json
import os
import time

from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI

from ragas import evaluate
from ragas import EvaluationDataset
from ragas.dataset_schema import SingleTurnSample
from ragas.metrics import (
    context_precision,
    context_recall,
)

from app.config import settings
from app.models.model_manager import ModelManager


# =========================================================
# CONFIG
# =========================================================

FIXED_CHROMA_PATH = (
    r"D:\legal-technology-agentic-rag\vector_store\chroma_fixed"
)

METADATA_CHROMA_PATH = (
    f"{settings.vector_store_path}/chroma"
)

FIXED_COLLECTION_NAME = "legal_documents_fixed"

METADATA_COLLECTION_NAME = "legal_documents"

QUESTION_PATH = (
    r"D:\legal-technology-agentic-rag\data\data_test\data_test.json"
)

RESULT_PATH = (
    r"D:\legal-technology-agentic-rag\benchmark\results\chunking_results.json"
)

PROGRESS_PATH = (
    r"D:\legal-technology-agentic-rag\benchmark\results\chunking_progress.json"
)

TOP_K = settings.retrieval_top_k

DELAY_SECONDS = 12

BATCH_SIZE = 10


# =========================================================
# LOAD QUESTION
# =========================================================

def load_questions():

    with open(
        QUESTION_PATH,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


# =========================================================
# VECTOR STORE
# =========================================================

def load_vectorstore(
    path,
    collection_name,
    embedding_model,
):

    return Chroma(

        collection_name=collection_name,

        persist_directory=path,

        embedding_function=embedding_model,

    )


# =========================================================
# PROGRESS
# =========================================================

def load_progress(total_questions):

    if not os.path.exists(PROGRESS_PATH):

        return {

            "batch_size": BATCH_SIZE,

            "last_completed": 0,

            "next_question": 1,

            "total_questions": total_questions,

            "finished": False,

        }

    with open(
        PROGRESS_PATH,
        "r",
        encoding="utf-8",
    ) as f:

        return json.load(f)


def save_progress(progress):

    os.makedirs(
        os.path.dirname(PROGRESS_PATH),
        exist_ok=True,
    )

    with open(
        PROGRESS_PATH,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            progress,
            f,
            indent=4,
            ensure_ascii=False,
        )


# =========================================================
# RESULT
# =========================================================

def load_results():

    if not os.path.exists(RESULT_PATH):

        return []

    with open(
        RESULT_PATH,
        "r",
        encoding="utf-8",
    ) as f:

        return json.load(f)


def save_results(results):

    os.makedirs(
        os.path.dirname(RESULT_PATH),
        exist_ok=True,
    )

    with open(
        RESULT_PATH,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            results,
            f,
            indent=4,
            ensure_ascii=False,
        )


# =========================================================
# CREATE SAMPLE
# =========================================================

def create_sample(
    question_item,
    retrieved_docs,
):

    contexts = [

        doc.page_content

        for doc in retrieved_docs

    ]

    return SingleTurnSample(

        user_input=
            question_item["question"],

        retrieved_contexts=
            contexts,

        reference_contexts=
            question_item["evidence"],

        reference=
            question_item["ground_truth"],

    )


# =========================================================
# EVALUATE
# =========================================================

def evaluate_one(
    vectorstore,
    question,
    evaluator_llm,
):

    docs = vectorstore.similarity_search(

        question["question"],

        k=TOP_K,

    )

    sample = create_sample(

        question,

        docs,

    )

    dataset = EvaluationDataset(

        samples=[sample]

    )

    result = evaluate(

        dataset,

        metrics=[

            context_precision,

            context_recall,

        ],

        llm=evaluator_llm,

    )

    return {

        "context_precision":

            float(

                result["context_precision"][0]

            ),

        "context_recall":

            float(

                result["context_recall"][0]

            ),

    }

# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 80)
    print("CHUNKING BENCHMARK")
    print("=" * 80)

    # -----------------------------------------------------
    # Load models
    # -----------------------------------------------------

    model_manager = ModelManager()

    model_manager.load_models()

    embedding_model = (
        model_manager.get_embedding_model()
    )

    evaluator_llm = ChatGoogleGenerativeAI(
        model=settings.llm_model,
        google_api_key=settings.google_api_key,
        temperature=0,
    )

    # -----------------------------------------------------
    # Load vector stores
    # -----------------------------------------------------

    fixed_db = load_vectorstore(
        FIXED_CHROMA_PATH,
        FIXED_COLLECTION_NAME,
        embedding_model,
    )

    metadata_db = load_vectorstore(
        METADATA_CHROMA_PATH,
        METADATA_COLLECTION_NAME,
        embedding_model,
    )

    # -----------------------------------------------------
    # Load questions
    # -----------------------------------------------------

    questions = load_questions()

    total_questions = len(questions)

    # -----------------------------------------------------
    # Load progress
    # -----------------------------------------------------

    progress = load_progress(total_questions)

    if progress["finished"]:

        print("\nBenchmark đã hoàn thành toàn bộ.")
        print("Không còn câu hỏi nào để chạy.")

        return

    start = progress["next_question"] - 1

    end = min(

        start + BATCH_SIZE,

        total_questions

    )

    print(
        f"\nChạy câu hỏi "
        f"{start + 1} -> {end}"
    )

    # -----------------------------------------------------
    # Load old results
    # -----------------------------------------------------

    results = load_results()

    # -----------------------------------------------------
    # Benchmark
    # -----------------------------------------------------

    for idx in range(start, end):

        question = questions[idx]

        print()
        print("=" * 60)

        print(

            f"[{idx+1}/{total_questions}] "

            f"{question['question']}"

        )

        # ---------------- Fixed ----------------

        print("\nFixed Chunk ...")

        fixed_score = evaluate_one(

            fixed_db,

            question,

            evaluator_llm,

        )

        print(fixed_score)

        time.sleep(DELAY_SECONDS)

        # ---------------- Metadata ----------------

        print("\nMetadata Chunk ...")

        metadata_score = evaluate_one(

            metadata_db,

            question,

            evaluator_llm,

        )

        print(metadata_score)

        # ---------------- Save result ----------------

        results.append({

            "id":

                question["id"],

            "category":

                question["category"],

            "question":

                question["question"],

            "fixed":

                fixed_score,

            "metadata":

                metadata_score,

        })

        save_results(results)

        # ---------------- Update progress ----------------

        progress["last_completed"] = idx + 1

        progress["next_question"] = idx + 2

        if progress["next_question"] > total_questions:

            progress["finished"] = True

        save_progress(progress)

        print("\nĐã lưu tiến độ.")

        time.sleep(DELAY_SECONDS)

    # -----------------------------------------------------
    # Finish batch
    # -----------------------------------------------------

    print()

    print("=" * 80)

    if progress["finished"]:

        print("Đã benchmark xong toàn bộ dataset.")

    else:

        print(

            f"Hoàn thành batch."

            f"\nLần chạy tiếp sẽ bắt đầu từ câu "

            f"{progress['next_question']}."

        )

    print("=" * 80)


if __name__ == "__main__":

    main()