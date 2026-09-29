import asyncio

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.documents import Document

from app.models.model_manager import ModelManager
from app.prompts.loader import load_prompt
from app.schemas.answer import AnswerOutput
from app.schemas.planning import EvidenceItem
from app.schemas.retrieval import RetrievalResult
from app.schemas.web_search import Citation, WebSearchResult


ANSWER_PROMPT = load_prompt("answer.md")


async def main():
    # Load model
    model_manager = ModelManager()
    model_manager.load_models()

    llm = model_manager.get_llm()

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                ANSWER_PROMPT,
            ),
            (
                "human",
                """
Intent:
{intent}

User Query:
{user_query}

Evidence Plan:
{evidence_plan}

RAG Results:
{rag_results}

Web Results:
{web_results}
""",
            ),
        ]
    )

    structured_llm = llm.with_structured_output(AnswerOutput)

    chain = prompt | structured_llm

    result = await chain.ainvoke(
        {
            "intent": "information",
            "user_query": (
                "Dữ liệu cá nhân là gì và mức xử phạt khi làm lộ dữ liệu cá nhân?"
            ),
            "evidence_plan": [
                EvidenceItem(
                    topic="Khái niệm",
                    query="Dữ liệu cá nhân là gì?",
                ),
                EvidenceItem(
                    topic="Mức xử phạt",
                    query="Mức xử phạt khi làm lộ dữ liệu cá nhân",
                ),
            ],
            "rag_results": [
                RetrievalResult(
                    topic="Khái niệm",
                    query="Dữ liệu cá nhân là gì?",
                    documents=[
                        Document(
                            page_content=(
                                "Dữ liệu cá nhân là thông tin dưới dạng ký hiệu, "
                                "chữ viết, chữ số, hình ảnh, âm thanh hoặc dạng "
                                "tương tự trên môi trường điện tử gắn liền với "
                                "một con người cụ thể hoặc giúp xác định một "
                                "con người cụ thể."
                            ),
                            metadata={
                                "title": "Nghị định 13/2023/NĐ-CP",
                                "url": "https://vanbanphapluat.co/nghi-dinh-13-2023-nd-cp-bao-ve-du-lieu-ca-nhan",
                            },
                        )
                    ],
                )
            ],
            "web_results": [
                WebSearchResult(
                    topic="Mức xử phạt",
                    query="Mức xử phạt khi làm lộ dữ liệu cá nhân",
                    answer=(
                        "Theo quy định hiện hành, hành vi làm lộ dữ liệu cá nhân "
                        "có thể bị xử phạt từ 10.000.000 đồng đến "
                        "20.000.000 đồng tùy theo tính chất và mức độ vi phạm."
                    ),
                    citations=[
                        Citation(
                            title="Thư viện Pháp luật",
                            url="https://thuvienphapluat.vn/",
                        )
                    ],
                )
            ],
        }
    )

    print("\n================ FINAL ANSWER ================\n")
    print(result.final_answer)

    print("\n================ CITATIONS ===================\n")

    for i, citation in enumerate(result.citations, start=1):
        print(f"[{i}]")
        print("Title :", citation.title)
        print("URL   :", citation.url)
        print()


if __name__ == "__main__":
    asyncio.run(main())