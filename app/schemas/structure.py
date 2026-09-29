from pydantic import BaseModel


class StructureNode(BaseModel):
    document: str
    level: str
    value: str
    page: int
    line_index: int