from langchain_core.prompts import ChatPromptTemplate

from app.prompts.loader import load_prompt
from app.schemas.review import ReviewOutput
from app.state.state import AgentState
from app.models.model_manager import model_manager

REVIEW_PROMPT = load_prompt("review.md")


async def review_node(
    state: AgentState
) -> AgentState:
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

    structured_llm = llm.with_structured_output(
        ReviewOutput
    )

    chain = prompt | structured_llm

    rag_results = [
        {
            "topic": result.topic,
            "query": result.query,
            "documents": [
                doc.page_content
                for doc in result.documents
            ],
        }
        for result in state["rag_results"]
    ]

    result = await chain.ainvoke(
        {
            "user_query": state["user_query"],
            "evidence_plan": state["evidence_plan"],
            "rag_results": rag_results,
        }
    )

    state["missing_evidence"] = result.missing_evidence

    return state