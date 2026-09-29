from tavily import TavilyClient

from app.config import settings
from app.schemas.web_search import (
    Citation,
    WebSearchResult,
)


class TavilyRetriever:

    def __init__(self):

        self.client = TavilyClient(
            api_key=settings.tavily_api_key,
        )

    def retrieve(
        self,
        topic: str,
        query: str,
    ) -> WebSearchResult:

        response = self.client.search(
            query=query,
            topic="general",
            search_depth="fast",
            max_results=5,
            include_answer=True,
            include_raw_content=False,
        )

        citations: list[Citation] = []

        for item in response.get("results", []):

            citations.append(
                Citation(
                    title=item.get("title", ""),
                    url=item.get("url", ""),
                )
            )

        answer = response.get("answer") or "Không tìm thấy thông tin."

        return WebSearchResult(
            topic=topic,
            query=query,
            answer=answer,
            citations=citations,
        )
        
