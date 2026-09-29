from app.ingestion.pdf_loader import load_pdfs
from app.ingestion.structure_detector import StructureDetector
from app.ingestion.structure_aware_chunker import StructureAwareChunker

from app.models.model_manager import ModelManager
from app.retrieveal.chroma_manager import ChromaManager


DATA_PATH = "data/documents"


def main():

    print("=" * 80)
    print("TEST CHROMA DB")
    print("=" * 80)

    # =========================================================
    # 1. Load PDFs
    # =========================================================

    print("\n[1] LOAD PDF")

    documents = load_pdfs(DATA_PATH)

    print(
        f"✓ Tổng số page: {len(documents)}"
    )

    # =========================================================
    # 2. Detect structure
    # =========================================================

    print("\n[2] STRUCTURE DETECTION")

    detector = StructureDetector()

    structure_nodes = detector.detect(
        documents
    )

    print(
        f"✓ Tổng số structure node: "
        f"{len(structure_nodes)}"
    )

    # =========================================================
    # 3. Structure-aware chunking
    # =========================================================

    print("\n[3] STRUCTURE-AWARE CHUNKING")

    chunker = StructureAwareChunker()

    chunks = chunker.chunk(
        documents=documents,
        structure_nodes=structure_nodes,
    )
    print("\n" + "=" * 80)
    print("CHECK CHUNK METADATA")
    print("=" * 80)

    # =========================================================
    # 1. Kiểm tra một chunk của tài liệu NUMBERED
    # =========================================================

    numbered_chunk = None

    for chunk in chunks:
        if chunk.metadata.get("document_type") == "numbered":
            numbered_chunk = chunk
            break


    if numbered_chunk:
        print("\n" + "-" * 80)
        print("TÀI LIỆU NUMBERED")
        print("-" * 80)

        print(
            f"Tài liệu       : "
            f"{numbered_chunk.metadata.get('document')}"
        )

        print(
            f"Loại tài liệu  : "
            f"{numbered_chunk.metadata.get('document_type')}"
        )

        print(
            f"Cấp 1          : "
            f"{numbered_chunk.metadata.get('level_1')}"
        )

        print(
            f"Cấp 2          : "
            f"{numbered_chunk.metadata.get('level_2')}"
        )

        print(
            f"Cấp 3          : "
            f"{numbered_chunk.metadata.get('level_3')}"
        )

        print(
            f"Trang bắt đầu  : "
            f"{numbered_chunk.metadata.get('page_start')}"
        )

        print(
            f"Trang kết thúc : "
            f"{numbered_chunk.metadata.get('page_end')}"
        )

        print(
            f"Chunk index    : "
            f"{numbered_chunk.metadata.get('chunk_index')}"
        )

        print(
            f"Chunk count    : "
            f"{numbered_chunk.metadata.get('chunk_count')}"
        )

        print(
            f"Chunk size     : "
            f"{numbered_chunk.metadata.get('chunk_size')}"
        )

        print(
            f"Unit size      : "
            f"{numbered_chunk.metadata.get('unit_size')}"
        )

        print(
            f"\nContent:\n"
            f"{numbered_chunk.page_content[:500]}"
        )


    # =========================================================
    # 2. Kiểm tra một chunk của tài liệu LEGAL
    # =========================================================

    legal_chunk = None

    for chunk in chunks:
        if chunk.metadata.get("document_type") == "legal":
            legal_chunk = chunk
            break


    if legal_chunk:
        print("\n" + "-" * 80)
        print("TÀI LIỆU FORMAT PHÁP LUẬT")
        print("-" * 80)

        print(
            f"Tài liệu       : "
            f"{legal_chunk.metadata.get('document')}"
        )

        print(
            f"Loại tài liệu  : "
            f"{legal_chunk.metadata.get('document_type')}"
        )

        print(
            f"Chương         : "
            f"{legal_chunk.metadata.get('chapter')}"
        )

        print(
            f"Điều           : "
            f"{legal_chunk.metadata.get('article')}"
        )

        print(
            f"Trang bắt đầu  : "
            f"{legal_chunk.metadata.get('page_start')}"
        )

        print(
            f"Trang kết thúc : "
            f"{legal_chunk.metadata.get('page_end')}"
        )

        print(
            f"Chunk index    : "
            f"{legal_chunk.metadata.get('chunk_index')}"
        )

        print(
            f"Chunk count    : "
            f"{legal_chunk.metadata.get('chunk_count')}"
        )

        print(
            f"Chunk size     : "
            f"{legal_chunk.metadata.get('chunk_size')}"
        )

        print(
            f"Unit size      : "
            f"{legal_chunk.metadata.get('unit_size')}"
        )

        print(
            f"\nContent:\n"
            f"{legal_chunk.page_content[:500]}")
    print(
        f"✓ Tổng số chunk: {len(chunks)}"
    )

    # =========================================================
    # 4. Load ModelManager
    # =========================================================

    print("\n[4] MODEL MANAGER")

    model_manager = ModelManager()

    model_manager.load_models()

    print("✓ Models loaded.")

    # =========================================================
    # 5. Create ChromaManager
    # =========================================================

    print("\n[5] CHROMA DB")

    chroma = ChromaManager(
        model_manager=model_manager
    )

    # =========================================================
    # 6. Reset collection
    # =========================================================

    print("\nReset ChromaDB...")

    chroma.reset()

    print("✓ Collection reset.")

    # =========================================================
    # 7. Add chunks
    # =========================================================

    print("\n[6] INDEXING")

    print(
        f"Đang thêm {len(chunks)} chunks..."
    )

    chroma.add_documents(
        chunks
    )

    total = chroma.count()

    print(
        f"✓ ChromaDB hiện có: {total} chunks"
    )

    # =========================================================
    # 8. Validate số lượng
    # =========================================================

    print("\n[7] VALIDATION")

    if total != len(chunks):
        raise RuntimeError(
            f"Số chunk không khớp: "
            f"expected={len(chunks)}, "
            f"actual={total}"
        )

    print(
        "✓ Số lượng chunk khớp."
    )

    # =========================================================
    # 9. Test Dense Retrieval
    # =========================================================

    print("\n[8] DENSE RETRIEVAL")

    query = "Dữ liệu cá nhân là gì?"

    print(
        f"Query: {query}"
    )

    results = chroma.similarity_search(
        query
    )

    print(
        f"\n✓ Retrieved: "
        f"{len(results)} chunks"
    )

    # =========================================================
    # 10. Display results
    # =========================================================

    print("\n[9] TOP RESULTS")

    for index, document in enumerate(
        results,
        start=1,
    ):

        print("\n" + "-" * 80)

        print(
            f"Rank       : {index}"
        )

        print(
            f"Tài liệu   : "
            f"{document.metadata.get('document')}"
        )

        print(
            f"Trang      : "
            f"{document.metadata.get('page')}"
        )

        print(
            f"Cấu trúc   : "
            f"{document.metadata.get('structure')}"
        )

        print(
            f"Level      : "
            f"{document.metadata.get('level')}"
        )

        print(
            f"Content    : "
            f"{document.page_content[:500]}"
        )

    # =========================================================
    # 11. Test similarity search with score
    # =========================================================

    print("\n" + "=" * 80)
    print("[10] SIMILARITY SEARCH WITH SCORE")
    print("=" * 80)

    scored_results = (
        chroma.similarity_search_with_score(
            query
        )
    )

    for index, (document, score) in enumerate(
        scored_results,
        start=1,
    ):

        print("\n" + "-" * 80)

        print(
            f"Rank       : {index}"
        )

        print(
            f"Score      : {score:.4f}"
        )

        print(
            f"Tài liệu   : "
            f"{document.metadata.get('document')}"
        )

        print(
            f"Trang      : "
            f"{document.metadata.get('page')}"
        )

        print(
            f"Content    : "
            f"{document.page_content[:300]}"
        )

    # =========================================================
    # 12. Final
    # =========================================================

    print("\n" + "=" * 80)
    print("CHROMA DB TEST PASSED")
    print("=" * 80)


if __name__ == "__main__":
    main()
