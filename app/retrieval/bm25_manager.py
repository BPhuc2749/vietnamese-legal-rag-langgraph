from pathlib import Path
import pickle

from langchain_core.documents import Document
from rank_bm25 import BM25Okapi
from underthesea import word_tokenize

from app.config import settings


class BM25Manager:

    def __init__(self):

        self.bm25 = None
        self.documents: list[Document] = []

        self.save_dir = Path(settings.vector_store_path) / "bm25"

        self.save_dir.mkdir(parents=True, exist_ok=True)

        self.bm25_path = self.save_dir / "bm25.pkl"
        self.documents_path = self.save_dir / "documents.pkl"

    # ==========================================================
    # Tokenizer
    # ==========================================================

    @staticmethod
    def tokenize(text: str) -> list[str]:
        return word_tokenize(
            text.lower(),
            format="text"
        ).split()

    # ==========================================================
    # Build
    # ==========================================================

    def build(
        self,
        documents: list[Document],
    ):

        self.documents = documents

        corpus = [
            self.tokenize(doc.page_content)
            for doc in documents
        ]

        self.bm25 = BM25Okapi(corpus)

    # ==========================================================
    # Save
    # ==========================================================

    def save(self):

        with open(self.bm25_path, "wb") as f:
            pickle.dump(self.bm25, f)

        with open(self.documents_path, "wb") as f:
            pickle.dump(self.documents, f)

    # ==========================================================
    # Load
    # ==========================================================

    def load(self):

        with open(self.bm25_path, "rb") as f:
            self.bm25 = pickle.load(f)

        with open(self.documents_path, "rb") as f:
            self.documents = pickle.load(f)

    # ==========================================================
    # Search
    # ==========================================================

    def search(
        self,
        query: str,
    ) -> list[Document]:

        if self.bm25 is None:
            raise RuntimeError("BM25 index has not been loaded.")

        query_tokens = self.tokenize(query)

        scores = self.bm25.get_scores(query_tokens)

        ranked = sorted(
            enumerate(scores),
            key=lambda x: x[1],
            reverse=True,
        )

        top_docs = []

        for idx, score in ranked[:settings.retrieval_top_k]:

            doc = self.documents[idx]

            doc.metadata["bm25_score"] = float(score)

            top_docs.append(doc)

        return top_docs
    
