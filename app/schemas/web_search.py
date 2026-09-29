from pydantic import BaseModel


class Citation(BaseModel):
    """
    Citation returned from web search.
    """

    title: str
    url: str


class WebSearchResult(BaseModel):
    """
    Web search result for one planned query.
    """

    topic: str
    query: str

    answer: str

    citations: list[Citation]