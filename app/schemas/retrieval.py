from langchain_core.documents import Document
from pydantic import BaseModel


class RetrievalResult(BaseModel):
    """
    Retrieval result for one planned query.
    """

    topic: str
    query: str
    documents: list[Document]