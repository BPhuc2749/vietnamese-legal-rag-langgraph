from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
# from sentence_transformers import CrossEncoder
from flashrank import Ranker

from app.config import settings


class ModelManager:
    def __init__(self):
        self.llm = None
        self.embedding_model = None
        self.reranker = None

    def load_models(self):
        # LLM
        self.llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            google_api_key=settings.google_api_key,
        )

        # Embedding
        self.embedding_model = HuggingFaceEmbeddings(
            model_name=settings.embedding_model,
        )

        # Reranker
        # self.reranker = CrossEncoder(
        #     settings.reranker_model,
        # )
        self.reranker = Ranker(
         model_name=settings.reranker_model,
        )

    def get_llm(self):
        if self.llm is None:
            raise RuntimeError(
                "LLM has not been loaded yet."
            )
        return self.llm

    def get_embedding_model(self):
        if self.embedding_model is None:
            raise RuntimeError(
                "Embedding model has not been loaded yet."
            )
        return self.embedding_model

    def get_reranker(self):
        if self.reranker is None:
            raise RuntimeError(
                "Reranker has not been loaded yet."
            )
        return self.reranker
    
    
model_manager = ModelManager()