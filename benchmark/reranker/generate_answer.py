import json
import os
import time

from time import perf_counter

from langchain_core.documents import Document

from app.config import settings
from app.models.model_manager import ModelManager
from app.retrieval.reranker import Reranker


# ==========================================================
# CONFIG
# ==========================================================

INPUT_PATH = (
    r"D:\legal-technology-agentic-rag\benchmark\reranker\results\retrieval_results.json"
)

OUTPUT_PATH = (
    r"D:\legal-technology-agentic-rag\benchmark\reranker\results\answer_benchmark_reranker.json"
)
PROGRESS_PATH = (
    r"D:\legal-technology-agentic-rag\benchmark\reranker\results\answer_progress.json"
)
BATCH_SIZE = 5

SLEEP_SECONDS = 12


# ==========================================================
# LOAD DATA
# ==========================================================

def load_retrieval_results():

    with open(
        INPUT_PATH,
        "r",
        encoding="utf-8",
    ) as f:

        return json.load(f)


# ==========================================================
# LOAD PREVIOUS RESULT
# ==========================================================

def load_answer_results():

    if not os.path.exists(OUTPUT_PATH):
        return []

    with open(
        OUTPUT_PATH,
        "r",
        encoding="utf-8",
    ) as f:

        return json.load(f)


# ==========================================================
# SAVE
# ==========================================================

def save_results(results):

    os.makedirs(
        os.path.dirname(OUTPUT_PATH),
        exist_ok=True,
    )

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            results,
            f,
            indent=4,
            ensure_ascii=False,
        )


# ==========================================================
# RESUME
# ==========================================================

def get_start_index(results):

    return len(results)


# ==========================================================
# PROMPT
# ==========================================================

PROMPT_TEMPLATE = """
Bạn là trợ lý pháp lý.

Chỉ sử dụng thông tin trong Context để trả lời.

Không sử dụng kiến thức bên ngoài.

Nếu Context không đủ thông tin hãy trả lời:

"Không có đủ thông tin trong các tài liệu được cung cấp để trả lời câu hỏi này. Tôi không thể kết luận ngoài phạm vi của cơ sở tri thức hiện tại."

==========================
Question

{question}

==========================
Context

{contexts}

==========================

Hãy trả lời bằng tiếng Việt.
"""


# ==========================================================
# BUILD CONTEXT
# ==========================================================

def build_context(contexts):

    parts = []

    for idx, item in enumerate(
        contexts,
        start=1,
    ):

        parts.append(

            f"""[Context {idx}]

{item["content"]}

--------------------------------------------------
"""

        )

    return "\n".join(parts)


# ==========================================================
# BUILD PROMPT
# ==========================================================

def build_prompt(
    question,
    contexts,
):

    return PROMPT_TEMPLATE.format(

        question=question,

        contexts=build_context(
            contexts,
        ),
    )


# ==========================================================
# LOAD MODELS
# ==========================================================

model_manager = ModelManager()

model_manager.load_models()

llm = model_manager.get_llm()

reranker = Reranker(
    model_manager,
)

# ==========================================================
# CREATE DOCUMENTS
# ==========================================================

def create_documents(candidates):

    documents = []

    for item in candidates:

        documents.append(

            Document(

                page_content=item["content"],

                metadata=item["metadata"],

            )

        )

    return documents


# ==========================================================
# GENERATE ANSWER
# ==========================================================

def generate_answer(

    question,
    contexts,

):

    prompt = build_prompt(

        question,

        contexts,

    )

    start = perf_counter()

    response = llm.invoke(prompt)

    generation_time = (

        perf_counter()

        - start

    )

    return (

        response.content,

        generation_time,

    )


# ==========================================================
# NO RERANK
# ==========================================================

def run_no_rerank(

    question_item,

):

    total_start = perf_counter()

    selected_contexts = (

        question_item["candidates"][:4]

    )

    answer, generation_time = (

        generate_answer(

            question_item["question"],

            selected_contexts,

        )

    )

    total_time = (

        perf_counter()

        - total_start

    )

    return {

        "contexts": selected_contexts,

        "answer": answer,

        "generation_time": generation_time,

        "total_time": total_time,

    }


# ==========================================================
# RERANK
# ==========================================================

def run_rerank(

    question_item,

):

    total_start = perf_counter()

    documents = create_documents(

        question_item["candidates"]

    )

    rerank_start = perf_counter()

    reranked_documents = (

        reranker.rerank(

            query=question_item["question"],

            documents=documents,

        )

    )

    rerank_time = (

        perf_counter()

        - rerank_start

    )

    selected_contexts = []

    for doc in reranked_documents:

        selected_contexts.append(

            {

                "content": doc.page_content,

                "metadata": doc.metadata,

            }

        )

    answer, generation_time = (

        generate_answer(

            question_item["question"],

            selected_contexts,

        )

    )

    total_time = (

        perf_counter()

        - total_start

    )

    return {

        "contexts": selected_contexts,

        "answer": answer,

        "rerank_time": rerank_time,

        "generation_time": generation_time,

        "total_time": total_time,

    }

# ==========================================================
# PROGRESS
# ==========================================================

def load_progress(total_questions):

    if not os.path.exists(PROGRESS_PATH):

        return {

            "completed": 0,

            "next_question": 1,

            "total": total_questions,

            "status": "running",

        }

    with open(

        PROGRESS_PATH,

        "r",

        encoding="utf-8",

    ) as f:

        return json.load(f)

def save_progress(progress):

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


# ==========================================================
# MAIN
# ==========================================================

def main():

    print("=" * 80)
    print("ANSWER BENCHMARK")
    print("=" * 80)

    retrieval_results = load_retrieval_results()

    answer_results = load_answer_results()

    progress = load_progress(
        len(retrieval_results)
    )

    start_index = progress["completed"]

    print()

    print(
        f"Resume from question {progress['next_question']}"
    )

    print(
        f"Completed : {progress['completed']}/{progress['total']}"
    )

    processed = 0

    for idx in range(

        start_index,

        len(retrieval_results),

    ):

        if processed >= BATCH_SIZE:

            break

        question = retrieval_results[idx]

        print()

        print("=" * 80)

        print(

            f"[{idx+1}/{len(retrieval_results)}]"

        )

        print(

            question["question"]

        )

        print("=" * 80)

        try:

            # ------------------------------------
            # No rerank
            # ------------------------------------

            print("No Rerank...")

            no_rerank = run_no_rerank(
                question
            )

            print(

                f"Generation : {no_rerank['generation_time']:.2f}s"

            )

            time.sleep(
                SLEEP_SECONDS
            )

            # ------------------------------------
            # Rerank
            # ------------------------------------

            print("Rerank...")

            rerank = run_rerank(
                question
            )

            print(

                f"Rerank : {rerank['rerank_time']:.2f}s"

            )

            print(

                f"Generation : {rerank['generation_time']:.2f}s"

            )

            time.sleep(
                SLEEP_SECONDS
            )

            # ------------------------------------
            # Save answer
            # ------------------------------------

            answer_results.append(

                {

                    "id": question["id"],

                    "question": question["question"],

                    "ground_truth": question["ground_truth"],

                    "evidence": question["evidence"],

                    "no_rerank": no_rerank,

                    "rerank": rerank,

                }

            )

            save_results(
                answer_results
            )

            # ------------------------------------
            # Update progress
            # ------------------------------------

            progress["completed"] += 1

            progress["next_question"] = (

                progress["completed"] + 1

            )

            if (

                progress["completed"]

                ==

                progress["total"]

            ):

                progress["status"] = "completed"

            save_progress(
                progress
            )

            processed += 1

            print()

            print(

                f"Completed : {progress['completed']}/{progress['total']}"

            )

        except Exception as e:

            print()

            print("ERROR")

            print(e)

            save_results(
                answer_results
            )

            save_progress(
                progress
            )

            break

    print()

    print("=" * 80)

    print("BATCH FINISHED")

    print("=" * 80)

    print(

        f"Processed : {processed}"

    )

    print(

        f"Next Question : {progress['next_question']}"

    )

    print(

        f"Status : {progress['status']}"

    )


if __name__ == "__main__":

    main()