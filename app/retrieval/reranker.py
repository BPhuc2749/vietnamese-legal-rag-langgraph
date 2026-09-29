import asyncio
from concurrent.futures import ThreadPoolExecutor
from flashrank import RerankRequest
from langchain_core.documents import Document
from app.config import settings
from app.models.model_manager import ModelManager


class Reranker:

    def __init__(
        self,
        model_manager: ModelManager,
    ):
        self.ranker = model_manager.get_reranker()
        self.executor = ThreadPoolExecutor(max_workers=2)

    def rerank(
        self,
        query: str,
        documents: list[Document],
    ) -> list[Document]:

        if len(documents) == 0:
            return []

        # FlashRank nhận danh sách dạng dict: [{"id": 0, "text": "..."}]
        passages = [
            {"id": idx, "text": doc.page_content}
            for idx, doc in enumerate(documents)
        ]

        # Thực hiện Rerank siêu tốc trên CPU bằng ONNX
        rerank_request = RerankRequest(query=query, passages=passages)
        results = self.ranker.rerank(rerank_request)

        reranked_documents = []

        # Lấy top kết quả theo config settings.rerank_top_k
        for item in results[: settings.rerank_top_k]:
            idx = item["id"]
            score = float(item["score"])

            doc = documents[idx]
            metadata = dict(doc.metadata)
            metadata["rerank_score"] = score

            reranked_documents.append(
                Document(
                    page_content=doc.page_content,
                    metadata=metadata,
                )
            )

        return reranked_documents

    async def rerank_async(
        self, query: str, documents: list[Document]
    ) -> list[Document]:
        """Phiên bản bất đồng bộ của rerank"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            self.executor, self.rerank, query, documents
        )