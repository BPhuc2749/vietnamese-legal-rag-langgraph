from pydantic import BaseModel


class EvidenceItem(BaseModel):
    topic : str
    query : str
    
class PlanningOutput(BaseModel):
    intent: str
    search_mode: str
    evidence_plan: list[EvidenceItem]