from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.v1.api_router import api_router
from app.loader import load_application
from app.models.graph_manager import graph_manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ======================================================
    # ĐOẠN NÀY CHỈ CHẠY 1 LẦN DUY NHẤT KHI START SERVER
    # ======================================================
    print("--- [STARTUP] Loading Heavy Resources ---")
    
    # 1. Load Model (LLM, Embedding, Reranker) vào RAM
    # 2. Load ChromaDB & BM25 từ ổ đĩa vào RAM
    load_application() 
    
    # 3. Build và Compile LangGraph
    graph_manager.load_graph()
    
    print("--- [STARTUP] Resources Loaded Successfully ---")
    
    yield # Server bắt đầu nhận Request ở đây
    
    # ======================================================
    # ĐOẠN NÀY CHẠY KHI TẮT SERVER
    # ======================================================
    print("--- [SHUTDOWN] Cleaning up ---")

app = FastAPI(lifespan=lifespan)
app.include_router(api_router, prefix="/api/v1")