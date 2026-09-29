from app.config import settings

from app.ingestion.pdf_loader import load_pdfs
from app.ingestion.structure_detector import StructureDetector
from app.ingestion.structure_aware_chunker import StructureAwareChunker

from app.models.model_manager import ModelManager
from app.retrieval.chroma_manager import ChromaManager


def main():

    print("=" * 80)
    print("BUILD CHROMA VECTOR STORE")
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
    # 4. Load models
    # =========================================================

    print("\n[4] LOAD MODELS")

    model_manager = ModelManager()

    model_manager.load_models()

    print("✓ Models loaded.")

    # =========================================================
    # 5. Create ChromaDB
    # =========================================================

    print("\n[5] CREATE CHROMA DB")

    chroma = ChromaManager(
        model_manager=model_manager
    )

    # =========================================================
    # 6. Reset existing collection
    # =========================================================

    print("\n[6] RESET COLLECTION")

    chroma.reset()

    print("✓ Collection reset.")

    # =========================================================
    # 7. Index chunks
    # =========================================================

    print("\n[7] INDEXING")

    print(
        f"Đang index {len(chunks)} chunks..."
    )

    chroma.add_documents(chunks)

    total = chroma.count()

    print(
        f"✓ ChromaDB chứa {total} chunks"
    )

    # =========================================================
    # 8. Validation
    # =========================================================

    print("\n[8] VALIDATION")

    if total != len(chunks):
        raise RuntimeError(
            f"Chunk count mismatch: "
            f"expected={len(chunks)}, "
            f"actual={total}"
        )

    print("✓ Chunk count khớp.")

    print("\n" + "=" * 80)
    print("BUILD CHROMA DB COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()