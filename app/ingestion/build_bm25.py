from app.config import settings

from app.ingestion.pdf_loader import load_pdfs
from app.ingestion.structure_detector import StructureDetector
from app.ingestion.structure_aware_chunker import StructureAwareChunker

from app.retrieval.bm25_manager import BM25Manager


def main():

    print("=" * 80)
    print("BUILD BM25")
    print("=" * 80)

    # =========================================================
    # 1. Load PDFs
    # =========================================================

    print("\n[1] LOAD PDF")

    documents = load_pdfs(settings.raw_data_path)

    print(f"✓ Tổng số page: {len(documents)}")

    # =========================================================
    # 2. Detect structure
    # =========================================================

    print("\n[2] STRUCTURE DETECTION")

    detector = StructureDetector()

    structure_nodes = detector.detect(documents)

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

    print(f"✓ Tổng số chunk: {len(chunks)}")

    # =========================================================
    # 4. Build BM25
    # =========================================================

    print("\n[4] BUILD BM25")

    bm25 = BM25Manager()

    bm25.build(chunks)

    bm25.save()

    print("✓ BM25 saved.")

    print("\n" + "=" * 80)
    print("BUILD BM25 COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()