from pydantic import BaseModel 
from app.schemas.planning import EvidenceItem


class ReviewOutput(BaseModel):
    missing_evidence: list[EvidenceItem]