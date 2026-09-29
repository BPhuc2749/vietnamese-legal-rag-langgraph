from app.models.model_manager import ModelManager


def main():
    print("=" * 80)
    print("TEST MODEL MANAGER")
    print("=" * 80)

    # =========================================================
    # 1. Khởi tạo ModelManager
    # =========================================================

    model_manager = ModelManager()

    print("\n[1] Loading models...")

    model_manager.load_models()

    print("✓ Models loaded successfully.")

    # =========================================================
    # 2. Test LLM
    # =========================================================

    print("\n[2] TEST LLM")

    llm = model_manager.get_llm()

    print(f"LLM class: {type(llm).__name__}")
    print("✓ LLM loaded.")

    # Không gọi Gemini để tránh tốn API quota.
    # Chỉ kiểm tra object đã được khởi tạo.

    # =========================================================
    # 3. Test Embedding
    # =========================================================

    print("\n[3] TEST EMBEDDING")

    embedding_model = (
        model_manager.get_embedding_model()
    )

    test_text = "Dữ liệu cá nhân là thông tin gắn liền với một con người cụ thể."

    embedding = embedding_model.embed_query(
        test_text
    )

    print(
        f"Embedding dimension: {len(embedding)}"
    )

    print(
        f"First 5 values: {embedding[:5]}"
    )

    print("✓ Embedding model hoạt động.")

    # =========================================================
    # 4. Test Reranker
    # =========================================================

    print("\n[4] TEST RERANKER")

    reranker = model_manager.get_reranker()

    query = "Dữ liệu cá nhân là gì?"

    documents = [
        "Dữ liệu cá nhân là thông tin gắn liền với một con người cụ thể.",
        "Hệ thống mạng phải đảm bảo an toàn thông tin.",
        "Dữ liệu cá nhân bao gồm dữ liệu cá nhân cơ bản và dữ liệu cá nhân nhạy cảm.",
    ]

    pairs = [
        (query, document)
        for document in documents
    ]

    scores = reranker.predict(pairs)

    print("\nReranker results:")

    for document, score in zip(
        documents,
        scores,
    ):
        print("-" * 60)
        print(f"Score    : {score:.4f}")
        print(f"Document : {document}")

    print("\n✓ Reranker model hoạt động.")

    # =========================================================
    # 5. Tổng kết
    # =========================================================

    print("\n" + "=" * 80)
    print("MODEL MANAGER TEST PASSED")
    print("=" * 80)


if __name__ == "__main__":
    main()

