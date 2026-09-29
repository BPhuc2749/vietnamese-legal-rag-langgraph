from app.config import settings
from app.retrieval.bm25_manager import BM25Manager


def main():

    print("=" * 80)
    print("TEST BM25")
    print("=" * 80)

    bm25 = BM25Manager()

    bm25.load()

    print("✓ BM25 loaded.\n")

    while True:

        query = input("Query (exit để thoát): ").strip()

        if query.lower() == "exit":
            break

        print("\nSearching...\n")

        results = bm25.search(
            query=query,
            top_k=settings.retrieval_top_k,
        )

        print(f"Tìm thấy {len(results)} kết quả\n")

        for rank, doc in enumerate(results, start=1):

            metadata = doc.metadata

            print("=" * 80)

            print(f"Rank           : {rank}")
            print(f"BM25 Score     : {metadata.get('bm25_score', 0):.4f}")

            print(f"Tài liệu       : {metadata.get('document')}")
            print(f"Loại tài liệu  : {metadata.get('document_type')}")

            if metadata.get("document_type") == "legal":

                print(f"Chương         : {metadata.get('chapter')}")
                print(f"Điều           : {metadata.get('article')}")

            else:

                print(f"Cấp 1          : {metadata.get('level_1')}")
                print(f"Cấp 2          : {metadata.get('level_2')}")
                print(f"Cấp 3          : {metadata.get('level_3')}")

            print(f"Trang bắt đầu  : {metadata.get('page_start')}")
            print(f"Trang kết thúc : {metadata.get('page_end')}")

            print(f"Chunk index    : {metadata.get('chunk_index')}")
            print(f"Chunk count    : {metadata.get('chunk_count')}")

            print(f"Chunk size     : {metadata.get('chunk_size')}")
            print(f"Unit size      : {metadata.get('unit_size')}")

            print("\nContent:\n")

            print(doc.page_content[:500])

            if len(doc.page_content) > 500:
                print("...")

            print()

        print()


if __name__ == "__main__":
    main()