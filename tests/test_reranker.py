from app.config import settings

from app.models.model_manager import ModelManager

from app.retrieval.bm25_manager import BM25Manager
from app.retrieval.reranker import Reranker


def main():

    print("=" * 80)
    print("TEST RERANKER")
    print("=" * 80)

    model_manager = ModelManager()
    model_manager.load_models()

    bm25 = BM25Manager()
    bm25.load()

    reranker = Reranker(model_manager)

    while True:

        query = input("\nQuery (exit để thoát): ").strip()

        if query.lower() == "exit":
            break

        # -----------------------------------------------------
        # BM25 Search
        # -----------------------------------------------------

        documents = bm25.search(query)

        print("\n" + "=" * 80)
        print("BM25 TOP K")
        print("=" * 80)

        for i, doc in enumerate(documents, start=1):

            print(f"\n[{i}]")

            print(
                f"BM25 Score : "
                f"{doc.metadata.get('bm25_score', 0):.4f}"
            )

            print(
                f"Tài liệu   : "
                f"{doc.metadata.get('document')}"
            )

            print(doc.page_content[:120].replace("\n", " "))

        # -----------------------------------------------------
        # Rerank
        # -----------------------------------------------------

        reranked = reranker.rerank(
            query=query,
            documents=documents,
        )

        print("\n" + "=" * 80)
        print("RERANK TOP K")
        print("=" * 80)

        for i, doc in enumerate(reranked, start=1):

            print(f"\n[{i}]")

            print(
                f"Rerank Score : "
                f"{doc.metadata.get('rerank_score', 0):.4f}"
            )

            print(
                f"Tài liệu     : "
                f"{doc.metadata.get('document')}"
            )

            print(doc.page_content[:120].replace("\n", " "))


if __name__ == "__main__":
    main()