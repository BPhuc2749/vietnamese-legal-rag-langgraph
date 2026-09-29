from pydantic import BaseModel
from langchain_core.messages import BaseMessage
from typing import List, Dict


class ChatMessage(BaseModel):
    role: str 
    content: str

class ChatRequest(BaseModel):
    query: str
    chat_history: List[ChatMessage] = [] # Nhận danh sách các tin nhắn cũ
    
class ResponseMetadata(BaseModel):
    retrieval_count : int
    web_search_count : int
    processing_time : float
    
class ChatResponse(BaseModel):
    final_answer: str
    citations: list[str]
    metadata: ResponseMetadata