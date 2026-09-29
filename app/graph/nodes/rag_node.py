from app.schemas.retrieval import RetrievalResult
from app.state.state import AgentState

import app.loader as loader
import asyncio

async def rag_node(
    state: AgentState,
) -> AgentState:
    """
    Retrieve relevant documents from local knowledge base.
    """

    if loader.hybrid_retriever is None:
        raise RuntimeError(
            "Hybrid Retriever has not been initialized."
        )

    # results: list[RetrievalResult] = []

    # for evidence in state["evidence_plan"]:

    #     documents = loader.hybrid_retriever.retrieve(
    #         query=evidence.query,
    #     )

    #     results.append(
    #         RetrievalResult(
    #             topic=evidence.topic,
    #             query=evidence.query,
    #             documents=documents,
    #         )
    #     )

    # state["rag_results"] = results
    # state["retrieval_count"] = len(results)

    # return state
    tasks = [
        loader.hybrid_retriever.retrieve_async(evidence.query)
        for evidence in state["evidence_plan"]
    ]

    # Đợi tất cả chạy xong cùng lúc
    all_results = await asyncio.gather(*tasks)

    results: list[RetrievalResult] = []
    for i, documents in enumerate(all_results):
        evidence = state["evidence_plan"][i]
        results.append(
            RetrievalResult(
                topic=evidence.topic,
                query=evidence.query,
                documents=documents,
            )
        )

    state["rag_results"] = results
    state["retrieval_count"] = len(results)
    return state