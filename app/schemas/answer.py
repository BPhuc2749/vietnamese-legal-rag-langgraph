from pydantic import BaseModel
  

class Citation(BaseModel):
    title: str
    url: str


class AnswerOutput(BaseModel):
    final_answer: str
    citations: list[Citation]