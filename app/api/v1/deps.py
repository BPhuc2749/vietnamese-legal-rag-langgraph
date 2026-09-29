from typing import Any
from app.models.graph_manager import graph_manager
from app.models.model_manager import model_manager
import app.loader as loader

def get_graph():
    """
    Dependency cung cấp Compiled Graph đã được load.
    """
    return graph_manager.get_graph()

def get_llm():
    """
    Dependency cung cấp LLM instance.
    """
    return model_manager.get_llm()

def get_hybrid_retriever():
    """
    Dependency cung cấp Hybrid Retriever (đã nạp Chroma & BM25).
    """
    if loader.hybrid_retriever is None:
        # Trong thực tế, lifespan sẽ đảm bảo nó không None
        # Nhưng check ở đây cho an toàn type-hinting
        loader.load_application()
    return loader.hybrid_retriever