import json
import os

from app.models.model_manager import ModelManager

from app.retrieval.chroma_manager import ChromaManager
from app.retrieval.bm25_manager import BM25Manager


# ==========================================================
# CONFIG
# ==========================================================

QUESTION_PATH = (
    r"D:\legal-technology-agentic-rag\data\data_test\data_test.json"
)

OUTPUT_PATH = (
    r"D:\legal-technology-agentic-rag\benchmark\reranker\results\retrieval_results.json"
)

RETRIEVAL_TOP_K = 5


# ==========================================================
# LOAD QUESTION
# ==========================================================

def load_questions():

    with open(
        QUESTION_PATH,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)


# ==========================================================
# HYBRID RETRIEVAL
# ==========================================================

def hybrid_retrieve(
    query,
    chroma,
    bm25,
):

    # -----------------------------
    # Dense Retrieval
    # -----------------------------

    dense_docs = chroma.similarity_search(
        query=query,
        k=RETRIEVAL_TOP_K,
    )

    # -----------------------------
    # Sparse Retrieval
    # -----------------------------

    sparse_docs = bm25.search(query)

    sparse_docs = sparse_docs[:RETRIEVAL_TOP_K]

    return dense_docs, sparse_docs

# ==========================================================
# INTERLEAVE + REMOVE DUPLICATE
# ==========================================================

def build_candidates(
    dense_docs,
    sparse_docs,
):

    candidates = []

    seen = set()

    max_len = max(
        len(dense_docs),
        len(sparse_docs),
    )

    for i in range(max_len):

        # -----------------------------
        # Dense
        # -----------------------------

        if i < len(dense_docs):

            doc = dense_docs[i]

            key = doc.page_content

            if key not in seen:

                seen.add(key)

                candidates.append({

                    "content": doc.page_content,

                    "metadata": doc.metadata,

                    "source": ["dense"],

                })

        # -----------------------------
        # BM25
        # -----------------------------

        if i < len(sparse_docs):

            doc = sparse_docs[i]

            key = doc.page_content

            if key not in seen:

                seen.add(key)

                candidates.append({

                    "content": doc.page_content,

                    "metadata": doc.metadata,

                    "source": ["bm25"],

                })

            else:

                # Nếu chunk đã có từ Dense
                # thì bổ sung nguồn BM25

                for candidate in candidates:

                    if candidate["content"] == key:

                        if "bm25" not in candidate["source"]:

                            candidate["source"].append("bm25")

                        break

    return candidates
# ==========================================================
# MAIN
# ==========================================================

def main():

    print("=" * 80)
    print("HYBRID RETRIEVAL")
    print("=" * 80)

    # -----------------------------------------------------
    # Load models
    # -----------------------------------------------------

    model_manager = ModelManager()

    model_manager.load_models()

    # -----------------------------------------------------
    # Dense Retriever
    # -----------------------------------------------------

    chroma = ChromaManager(
        model_manager=model_manager,
    )

    # -----------------------------------------------------
    # Sparse Retriever
    # -----------------------------------------------------

    bm25 = BM25Manager()

    bm25.load()

    # -----------------------------------------------------
    # Questions
    # -----------------------------------------------------

    questions = load_questions()

    print(
        f"Total Questions : {len(questions)}"
    )

    retrieval_results = []

    # -----------------------------------------------------
    # Retrieve
    # -----------------------------------------------------

    for idx, question in enumerate(
        questions,
        start=1,
    ):

        print(
            f"[{idx}/{len(questions)}]"
        )

        dense_docs, sparse_docs = hybrid_retrieve(
            query=question["question"],
            chroma=chroma,
            bm25=bm25,
        )

        # dense_contexts = []

        # for rank, doc in enumerate(
        #     dense_docs,
        #     start=1,
        # ):

        #     dense_contexts.append({

        #         "rank": rank,

        #         "content": doc.page_content,

        #         "metadata": doc.metadata,

        #     })

        # bm25_contexts = []

        # for rank, doc in enumerate(
        #     sparse_docs,
        #     start=1,
        # ):

        #     bm25_contexts.append({

        #         "rank": rank,

        #         "content": doc.page_content,

        #         "metadata": doc.metadata,

        #     })

        # retrieval_results.append({

        #     "id": question["id"],

        #     "question": question["question"],

        #     "ground_truth": question["ground_truth"],

        #     "evidence": question["evidence"],

        #     "dense_contexts": dense_contexts,

        #     "bm25_contexts": bm25_contexts,

        # })
        candidates = build_candidates(
                dense_docs,
                sparse_docs,
            )

        retrieval_results.append({

                "id": question["id"],

                "question": question["question"],

                "ground_truth": question["ground_truth"],

                "evidence": question["evidence"],

                "candidates": candidates,

            })

    # -----------------------------------------------------
    # Save
    # -----------------------------------------------------

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
            retrieval_results,
            f,
            indent=4,
            ensure_ascii=False,
        )

    print()
    print("=" * 80)
    print("DONE")
    print("=" * 80)
    print(f"Saved to:\n{OUTPUT_PATH}")


if __name__ == "__main__":
    main()