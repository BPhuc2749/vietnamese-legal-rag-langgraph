from pprint import pprint

from langchain_core.prompts import ChatPromptTemplate

from app.prompts.loader import load_prompt
from app.schemas.planning import EvidenceItem
from app.schemas.review import ReviewOutput
from app.schemas.retrieval import RetrievalResult
from app.models.model_manager import ModelManager

REVIEW_PROMPT = load_prompt("review.md")


async def main():

    # Load model giống như FastAPI startup
    model_manager = ModelManager()
    model_manager.load_models()

    llm = model_manager.get_llm()

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                REVIEW_PROMPT,
            ),
            (
                "human",
                """
User Query:
{user_query}

Evidence Plan:
{evidence_plan}

RAG Results:
{rag_results}
""",
            ),
        ]
    )

    chain = prompt | llm.with_structured_output(
        ReviewOutput
    )

    user_query = (
        "Dữ liệu cá nhân là gì và mức xử phạt khi làm lộ dữ liệu cá nhân?"
    )

    evidence_plan = [
        EvidenceItem(
            topic="Khái niệm",
            query="Dữ liệu cá nhân là gì?"
        ),
        EvidenceItem(
            topic="Mức xử phạt",
            query="Mức xử phạt khi làm lộ dữ liệu cá nhân"
        ),
        EvidenceItem(
            topic="Quyền của chủ thể dữ liệu",
            query="Quyền của chủ thể dữ liệu cá nhân"
        ),
    ]

    rag_results = [
        {
            "topic": "Khái niệm",
            "query": "Dữ liệu cá nhân là gì?",
            "documents": [
                """
Dữ liệu cá nhân là thông tin dưới dạng ký hiệu,
chữ viết, chữ số, hình ảnh, âm thanh hoặc dạng tương tự
gắn liền với một con người cụ thể hoặc giúp xác định
một con người cụ thể.
"""
            ],
        },
        {
            "topic": "Mức xử phạt",
            "query": "Mức xử phạt khi làm lộ dữ liệu cá nhân",
            "documents": [],
        },
        {
                    "topic": "Quyền của chủ thể dữ liệu",
                    "query": "Quyền của chủ thể dữ liệu cá nhân",
                    "documents": [],
                },
    
        
    ]

    result = await chain.ainvoke(
        {
            "user_query": user_query,
            "evidence_plan": evidence_plan,
            "rag_results": rag_results,
        }
    )

    print("=" * 80)
    print("MISSING EVIDENCE")
    print("=" * 80)

    pprint(result.model_dump())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())