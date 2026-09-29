import app.loader as loader

from app.schemas.planning import EvidenceItem
from app.state.state import AgentState


def get_web_search_plan(
    state: AgentState,
) -> list[EvidenceItem]:
    """
    Xác định danh sách EvidenceItem cần tìm kiếm.

    WEB:
        - Search toàn bộ Evidence Plan.

    HYBRID:
        - Search toàn bộ Evidence Plan.

    AUTO:
        - Nếu Review Node đã tạo missing_evidence
          -> chỉ search phần còn thiếu.
        - Ngược lại
          -> search toàn bộ Evidence Plan.
    """

    search_mode = state["search_mode"]

    if search_mode in ["WEB", "HYBRID"]:
    # if search_mode in ["web", "hybrid"]:
        return state["evidence_plan"]

    if search_mode == "AUTO":
    # if search_mode == "auto":

        if state["missing_evidence"]:
            return state["missing_evidence"]

        return state["evidence_plan"]

    return []


def web_search_node(
    state: AgentState,
) -> AgentState:
    """
    Web Search Node.
    """

    if loader.tavily_retriever is None:
        raise RuntimeError(
            "Tavily Retriever has not been initialized."
        )

    evidence_items = get_web_search_plan(state)

    web_results = []

    for evidence in evidence_items:

        result = loader.tavily_retriever.retrieve(
            topic=evidence.topic,
            query=evidence.query,
        )

        web_results.append(result)

    state["web_results"] = web_results
    state["web_search_count"] = len(web_results)

    return state