from typing import TypedDict
from app.schemas.web_search import WebSearchResult
from langchain_core.messages import BaseMessage
from app.schemas.planning import EvidenceItem
from app.schemas.retrieval import RetrievalResult
from app.schemas.answer import Citation
class AgentState(TypedDict):
    # User State
    user_query : str
    chat_history : list[BaseMessage]
    
    # Planning State
    intent : str
    search_mode : str
    evidence_plan : list[EvidenceItem]
    
    # Evidence State
    rag_results : list[RetrievalResult]
    web_results : list[WebSearchResult]
    
    # Workflow State
    missing_evidence : list[EvidenceItem]
    
    # Output State
    final_answer : str
    citations : list [Citation]
    
    # Metatdata State
    retrieval_count : int
    web_search_count : int
    # processing_time : float
    
def create_initial_state(
    user_query: str,
    chat_history: list[BaseMessage],
) -> AgentState:
    return {
        # User State
        "user_query": user_query,
        "chat_history": chat_history,

        # Planning State
        "intent": "",
        "search_mode": "",
        "evidence_plan": [],

        # Evidence State
        "rag_results": [],
        "web_results": [],

        # Workflow State
        "missing_evidence": [],

        # Output State
        # "final_answer": "",
        # "citations": [],

        # Metadata State
        "retrieval_count": 0,
        "web_search_count": 0,
        # "processing_time": 0.0,
    }