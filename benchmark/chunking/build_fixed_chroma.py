from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma

from app.config import settings
from app.ingestion.pdf_loader import load_pdfs
from app.models.model_manager import ModelManager


def main():

    print("=" * 80)
    print("BUILD CHROMA VECTOR STORE (FIXED CHUNKING)")
    print("=" * 80)

    # =========================================================
    # 1. Load PDFs
    # =========================================================

    print("\n[1] LOAD PDF")

    documents = load_pdfs(settings.raw_data_path)

    print(f"✓ Tổng số page: {len(documents)}")

    # =========================================================
    # 2. Fixed Chunking
    # =========================================================

    print("\n[2] FIXED CHUNKING")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
    )

    chunks = splitter.split_documents(documents)

    print(f"✓ Tổng số chunk: {len(chunks)}")

    # =========================================================
    # 3. Load Models
    # =========================================================

    print("\n[3] LOAD MODELS")

    model_manager = ModelManager()
    model_manager.load_models()

    embedding_model = model_manager.get_embedding_model()

    print("✓ Models loaded.")

    # =========================================================
    # 4. Create ChromaDB
    # =========================================================

    print("\n[4] CREATE CHROMA DB")

    persist_directory = (
        f"{settings.vector_store_path}/chroma_fixed"
    )

    collection_name = "legal_documents_fixed"

    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embedding_model,
        persist_directory=persist_directory,
    )

    # =========================================================
    # 5. Reset Existing Collection
    # =========================================================

    print("\n[5] RESET COLLECTION")

    vectorstore.delete_collection()

    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=embedding_model,
        persist_directory=persist_directory,
    )

    print("✓ Collection reset.")

    # =========================================================
    # 6. Index Chunks
    # =========================================================

    print("\n[6] INDEXING")

    print(f"Đang index {len(chunks)} chunks...")

    vectorstore.add_documents(chunks)

    total = vectorstore._collection.count()

    print(f"✓ ChromaDB chứa {total} chunks")

    # =========================================================
    # 7. Validation
    # =========================================================

    print("\n[7] VALIDATION")

    if total != len(chunks):
        raise RuntimeError(
            f"Chunk count mismatch: "
            f"expected={len(chunks)}, "
            f"actual={total}"
        )

    print("✓ Chunk count khớp.")

    print("\n" + "=" * 80)
    print("BUILD FIXED CHROMA DB COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main()