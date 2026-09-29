from langchain_core.documents import Document

from app.retrieval.bm25_manager import BM25Manager
from app.retrieval.chroma_manager import ChromaManager
from app.retrieval.reranker import Reranker


class HybridRetriever:

    def __init__(
        self,
        chroma_manager: ChromaManager,
        bm25_manager: BM25Manager,
        reranker: Reranker,
    ):
        self.chroma = chroma_manager
        self.bm25 = bm25_manager
        self.reranker = reranker

    def retrieve(
        self,
        query: str,
    ) -> list[Document]:

        # --------------------------------------------------
        # Dense Retrieval
        # --------------------------------------------------

        dense_documents = self.chroma.similarity_search(query)

        # --------------------------------------------------
        # Sparse Retrieval
        # --------------------------------------------------

        sparse_documents = self.bm25.search(query)

        # --------------------------------------------------
        # Merge
        # --------------------------------------------------

        merged_documents = dense_documents + sparse_documents

        # --------------------------------------------------
        # Deduplicate
        # --------------------------------------------------

        unique_documents = []

        seen = set()

        for document in merged_documents:

            key = document.page_content

            if key in seen:
                continue

            seen.add(key)
            unique_documents.append(document)

        # --------------------------------------------------
        # Rerank
        # --------------------------------------------------

        reranked_documents = self.reranker.rerank(
            query=query,
            documents=unique_documents,
        )

        return reranked_documents
    async def retrieve_async(self, query: str) -> list[Document]:
        """Phiên bản Async giúp chạy song song nhiều query"""
        # 1. Chạy Chroma và BM25 (Thường rất nhanh nên gọi sync cũng được, 
        # hoặc bọc tương tự nếu muốn tối ưu tuyệt đối)
        dense_documents = self.chroma.similarity_search(query)
        sparse_documents = self.bm25.search(query)

        # 2. Merge & Deduplicate
        merged_documents = dense_documents + sparse_documents
        unique_documents = []
        seen = set()
        for doc in merged_documents:
            if doc.page_content not in seen:
                seen.add(doc.page_content)
                unique_documents.append(doc)
        top_candidates = unique_documents[:8]
        # 3. Rerank ASYNC (Đây là chỗ tiết kiệm 17 giây)
        return await self.reranker.rerank_async(query, top_candidates)
    
    
