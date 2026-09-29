from langgraph.graph import StateGraph, START, END

from app.state.state import AgentState

# Nodes
from app.graph.nodes.planning_node import planning_node
from app.graph.nodes.rag_node import rag_node
from app.graph.nodes.web_search_node import web_search_node
from app.graph.nodes.review_node import review_node
from app.graph.nodes.answer_node import answer_node

# Router
from app.graph.router import (
    route_after_planning,
    route_after_review,
)


def build_graph():
    workflow = StateGraph(AgentState)

    # ========= Nodes =========

    workflow.add_node(
        "planning",
        planning_node,
    )

    workflow.add_node(
        "rag_mode",
        rag_node,
    )

    workflow.add_node(
        "rag_hybrid",
        rag_node,
    )

    workflow.add_node(
        "rag_auto",
        rag_node,
    )

    workflow.add_node(
        "web_mode",
        web_search_node,
    )

    workflow.add_node(
        "web_hybrid",
        web_search_node,
    )

    workflow.add_node(
        "web_auto",
        web_search_node,
    )

    workflow.add_node(
        "review_rag",
        review_node,
    )

    workflow.add_node(
        "review_web",
        review_node,
    )

    workflow.add_node(
        "answer",
        answer_node,
    )

    # ========= Start =========

    workflow.add_edge(
        START,
        "planning",
    )

    # ========= Planning Router =========

    workflow.add_conditional_edges(
        "planning",
        route_after_planning,
        {
            "rag": "rag_mode",
            "web": "web_mode",
            "hybrid": "rag_hybrid",
            "auto": "rag_auto",
        },
    )

    # ========= RAG Mode =========

    workflow.add_edge(
        "rag_mode",
        "answer",
    )

    # ========= WEB Mode =========

    workflow.add_edge(
        "web_mode",
        "answer",
    )

    # ========= HYBRID =========

    workflow.add_edge(
        "rag_hybrid",
        "web_hybrid",
    )

    workflow.add_edge(
        "web_hybrid",
        "answer",
    )

    # ========= AUTO =========

    workflow.add_edge(
        "rag_auto",
        "review_rag",
    )

    workflow.add_conditional_edges(
        "review_rag",
        route_after_review,
        {
            "web": "web_auto",
            "answer": "answer",
        },
    )

    workflow.add_edge(
        "web_auto",
        "review_web",
    )

    workflow.add_edge(
        "review_web",
        "answer",
    )

    # ========= END =========

    workflow.add_edge(
        "answer",
        END,
    )

    return workflow.compile()