# State Design v4

> Project: Legal Technology Agentic RAG
>
> Status: Final
>
> Version: 4.0

---

# 1. Design Principles

## Principle 1 - Source of Truth

State chỉ lưu **dữ liệu gốc (Source of Truth)**.

Không lưu các dữ liệu có thể suy diễn từ dữ liệu khác.

Ví dụ:

❌ Không lưu:

- covered_topics
- evidence_status
- reasoning_strategy

Các thông tin trên đều có thể suy ra từ:

- evidence_plan
- rag_documents
- web_documents

State chỉ lưu dữ liệu cần thiết để các Node tiếp tục Workflow.

---

## Principle 2 - Node Communication

Các Node không giao tiếp trực tiếp với nhau.

Mọi dữ liệu đều truyền thông qua Workflow State.

```text
Planning Node
      │
      ▼
Workflow State
      │
      ▼
Retriever Node
```

Không Node nào được gọi trực tiếp Node khác.

---

## Principle 3 - State Ownership

Mỗi Field chỉ có một Owner duy nhất.

Chỉ Owner mới được phép cập nhật Field đó.

Các Node khác chỉ được đọc.

Điều này giúp:

- tránh xung đột dữ liệu
- dễ debug
- dễ mở rộng Workflow

---

## Principle 4 - Immutable Planning

Planning chỉ thực hiện một lần.

Sau khi Planning Node tạo:

```text
evidence_plan
```

thì không Node nào được phép chỉnh sửa.

Review Node chỉ được phép tạo:

```text
missing_evidence
```

bằng cách lọc từ Evidence Plan.

---

## Principle 5 - Workflow Driven

Workflow không được điều hướng bằng Logic trong Node.

Workflow được điều hướng hoàn toàn bằng Workflow State.

Ví dụ.

```text
need_websearch = true
```

↓

Graph chuyển sang:

```text
Retriever (Web)
```

---

# 2. State Structure

Workflow State được chia thành sáu nhóm.

```text
State
│
├── UserState
├── PlanningState
├── EvidenceState
├── WorkflowState
├── OutputState
└── MetadataState
```

Mỗi nhóm chỉ quản lý một loại dữ liệu.

---

# 3. UserState

Thông tin đầu vào của người dùng.

```python
UserState = {

    "user_query": str,

    "chat_history": list

}
```

---

## user_query

Câu hỏi hiện tại của người dùng.

Ví dụ:

```text
"Dữ liệu cá nhân là gì?"
```

Owner

- User

Read

- Planning Node
- Answer Node

---

## chat_history

Các đoạn hội thoại gần nhất.

Ví dụ:

```python
[
    HumanMessage(...),
    AIMessage(...),
    HumanMessage(...),
    AIMessage(...)
]
```

Lưu ý:

- Chỉ lưu một số lượng Message gần nhất.
- Không lưu toàn bộ lịch sử hội thoại.
- Không do LangGraph quản lý.

Memory Layer sẽ quyết định:

- lưu bao nhiêu Message
- cắt theo Token
- hoặc thay bằng Conversation Summary trong tương lai.

Owner

- Memory Layer

Read

- Planning Node
- Answer Node

---

# 4. PlanningState

Được tạo duy nhất bởi Planning Node.

```python
PlanningState = {

    "intent": str,

    "search_mode": str,

    "evidence_plan": list

}
```

---

## intent

Loại yêu cầu của người dùng.

Ví dụ:

```text
definition

comparison

scenario
```

Intent quyết định cách Planning Node xây dựng Evidence Plan.

Owner

- Planning Node

Read

- Review Node
- Answer Node

---

## search_mode

Ví dụ:

```text
auto

rag

web

hybrid
```

Ý nghĩa

Auto

Planning Node tự quyết định Workflow.

RAG

Chỉ sử dụng Knowledge Base.

Web

Chỉ sử dụng Internet.

Hybrid

Bắt buộc sử dụng cả Knowledge Base và Internet.

Owner

- Planning Node

Read

- Graph Router

---

## evidence_plan

Đây là kế hoạch thu thập Evidence.

Ví dụ:

```python
[
    {

        "topic": "Khái niệm dữ liệu cá nhân",

        "query": "dữ liệu cá nhân"

    },

    {

        "topic": "Trách nhiệm doanh nghiệp",

        "query": "trách nhiệm doanh nghiệp dữ liệu"

    },

    {

        "topic": "Xử phạt",

        "query": "xử phạt dữ liệu cá nhân"

    }

]
```

Evidence Plan chỉ mô tả:

```text
"Tôi cần thu thập những Information Need nào?"
```

Không lưu:

- documents
- status
- score
- priority

Evidence Plan là **Immutable**.

Owner

- Planning Node

Read

- Retriever (RAG)
- Review Node

---

# 5. EvidenceState

Được cập nhật bởi các Retriever Node.

```python
EvidenceState = {

    "rag_documents": list,

    "web_documents": list

}
```

---

## rag_documents

Danh sách Document thu được từ Knowledge Base.

Ví dụ:

```python
Document(

    page_content="...",

    metadata={

        "topic":"Khái niệm dữ liệu cá nhân",

        "source":"rag",

        "document":"Nghị định 13",

        "page":12

    }

)
```

Retriever (RAG) sẽ tự bổ sung Metadata.

Owner

- Retriever (RAG)

Read

- Review Node
- Answer Node

---

## web_documents

Danh sách Document thu được từ Internet.

Ví dụ:

```python
Document(

    page_content="...",

    metadata={

        "topic":"Xử phạt",

        "source":"web",

        "url":"https://..."

    }

)
```

Retriever (Web) sẽ tự bổ sung Metadata.

Owner

- Retriever (Web)

Read

- Review Node
- Answer Node

---

# 6. WorkflowState

WorkflowState điều hướng toàn bộ Graph.

```python
WorkflowState = {

    "need_websearch": False,

    "missing_evidence": [

        {

            "topic": str,

            "query": str

        }

    ]

}
```

---

## need_websearch

Được cập nhật bởi Review Node.

```text
False
```

↓

Workflow chuyển sang:

```text
Answer Node
```

```text
True
```

↓

Workflow chuyển sang:

```text
Retriever (Web)
```

Owner

- Review Node

Read

- Graph Router

---

## missing_evidence

Danh sách các Topic chưa được Evidence hiện tại bao phủ.

Ví dụ:

```python
[
    {

        "topic":"Nghĩa vụ thông báo",

        "query":"Nghĩa vụ thông báo vi phạm dữ liệu"

    },

    {

        "topic":"Xử phạt",

        "query":"Xử phạt vi phạm dữ liệu cá nhân"

    }

]
```

`missing_evidence` được tạo bằng cách lọc từ:

```text
evidence_plan
```

Review Node không được:

- tạo Topic mới
- tạo Query mới
- chỉnh sửa Query
- chỉnh sửa Evidence Plan

Owner

- Review Node

Read

- Retriever (Web)

# 7. OutputState

Kết quả cuối cùng của Workflow.

```python
OutputState = {

    "final_answer": str,

    "citations": list

}
```

---

## final_answer

Câu trả lời cuối cùng được sinh bởi Answer Node.

Owner

- Answer Node

Read

- Response Layer

---

## citations

Danh sách Citation được sử dụng trong Final Answer.

Ví dụ:

```python
[
    {

        "source":"rag",

        "document":"Nghị định 13",

        "page":12

    },

    {

        "source":"web",

        "url":"https://..."

    }

]
```

Owner

- Answer Node

Read

- Response Layer

---

# 8. MetadataState

Thông tin phục vụ Logging và Monitoring.

```python
MetadataState = {

    "retrieval_count": 0,

    "web_search_count": 0,

    "processing_time": 0.0

}
```

Metadata không tham gia điều hướng Workflow.

Chỉ dùng cho:

- Logging
- Debug
- Dashboard
- LangSmith

---

## retrieval_count

Số lần Retriever (RAG) được gọi.

Owner

- Retriever (RAG)

---

## web_search_count

Số lần Retriever (Web) được gọi.

Owner

- Retriever (Web)

---

## processing_time

Tổng thời gian xử lý của Workflow.

Owner

- System

---

# 9. State Ownership

| Field | Owner |
|---------|------------------|
| user_query | User |
| chat_history | Memory Layer |
| intent | Planning Node |
| search_mode | Planning Node |
| evidence_plan | Planning Node |
| rag_documents | Retriever (RAG) |
| web_documents | Retriever (Web) |
| need_websearch | Review Node |
| missing_evidence | Review Node |
| final_answer | Answer Node |
| citations | Answer Node |
| retrieval_count | Retriever (RAG) |
| web_search_count | Retriever (Web) |
| processing_time | System |

---

# 10. State Evolution

```text
User

↓

UserState

↓

Planning Node

↓

PlanningState

↓

Retriever (RAG)

↓

EvidenceState

↓

Review Node

↓

need_websearch ?

├───────────────┐
│               │
│ No            │ Yes
│               │
▼               ▼
Answer Node   missing_evidence
                  │
                  ▼
          Retriever (Web)
                  │
                  ▼
           EvidenceState Update
                  │
                  ▼
             Review Node
                  │
                  ▼
                 ...
```

Mọi Node đều chỉ đọc và ghi dữ liệu thông qua State.

Không có Node nào gọi trực tiếp Node khác.

---

# 11. Future Extensions

State được thiết kế để dễ mở rộng.

Ví dụ:

- Conversation Summary
- Long Context Window
- Streaming Response
- Speech Input
- Speech Output
- Evaluation Metrics
- MCP Tool Integration
- SQL Query
- Database Retrieval

Các tính năng trên có thể bổ sung mà không cần thay đổi kiến trúc State hiện tại.

---

# 12. Complete State

Toàn bộ State sau khi kết hợp tất cả các nhóm State.

```python
State = {

    # ==========================
    # User State
    # ==========================

    "user_query": str,

    "chat_history": list,


    # ==========================
    # Planning State
    # ==========================

    "intent": str,

    "search_mode": str,

    "evidence_plan": [

        {

            "topic": str,

            "query": str

        }

    ],


    # ==========================
    # Evidence State
    # ==========================

    "rag_documents": [

        Document(

            page_content="...",

            metadata={

                "topic": "...",

                "source": "rag",

                "document": "...",

                "page": ...

            }

        )

    ],

    "web_documents": [

        Document(

            page_content="...",

            metadata={

                "topic": "...",

                "source": "web",

                "url": "..."

            }

        )

    ],


    # ==========================
    # Workflow State
    # ==========================

    "need_websearch": bool,

    "missing_evidence": [

        {

            "topic": str,

            "query": str

        }

    ],


    # ==========================
    # Output State
    # ==========================

    "final_answer": str,

    "citations": list,


    # ==========================
    # Metadata State
    # ==========================

    "retrieval_count": int,

    "web_search_count": int,

    "processing_time": float

}
```

---

# State Summary

| Group | Fields |
|--------|--------|
| UserState | user_query, chat_history |
| PlanningState | intent, search_mode, evidence_plan |
| EvidenceState | rag_documents, web_documents |
| WorkflowState | need_websearch, missing_evidence |
| OutputState | final_answer, citations |
| MetadataState | retrieval_count, web_search_count, processing_time |

---

# Total Fields

```text
UserState
│
├── user_query
└── chat_history

PlanningState
│
├── intent
├── search_mode
└── evidence_plan

EvidenceState
│
├── rag_documents
└── web_documents

WorkflowState
│
├── need_websearch
└── missing_evidence

OutputState
│
├── final_answer
└── citations

MetadataState
│
├── retrieval_count
├── web_search_count
└── processing_time
```

**Tổng số Field:** **13**

---

## State Lifecycle Summary

```text
Planning Node
        │
        ▼
PlanningState
        │
        ▼
Retriever (RAG)
        │
        ▼
EvidenceState
        │
        ▼
Review Node
        │
        ├───────────────┐
        │               │
        ▼               ▼
Answer Node    WorkflowState Update
                       │
                       ▼
               Retriever (Web)
                       │
                       ▼
                  EvidenceState
                       │
                       ▼
                  Review Node
                       │
                       ▼
                  Answer Node
```

Workflow được điều hướng hoàn toàn thông qua **WorkflowState**.

PlanningState là **Immutable**.

EvidenceState được cập nhật bởi các Retriever Node.

WorkflowState được cập nhật bởi Review Node.

OutputState chỉ được tạo một lần tại Answer Node.