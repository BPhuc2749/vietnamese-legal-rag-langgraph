# Agentic RAG Workflow Design

> Version: v1.2
> Status: Final Design
> Architecture: Single-Agent
> Domain: Legal Technology Research Assistant

---

# 1. Product Goal

Xây dựng một **Single-Agent Agentic RAG** hỗ trợ nghiên cứu về **Luật Công nghệ**.

Hệ thống có khả năng:

- Trả lời câu hỏi định nghĩa.
- Phân tích tình huống pháp lý.
- So sánh các văn bản pháp luật.
- Trích dẫn nguồn từ Knowledge Base.
- Mở rộng tìm kiếm trên Internet khi cần thiết.
- Tự lập kế hoạch thu thập Evidence trước khi sinh câu trả lời.

---

# 2. Design Philosophy

Project không được thiết kế theo hướng:

```text
Question
    ↓
Retriever
    ↓
LLM
```

Mà theo hướng:

```text
Question
    ↓
Reasoning
    ↓
Evidence Planning
    ↓
Evidence Collection
    ↓
Evidence Review
    ↓
Answer
```

Điểm khác biệt của Agentic RAG nằm ở **Reasoning trước khi Retrieval**, không phải chỉ đơn thuần gọi nhiều Tool.

---

## Single-Agent Architecture

Hệ thống được xây dựng theo kiến trúc **Single-Agent**.

Agent được chia thành nhiều **Reasoning Node**, mỗi Node phụ trách một giai đoạn suy luận khác nhau trong Workflow.

Toàn bộ các Node:

- sử dụng chung Workflow State
- sử dụng chung Memory
- cùng thực hiện một mục tiêu duy nhất
- không hoạt động như các Agent độc lập

Workflow được điều khiển hoàn toàn thông qua **Workflow State**.

---

## Reasoning vs Execution

Workflow được chia thành hai nhóm Node.

### Reasoning Nodes

Các Node sử dụng LLM để suy luận.

Bao gồm:

- Planning Node
- Review Node
- Answer Node

Reasoning Node có nhiệm vụ:

- hiểu yêu cầu người dùng
- lập kế hoạch Retrieval
- đánh giá Evidence
- sinh câu trả lời

---

### Execution Nodes

Các Node chỉ thực hiện hành động.

Bao gồm:

- Retriever Node (RAG)
- Retriever Node (Web)

Execution Node:

- không suy luận
- không lập kế hoạch
- không chỉnh sửa Workflow

Execution Node chỉ thực hiện Retrieval theo Workflow State.

---

# 3. System Architecture

```text
                           User
                             │
                             ▼
                     Planning Node
                             │
                             ▼
                  Update Workflow State
         (Intent / Search Mode / Evidence Plan)
                             │
      ┌──────────────────────┼──────────────────────┐
      │                      │                      │
      ▼                      ▼                      ▼
 Search Mode             Search Mode           Search Mode
     = RAG                   = WEB              = HYBRID
      │                      │                      │
      ▼                      ▼                      ▼
Retriever (RAG)       Retriever (Web)       Retriever (RAG)
                                                   │
                                                   ▼
                                            Retriever (Web)
      │                      │                      │
      └──────────────────────┴──────────────────────┘
                             │
                             ▼
                       Review Node
                             │
               ┌─────────────┴─────────────┐
               │                           │
               ▼                           ▼
need_websearch = false          need_websearch = true
               │                           │
               ▼                           ▼
        Answer Node             Update missing_evidence
                                            │
                                            ▼
                                     Retriever (Web)
                                            │
                                            ▼
                                   Update Workflow State
                                            │
                                            ▼
                                       Review Node
```

Workflow được điều hướng thông qua **Workflow State**.

Reasoning chỉ xảy ra tại:

- Planning Node
- Review Node
- Answer Node

Retriever chỉ đóng vai trò Executor.

---

# 4. Node Responsibilities

## Planning Node

Planning Node chịu trách nhiệm:

- Hiểu yêu cầu người dùng.
- Phân tích Intent.
- Xác định Search Mode.
- Xây dựng Evidence Plan.
- Khởi tạo Workflow State.

Planning Node KHÔNG:

- Retrieval.
- Web Search.
- Sinh Answer.

---

## Review Node

Review Node chịu trách nhiệm:

- Đánh giá Evidence hiện có.
- So sánh Evidence với Evidence Plan.
- Xác định Topic còn thiếu.
- Cập nhật Workflow State.
- Quyết định Workflow tiếp theo.

Review Node KHÔNG:

- Retrieval.
- Chỉnh sửa Evidence Plan.
- Sinh Query mới.

---

## Answer Node

Answer Node chịu trách nhiệm:

- Tổng hợp toàn bộ Evidence.
- Sinh câu trả lời cuối cùng.
- Trích dẫn Citation.

Answer Node KHÔNG:

- Retrieval.
- Planning.
- Review.

---

## Retriever Node

Retriever Node chỉ thực hiện Retrieval.

Retriever đọc Query từ Workflow State.

Retriever KHÔNG:

- suy luận
- tạo Query
- chỉnh sửa Query
- quyết định Workflow

---

# 5. Search Modes

Hệ thống hỗ trợ bốn chế độ tìm kiếm.

| Search Mode | Knowledge Base | Internet | Workflow |
|--------------|----------------|----------|----------|
| Auto | Khi cần | Khi cần | Agent tự quyết định |
| RAG | ✅ | ❌ | Chỉ sử dụng KB |
| Web | ❌ | ✅ | Chỉ sử dụng Internet |
| Hybrid | ✅ | ✅ | Bắt buộc sử dụng cả hai |

---

## Auto (Default)

Planning Node sẽ xác định Search Mode phù hợp.

Workflow:

```text
Planning
    │
    ▼
Retriever (RAG)
    │
    ▼
Review
    │
Need Web Search?
 ┌──┴──┐
 │     │
No    Yes
 │      │
 ▼      ▼
Answer Retriever(Web)
          │
          ▼
       Review
          │
          ▼
         ...
```

Đây là Search Mode mặc định.

---

## RAG Only

Người dùng yêu cầu:

- Chỉ sử dụng Knowledge Base.
- Không sử dụng Internet.

Workflow:

```text
Planning
    │
    ▼
Retriever (RAG)
    │
    ▼
Review
    │
    ▼
Answer
```

Workflow sẽ không bao giờ gọi Web Search.

Nếu Knowledge Base không đủ Evidence:

```text
Knowledge Base hiện tại chưa có đầy đủ thông tin.
```

---

## Web Only

Người dùng yêu cầu:

- Chỉ sử dụng Internet.
- Không sử dụng Knowledge Base.

Workflow:

```text
Planning
    │
    ▼
Retriever (Web)
    │
    ▼
Review
    │
    ▼
Answer
```

Knowledge Base sẽ được bỏ qua hoàn toàn.

---

## Hybrid

Người dùng yêu cầu:

- Bắt buộc sử dụng cả Knowledge Base.
- Bắt buộc sử dụng Internet.

Workflow:

```text
Planning
    │
    ▼
Retriever (RAG)
    │
    ▼
Retriever (Web)
    │
    ▼
Review
    │
    ▼
Answer
```

Khác với Auto:

- Web Search luôn được thực hiện.
- Không cần Review quyết định.
- Review chỉ đánh giá Evidence sau khi đã thu thập từ cả hai nguồn.

---

# 6. Intent Types

Planning Node xác định một trong ba Intent.

## Definition

Ví dụ:

```text
"Dữ liệu cá nhân là gì?"
```

Thông thường:

- Retrieve một lần.
- Evidence Plan đơn giản.

---

## Comparison

Ví dụ:

```text
"So sánh Luật A và Luật B"
```

Thông thường:

- Có nhiều Topic.
- Mỗi Topic tương ứng một Query.

---

## Scenario

Ví dụ:

```text
"Công ty bị lộ dữ liệu khách hàng có vi phạm không?"
```

Planning Node sẽ:

- Phân tích tình huống.
- Xây dựng Evidence Plan.
- Tạo nhiều Information Need nếu cần.
- Chuẩn bị Query phục vụ Retrieval.

---

# 7. Evidence Planning

Đây là trái tim của hệ thống.

Planning Node KHÔNG truyền nguyên User Query cho Retriever.

Thay vào đó tạo **Evidence Plan**.

Ví dụ.

User:

```text
Website bị hack làm lộ dữ liệu khách hàng.
```

Evidence Plan:

```text
Topic:
Khái niệm dữ liệu cá nhân

Query:
"Dữ liệu cá nhân"

------------------------

Topic:
Trách nhiệm doanh nghiệp

Query:
"Trách nhiệm doanh nghiệp khi làm lộ dữ liệu"

------------------------

Topic:
Nghĩa vụ thông báo

Query:
"Nghĩa vụ thông báo vi phạm dữ liệu"

------------------------

Topic:
Xử phạt

Query:
"Xử phạt vi phạm dữ liệu cá nhân"
```

Mỗi Information Need sinh đúng:

- một Topic
- một Query

Retriever sử dụng trực tiếp Query trong Evidence Plan.

Không tồn tại Search Plan riêng.

Evidence Plan là nguồn dữ liệu duy nhất cho Retrieval.

Evidence Plan chỉ được tạo một lần trong toàn bộ Workflow.

---

# 8. Retriever Node

Retriever Node KHÔNG suy luận.

Retriever chỉ thực hiện Retrieval.

Retriever đọc Query từ Workflow State.

Nguồn Query phụ thuộc vào Workflow:

- `evidence_plan`
- `missing_evidence`

Retriever hỗ trợ hai chế độ:

- RAG Retrieval
- Web Retrieval

Retriever chịu trách nhiệm:

- Thực hiện Retrieval.
- Thu thập Documents.
- Cập nhật Workflow State.

Retriever KHÔNG:

- quyết định Workflow
- tạo Query
- chỉnh sửa Query
- đánh giá Evidence
- sinh Answer

# 9. Evidence Review

Sau khi hoàn thành Retrieval.

Review Node sẽ đánh giá Evidence hiện có.

Review Node KHÔNG hỏi:

```text
Đã đủ chưa?
```

Mà đánh giá theo tiêu chí:

```text
Evidence hiện tại đã cover đầy đủ
các Topic trong Evidence Plan chưa?
```

Ví dụ.

Evidence Plan

```text
✓ Khái niệm dữ liệu cá nhân

✓ Trách nhiệm doanh nghiệp

✗ Nghĩa vụ thông báo

✗ Xử phạt
```

Review Node sẽ cập nhật Workflow State.

Ví dụ:

```json
{
    "need_websearch": true,
    "missing_evidence": [
        {
            "topic": "Nghĩa vụ thông báo",
            "query": "Nghĩa vụ thông báo vi phạm dữ liệu"
        },
        {
            "topic": "Xử phạt",
            "query": "Xử phạt vi phạm dữ liệu cá nhân"
        }
    ]
}
```

---

## missing_evidence

`missing_evidence` chỉ được tạo bằng cách lọc từ `evidence_plan`.

Review Node không được:

- Sinh Topic mới.
- Sinh Query mới.
- Chỉnh sửa Query.
- Bổ sung Information Need.
- Chỉnh sửa Evidence Plan.

Review chỉ xác định:

- Topic nào đã được cover.
- Topic nào còn thiếu.

Sau mỗi lần Review, `missing_evidence` sẽ được cập nhật lại.

Khi:

```text
missing_evidence = []
```

Workflow kết thúc Retrieval và chuyển sang Answer Node.

---

# 10. Web Search Decision

Việc sử dụng Web Search phụ thuộc vào Search Mode.

---

## Auto

Review Node quyết định.

Nếu:

```text
need_websearch = true
```

↓

Retriever (Web) sẽ sử dụng Query trong:

```text
missing_evidence
```

Sau đó Workflow quay lại Review.

---

## RAG

Không sử dụng Web Search.

Nếu Knowledge Base chưa đủ Evidence:

Answer Node trả lời dựa trên Evidence hiện có và thông báo rằng Knowledge Base chưa có đầy đủ thông tin.

---

## Web

Web Retrieval luôn được thực hiện ngay từ đầu.

Không sử dụng Knowledge Base.

---

## Hybrid

Workflow luôn thực hiện:

```text
Retriever (RAG)

↓

Retriever (Web)

↓

Review
```

Review không quyết định có Web Search hay không.

Review chỉ đánh giá Evidence sau khi đã thu thập từ cả hai nguồn.

---

# 11. Web Search Strategy

Retriever (Web) KHÔNG tìm kiếm nguyên User Query.

Ví dụ.

Không tìm:

```text
Website bị hack làm lộ dữ liệu khách hàng có vi phạm không?
```

Mà tìm:

```text
Thông báo vi phạm dữ liệu

Xử phạt vi phạm dữ liệu cá nhân
```

Retriever (Web) sử dụng trực tiếp Query trong:

```text
missing_evidence
```

để thực hiện Web Retrieval.

Retriever KHÔNG:

- tạo Query
- chỉnh sửa Query
- suy luận Query

`missing_evidence` được Review Node cập nhật sau mỗi vòng Review.

---

# 12. Evidence Aggregation

Sau khi hoàn thành quá trình Retrieval.

Answer Node sẽ tổng hợp:

```text
RAG Documents

+

Web Documents
```

Answer Node sẽ:

- Loại bỏ Evidence trùng lặp.
- Tổng hợp Evidence.
- Giữ nguyên Citation.
- Chuẩn bị Context cuối cùng cho LLM.

Evidence Aggregation không:

- Retrieval.
- Review.
- Planning.
- Sinh Evidence mới.

---

# 13. Final Answer

Answer Node sinh câu trả lời cuối cùng.

Input:

```text
User Query

+

Chat History

+

RAG Documents

+

Web Documents
```

Output:

- Answer
- Citation
- Source

Answer Node chỉ sử dụng Evidence đã thu thập.

Không Retrieval.

Không Review.

Không Planning.

---

# 14. Auto Workflow Summary

Workflow dưới đây áp dụng cho **Search Mode = Auto**.

```text
User Question
        │
        ▼
Planning Node
        │
        ▼
Generate Evidence Plan
        │
        ▼
Retriever (RAG)
        │
        ▼
Review Node
        │
   ┌────┴────┐
   │         │
   ▼         ▼
Answer   need_websearch
 Node         │
              ▼
     Update missing_evidence
              │
              ▼
      Retriever (Web)
              │
              ▼
         Review Node
              │
      missing_evidence ?
        ┌─────┴─────┐
        │           │
        ▼           ▼
     Continue    Answer Node
```

---

# 15. Core Design Principles

## Principle 1

Hệ thống được xây dựng theo kiến trúc **Single-Agent**.

Planning, Review và Answer là các Reasoning Node của cùng một Agent.

---

## Principle 2

Mỗi Node chỉ thực hiện một nhiệm vụ duy nhất (Single Responsibility).

---

## Principle 3

Workflow được điều hướng thông qua Workflow State.

Các Node không giao tiếp trực tiếp với nhau.

---

## Principle 4

Reasoning và Execution được tách biệt.

Reasoning Nodes:

- Planning Node
- Review Node
- Answer Node

Execution Nodes:

- Retriever (RAG)
- Retriever (Web)

---

## Principle 5

Planning chỉ thực hiện một lần.

Evidence Plan là bất biến trong suốt Workflow.

---

## Principle 6

Review không được chỉnh sửa Evidence Plan.

Review chỉ được phép cập nhật:

- need_websearch
- missing_evidence

---

## Principle 7

`missing_evidence` chỉ được tạo bằng cách lọc từ `evidence_plan`.

Không được sinh:

- Topic mới
- Query mới
- Information Need mới

---

## Principle 8

Retriever chỉ thực thi Query có trong Workflow State.

Retriever không được suy luận Query.

---

## Principle 9

Evidence được đánh giá theo từng Topic trong Evidence Plan.

Không đánh giá bằng câu hỏi:

```text
Đã đủ chưa?
```

---

## Principle 10

Answer Node chỉ sử dụng Evidence đã thu thập.

Không thực hiện:

- Planning
- Review
- Retrieval

---

# 16. Future Extensions

Sau khi hoàn thành Agentic RAG.

Có thể mở rộng thêm:

- MCP Tool Integration
- Database Search
- SQL Search
- Streaming Response
- Text-to-Speech
- Speech-to-Text
- LangSmith
- Citation Highlight
- Workflow Visualization
- Evaluation Dashboard