from app.state.state import AgentState


def route_after_planning(state: AgentState) -> str:
    """
    Điều hướng workflow sau Planning Node
    dựa trên Search Mode mà Planning đã quyết định.
    """

    return state["search_mode"].lower()


def route_after_review(state: AgentState) -> str:
    """
    Điều hướng workflow sau Review Node (chỉ dùng cho Auto Mode).

    Nếu còn Evidence chưa được bao phủ,
    chuyển sang Web Search.

    Nếu đã đủ Evidence,
    chuyển sang Answer Node.
    """

    if len(state["missing_evidence"]) > 0:
        return "web"

    return "answer"