# Legal Technology Agentic RAG - Sprint Roadmap (14 Days)

## Goal

-   Hoàn thành Agentic RAG V1 trong \~10 ngày.
-   Dành 4 ngày cuối để đánh giá, tối ưu và triển khai V2 (Query
    Rewrite) nếu kịp.
-   Có project sẵn sàng đưa vào CV và GitHub.

------------------------------------------------------------------------

# Day 0 - Project Setup

## Tasks

-   Tạo GitHub repository
-   Tạo Python 3.11 virtual environment
-   Cài package cơ bản
-   Tạo folder structure
-   FastAPI Hello World
-   Commit đầu tiên

**Deliverable** - Project chạy được - Repository sẵn sàng

------------------------------------------------------------------------

# Day 1 - Foundation

## Tasks

-   config.py
-   state/
-   models/
-   utils/
-   prompts/
-   logger
-   prompt loader

**Deliverable** - Foundation hoàn chỉnh

------------------------------------------------------------------------

# Day 2 - Knowledge Base

## Tasks

-   Thu thập 10--15 PDF chính thức
-   Chuẩn hóa tên file
-   Metadata
-   data/raw
-   data/processed

**Deliverable** - Knowledge Base V1

------------------------------------------------------------------------

# Day 3 - Retrieval

## Tasks

-   Chunking
-   Embedding
-   BM25
-   FAISS
-   Hybrid Retrieval
-   Reranker

**Deliverable** - Vector Database hoạt động

------------------------------------------------------------------------

# Day 4 - LLM Layer

## Tasks

-   llm_service.py
-   Structured Output
-   Retry
-   JSON Parsing

**Deliverable** - LLM Service hoàn chỉnh

------------------------------------------------------------------------

# Day 5 - Agent Layer

## Tasks

-   Planning
-   Review
-   Answer
-   agent_service.py

**Deliverable** - Agent Service hoạt động

------------------------------------------------------------------------

# Day 6 - LangGraph

## Tasks

-   Planning Node
-   Retriever Node
-   Review Node
-   Answer Node
-   Graph

**Deliverable** - Agentic RAG chạy với RAG

------------------------------------------------------------------------

# Day 7 - Web Search

## Tasks

-   Web Search Service
-   Web Retriever Node
-   Review Loop
-   Auto Mode

**Deliverable** - Agentic RAG V1 hoàn chỉnh

------------------------------------------------------------------------

# Day 8 - API

## Tasks

-   FastAPI
-   Router
-   Schemas
-   Streaming Response

**Deliverable** - API hoàn chỉnh

------------------------------------------------------------------------

# Day 9 - Demo

## Tasks

-   Gradio hoặc Streamlit
-   Hiển thị Answer
-   Citation
-   Source

**Deliverable** - Demo UI

------------------------------------------------------------------------

# Day 10 - Evaluation

## Tasks

-   Bộ test (\~100 câu)
-   Chạy Evaluation
-   Ghi nhận lỗi

**Deliverable** - Baseline V1

------------------------------------------------------------------------

# Day 11 - Documentation

## Tasks

-   README
-   Architecture
-   Workflow
-   Folder Structure
-   Hình minh họa

**Deliverable** - GitHub chuyên nghiệp

------------------------------------------------------------------------

# Day 12 - Refactor

## Tasks

-   Fix bug
-   Clean code
-   Logging
-   Review

**Deliverable** - V1 Stable

------------------------------------------------------------------------

# Day 13 - Version 2

## Tasks

-   Query Rewrite Node
-   So sánh với V1
-   Đánh giá Recall / Accuracy

**Deliverable** - V2 (nếu cải thiện)

------------------------------------------------------------------------

# Day 14 - Final

## Tasks

-   Deploy
-   Quay demo
-   Cập nhật CV
-   Apply Intern

**Deliverable** - Project hoàn chỉnh

------------------------------------------------------------------------

# Version Roadmap

## V1

-   Official PDF Knowledge Base
-   Hybrid Retrieval
-   Review Node
-   Web Search
-   Agentic Workflow
-   Evaluation

## V2

-   Context-aware Query Rewrite
-   So sánh với V1
-   Giữ nếu cải thiện

## Sau Internship

-   Government Crawler
-   MCP
-   Knowledge Graph
-   LangSmith
-   Speech
