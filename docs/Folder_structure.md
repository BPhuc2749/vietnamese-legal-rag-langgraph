# Folder Structure v2

> Project: Legal Technology Agentic RAG
>
> Status: Final
>
> Version: 2.0

---

# 1. Design Principles

## Principle 1 - Simplicity First

Chỉ tạo Folder khi thực sự cần.

Không chia nhỏ Project quá sớm.

Ưu tiên cấu trúc đơn giản nhưng đủ khả năng mở rộng.

---

## Principle 2 - One Responsibility

Mỗi Folder chỉ chịu trách nhiệm cho một nhóm chức năng.

Ví dụ:

- graph → Workflow
- services → Business Logic
- prompts → Prompt
- state → Shared State
- models → Data Models

---

## Principle 3 - Easy Navigation

Người mới tham gia Project có thể dễ dàng xác định vị trí cần sửa.

Ví dụ.

Muốn sửa Prompt

↓

```text
prompts/
```

Muốn sửa Workflow

↓

```text
graph/
```

Muốn sửa Logic Retrieval

↓

```text
services/retrieval/
```

Muốn sửa State

↓

```text
state/
```

---

## Principle 4 - Workflow First

Cấu trúc thư mục phản ánh đúng Workflow của hệ thống.

```text
Planning

↓

Retriever (RAG)

↓

Review

↓

Retriever (Web)

↓

Answer
```

Mỗi Node chỉ đóng vai trò kết nối Graph với Service.

Business Logic không nằm trong Node.

---

# 2. Project Structure

```text
project/
│
├── app/
│   │
│   ├── api/
│   │   ├── router.py
│   │   └── schemas.py
│   │
│   ├── graph/
│   │   ├── graph.py
│   │   ├── planning_node.py
│   │   ├── retriever_node.py
│   │   ├── web_retriever_node.py
│   │   ├── review_node.py
│   │   └── answer_node.py
│   │
│   ├── prompts/
│   │   ├── planning.md
│   │   ├── review.md
│   │   └── answer.md
│   │
│   ├── services/
│   │   ├── agent_service.py
│   │   ├── llm_service.py
│   │   ├── web_search_service.py
│   │   │
│   │   └── retrieval/
│   │       ├── retrieval_service.py
│   │       ├── bm25.py
│   │       ├── vector.py
│   │       ├── hybrid.py
│   │       └── reranker.py
│   │
│   ├── state/
│   │   └── state.py
│   │
│   ├── models/
│   │   ├── document.py
│   │   ├── citation.py
│   │   └── outputs.py
│   │
│   ├── utils/
│   │   ├── logger.py
│   │   ├── helpers.py
│   │   └── formatter.py
│   │
│   ├── config.py
│   └── main.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── uploads/
│
├── vector_store/
│
├── tests/
│
├── requirements.txt
├── .env
└── README.md
```

---

# 3. Folder Responsibilities

## app/

Chứa toàn bộ Source Code của hệ thống.

---

## api/

Chịu trách nhiệm giao tiếp với bên ngoài.

Bao gồm:

- FastAPI Router
- Request Schema
- Response Schema

Không chứa Business Logic.

---

## graph/

Chứa toàn bộ Workflow của LangGraph.

---

### graph.py

Chịu trách nhiệm:

- Khởi tạo Graph
- Định nghĩa Entry Point
- Định nghĩa Edge
- Conditional Routing
- Compile Graph

Không chứa Business Logic.

---

### planning_node.py

Planning Node.

Nhiệm vụ:

- Đọc UserState
- Gọi Agent Service
- Update PlanningState

Không chứa Prompt.

Không chứa Business Logic.

---

### retriever_node.py

Retriever (RAG).

Nhiệm vụ:

- Đọc Evidence Plan
- Gọi Retrieval Service
- Update EvidenceState

---

### web_retriever_node.py

Retriever (Web).

Nhiệm vụ:

- Đọc missing_evidence
- Gọi Web Search Service
- Update EvidenceState

---

### review_node.py

Review Node.

Nhiệm vụ:

- Đọc Evidence
- Gọi Agent Service
- Update WorkflowState

---

### answer_node.py

Answer Node.

Nhiệm vụ:

- Đọc toàn bộ Evidence
- Gọi Agent Service
- Update OutputState

---

Node chỉ đóng vai trò cầu nối giữa Graph và Service.

Node không chứa:

- Business Logic
- Prompt
- Retrieval Logic
- Web Search Logic

---

## prompts/

Chứa toàn bộ Prompt Template.

Hiện tại:

```text
planning.md

review.md

answer.md
```

Prompt được tách hoàn toàn khỏi Code.

Có thể chỉnh Prompt mà không cần sửa Logic.

---

## services/

Đây là nơi chứa toàn bộ Business Logic.

---

### agent_service.py

Quản lý toàn bộ Logic sử dụng LLM.

Bao gồm:

- Planning
- Review
- Final Answer

Service này sẽ:

- đọc Prompt
- gọi LLM
- parse Output

Không tham gia Workflow.

---

### llm_service.py

Đóng gói việc giao tiếp với LLM.

Ví dụ:

- Load Model
- Generate Response
- Retry
- Temperature
- Token Limit
- Structured Output

---

### retrieval/

Chứa toàn bộ Pipeline Retrieval.

Bao gồm:

#### retrieval_service.py

Điều phối toàn bộ quá trình Retrieval.

#### bm25.py

BM25 Search.

#### vector.py

Vector Search.

#### hybrid.py

Hybrid Retrieval.

#### reranker.py

Cross Encoder Reranker.

Toàn bộ Retrieval Logic chỉ nằm trong thư mục này.

---

### web_search_service.py

Chứa toàn bộ Pipeline Web Search.

Bao gồm:

- Search
- Crawl
- Parse
- Normalize
- Metadata Processing

Không chứa Logic Review.
# 4. Data Folder

## data/raw/

Lưu dữ liệu gốc.

Ví dụ:

- PDF
- DOCX
- TXT

Đây là dữ liệu chưa qua xử lý.

---

## data/processed/

Lưu dữ liệu sau khi xử lý.

Ví dụ:

- Clean Text
- Chunk
- Metadata

Dữ liệu trong thư mục này được sử dụng để tạo Vector Store.

---

## data/uploads/

Dành cho dữ liệu người dùng Upload trong tương lai.

Ví dụ:

- PDF Upload
- DOCX Upload
- TXT Upload

Hiện tại chưa sử dụng.

---

# 5. Vector Store

```text
vector_store/
```

Chứa toàn bộ Embedding Database.

Ví dụ:

- FAISS
- Chroma

Không lưu:

- File gốc
- Chunk gốc
- Prompt

Chỉ lưu dữ liệu Embedding phục vụ Retrieval.

---

# 6. Models

```text
models/
```

Chứa các Data Model dùng chung trong toàn hệ thống.

Ví dụ:

### document.py

Định nghĩa cấu trúc Document sau Retrieval.

### citation.py

Định nghĩa Citation trả về cho Answer Node.

### outputs.py

Định nghĩa các Structured Output của LLM.

Ví dụ:

- PlanningOutput
- ReviewOutput
- AnswerOutput

Models giúp chuẩn hóa dữ liệu trao đổi giữa các Service.

---

# 7. State

```text
state/
```

Chứa Workflow State của LangGraph.

Hiện tại gồm:

```text
state.py
```

Định nghĩa toàn bộ Workflow State.

Bao gồm:

- UserState
- PlanningState
- EvidenceState
- WorkflowState
- OutputState
- MetadataState

Trong tương lai có thể mở rộng thêm:

```text
reducers.py

validators.py
```

nếu Workflow trở nên phức tạp hơn.

---

# 8. Utils

```text
utils/
```

Chứa các hàm tiện ích dùng chung.

Ví dụ:

- Logger
- Formatter
- Timer
- Helper

Không chứa Business Logic.

---

# 9. config.py

Quản lý toàn bộ cấu hình của hệ thống.

Ví dụ:

- API Key
- Model Name
- Embedding Model
- Reranker Model
- Top K
- Chunk Size
- Temperature
- Timeout

Toàn bộ cấu hình được quản lý tập trung.

---

# 10. main.py

Điểm khởi động của ứng dụng.

Khởi tạo:

- FastAPI
- LangGraph
- Services
- Configuration

Sau đó expose API.

---

# 11. Tests

```text
tests/
```

Chứa toàn bộ Test của Project.

Ví dụ:

- Unit Test
- Integration Test
- Graph Test
- Retrieval Test

Không chứa dữ liệu thật.

---

# 12. Design Summary

```text
                Graph
                  │
                  ▼
               Node Layer
                  │
        Read State / Write State
                  │
                  ▼
            Service Layer
                  │
      Business Logic / LLM / Tool
                  │
                  ▼
            Update Workflow State
```

Workflow chỉ tồn tại trong:

```text
graph/
```

Business Logic chỉ tồn tại trong:

```text
services/
```

Prompt chỉ tồn tại trong:

```text
prompts/
```

State chỉ tồn tại trong:

```text
state/
```

---

# 13. Folder Mapping

| Folder | Responsibility |
|----------|----------------|
| api | API Layer |
| graph | LangGraph Workflow |
| prompts | Prompt Template |
| services | Business Logic |
| retrieval | Retrieval Pipeline |
| state | Workflow State |
| models | Shared Data Models |
| utils | Shared Utilities |
| data | Raw & Processed Documents |
| vector_store | Embedding Database |
| tests | Testing |

---

# 14. Design Philosophy

Kiến trúc thư mục được xây dựng theo các nguyên tắc:

- Workflow và Business Logic tách biệt hoàn toàn.
- Node không chứa Business Logic.
- Service không chứa Workflow.
- Prompt độc lập với Code.
- State là trung tâm giao tiếp giữa các Node.
- Mỗi Folder chỉ có một trách nhiệm rõ ràng.
- Dễ mở rộng mà không cần thay đổi kiến trúc hiện tại.

---

# 15. Architecture Summary

```text
                 User
                   │
                   ▼
                FastAPI
                   │
                   ▼
              LangGraph
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   Planning     Review     Answer
      │            ▲
      ▼            │
 Retriever(RAG)    │
      │            │
      ▼            │
 Retriever(Web) ───┘
                   │
                   ▼
                Response
```

Mỗi Node chỉ:

- Đọc State
- Gọi Service
- Ghi State

Mọi xử lý nghiệp vụ đều nằm trong Service Layer.

---

# 16. Future Extensions

Kiến trúc hiện tại cho phép bổ sung thêm Node hoặc Service mà không cần thay đổi cấu trúc tổng thể.

Ví dụ:

- OCR Service
- SQL Retrieval
- MCP Tool Calling
- Legal Update Service
- Evaluation Service
- Speech-to-Text
- Text-to-Speech
- LangSmith
- Human Feedback
- Multi-Vector Retrieval

Nhờ tách biệt rõ giữa Workflow, State và Business Logic, các thành phần mới có thể được tích hợp với mức thay đổi tối thiểu.