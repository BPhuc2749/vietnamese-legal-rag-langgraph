from typing import List

from langchain_core.documents import Document
from langchain_chroma import Chroma

from app.config import settings
from app.models.model_manager import ModelManager

class ChromaManager:
    """
    Quản lý ChromaDB cho Dense Retrieval.

    Responsibilities:
    - Khởi tạo / load ChromaDB
    - Thêm chunks vào ChromaDB
    - Dense similarity search
    - Kiểm tra số lượng chunks
    - Reset collection khi cần rebuild
    """

    def __init__(
        self,
        model_manager: ModelManager,
    ):
        self.model_manager = model_manager

        self.embedding_model = (
            self.model_manager.get_embedding_model()
        )

        self.persist_directory = (
            f"{settings.vector_store_path}/chroma"
        )

        self.collection_name = "legal_documents"

        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embedding_model,
            persist_directory=self.persist_directory,
        )

    def add_documents(
        self,
        documents: List[Document],
    ) -> None:
        """
        Thêm chunks vào ChromaDB.
        """

        if not documents:
            return

        self.vectorstore.add_documents(
            documents
        )

    def similarity_search(
        self,
        query: str,
        k: int | None = None,
    ) -> List[Document]:
        """
        Dense similarity search.

        Nếu k không truyền vào thì sử dụng
        settings.retrieval_top_k.
        """

        if k is None:
            k = settings.retrieval_top_k

        return self.vectorstore.similarity_search(
            query,
            k=k,
        )

    def similarity_search_with_score(
        self,
        query: str,
        k: int | None = None,
    ):
        """
        Dense similarity search kèm score.
        """

        if k is None:
            k = settings.retrieval_top_k

        return (
            self.vectorstore
            .similarity_search_with_score(
                query,
                k=k,
            )
        )

    def count(self) -> int:
        """
        Trả về tổng số chunks trong collection.
        """

        return self.vectorstore._collection.count()

    def reset(self) -> None:
        """
        Xóa toàn bộ collection và tạo lại collection rỗng.
        """

        self.vectorstore.delete_collection()

        self.vectorstore = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embedding_model,
            persist_directory=self.persist_directory,
        )


