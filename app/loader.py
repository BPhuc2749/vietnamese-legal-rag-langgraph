"""
Application Loader

Khởi tạo toàn bộ dependency của hệ thống.
File này chỉ được gọi đúng một lần khi application startup.
"""

from app.models.model_manager import model_manager

from app.retrieval.chroma_manager import ChromaManager
from app.retrieval.bm25_manager import BM25Manager
from app.retrieval.reranker import Reranker
from app.retrieval.hybrid_retriever import HybridRetriever
from app.retrieval.tavily_retriever import TavilyRetriever


# ==========================================================
# Global Dependencies
# ==========================================================

chroma_manager: ChromaManager | None = None
bm25_manager: BM25Manager | None = None

reranker: Reranker | None = None

hybrid_retriever: HybridRetriever | None = None
tavily_retriever: TavilyRetriever | None = None


# ==========================================================
# Loader
# ==========================================================

def load_application() -> None:
    """
    Initialize the whole application.

    This function should be called exactly once.

    It loads:
        - LLM
        - Embedding Model
        - CrossEncoder
        - ChromaDB
        - BM25
        - Hybrid Retriever
        - Tavily Retriever
        - LangGraph
    """

    global chroma_manager
    global bm25_manager

    global reranker

    global hybrid_retriever
    global tavily_retriever

    # ------------------------------------------------------
    # Models
    # ------------------------------------------------------

    model_manager.load_models()

    # ------------------------------------------------------
    # Chroma
    # ------------------------------------------------------

    chroma_manager = ChromaManager(
        model_manager=model_manager,
    )

    # ------------------------------------------------------
    # BM25
    # ------------------------------------------------------

    bm25_manager = BM25Manager()
    bm25_manager.load()

    # ------------------------------------------------------
    # Reranker
    # ------------------------------------------------------

    reranker = Reranker(
        model_manager=model_manager,
    )

    # ------------------------------------------------------
    # Hybrid Retriever
    # ------------------------------------------------------

    hybrid_retriever = HybridRetriever(
        chroma_manager=chroma_manager,
        bm25_manager=bm25_manager,
        reranker=reranker,
    )

    # ------------------------------------------------------
    # Tavily Retriever
    # ------------------------------------------------------

    tavily_retriever = TavilyRetriever()

 