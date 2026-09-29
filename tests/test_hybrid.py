from app.models.model_manager import ModelManager

from app.retrieval.bm25_manager import BM25Manager
from app.retrieval.chroma_manager import ChromaManager
from app.retrieval.reranker import Reranker
from app.retrieval.hybrid_retriever import HybridRetriever


def print_docs(title, documents, score_key=None):

    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)

    print(f"Tổng số document: {len(documents)}\n")

    for i, doc in enumerate(documents, start=1):

        print(f"[{i}]")

        if score_key is not None:
            score = doc.metadata.get(score_key)

            if score is not None:
                print(f"{score_key}: {score:.4f}")

        print(f"Tài liệu : {doc.metadata.get('document')}")

        if doc.metadata.get("document_type") == "legal":
            print(f"Chương   : {doc.metadata.get('chapter')}")
            print(f"Điều     : {doc.metadata.get('article')}")

        else:
            print(f"Level 1  : {doc.metadata.get('level_1')}")

        print(
            doc.page_content[:120]
            .replace("\n", " ")
        )

        print()


def main():

    model_manager = ModelManager()
    model_manager.load_models()

    chroma = ChromaManager(model_manager)

    bm25 = BM25Manager()
    bm25.load()

    reranker = Reranker(model_manager)

    hybrid = HybridRetriever(
        chroma_manager=chroma,
        bm25_manager=bm25,
        reranker=reranker,
    )

    while True:

        query = input("\nQuery (exit để thoát): ").strip()

        if query.lower() == "exit":
            break

        # --------------------------------------------------
        # Dense
        # --------------------------------------------------

        dense = chroma.similarity_search(query)

        print_docs(
            "DENSE SEARCH",
            dense,
        )

        # --------------------------------------------------
        # Sparse
        # --------------------------------------------------

        sparse = bm25.search(query)

        print_docs(
            "SPARSE SEARCH",
            sparse,
            score_key="bm25_score",
        )

        # --------------------------------------------------
        # Hybrid
        # --------------------------------------------------

        documents = hybrid.retrieve(query)

        print_docs(
            "HYBRID RESULT (AFTER RERANK)",
            documents,
            score_key="rerank_score",
        )


if __name__ == "__main__":
    main()