from fastapi import APIRouter, HTTPException, Depends
from app.schemas.chat import ChatRequest, ChatResponse, ResponseMetadata
from app.api.v1 import deps  # Import file deps bạn vừa tạo
from app.state.state import create_initial_state
import time
import uuid
from langchain_core.messages import HumanMessage, AIMessage
from fastapi.responses import StreamingResponse
import json
import re

router = APIRouter()
@router.post("/streaming")
async def chat_streaming(
    request: ChatRequest, 
    graph = Depends(deps.get_graph)
):
    async def event_generator():
        start_time = time.time()
        
        # 1. Chuyển đổi ChatHistory từ Pydantic sang LangChain Objects (Xử lý Memory)
        langchain_history = []
        for msg in request.chat_history:
            # Truy cập trực tiếp thuộc tính của Pydantic Model
            role = msg.role
            content = msg.content
            if role == "user":
                langchain_history.append(HumanMessage(content=content))
            else:
                langchain_history.append(AIMessage(content=content))

        # 2. Khởi tạo state và config
        initial_state = create_initial_state(
            user_query=request.query,
            chat_history=langchain_history
        )
        
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}

        # CÁC BIẾN ĐIỀU KHIỂN LUỒNG LỌC JSON
        accumulated_text = ""      # Kho chứa toàn bộ JSON thô
        yielded_ptr = 0            # Vị trí đã in ra
        has_started = False
        final_citations = []

        try:
            # 3. Chạy astream_events để bắt luồng dữ liệu
            async for event in graph.astream_events(initial_state, version="v2", config=config):
                kind = event["event"]
                # --- BẮN TÍN HIỆU TRẠNG THÁI ĐỂ GIỮ KẾT NỐI (CHỐNG TIMEOUT) ---
                if kind == "on_chain_start":
                    node_name = event.get("name")
                    if node_name == "planning":
                        yield "🔍 *Đang phân tích câu hỏi và lập kế hoạch...*\n\n"
                    elif node_name in ["rag_mode", "rag_hybrid", "rag_auto"]:
                        yield "📚 *Đang tra cứu kho văn bản pháp luật...*\n\n"
                    elif node_name in ["web_mode", "web_hybrid", "web_auto"]:
                        yield "🌐 *Đang tìm kiếm thông tin bổ sung trên Internet...*\n\n"
                    elif node_name in ["review_rag", "review_web"]:
                        yield "⚖️ *Đang đối soát căn cứ pháp lý...*\n\n"
                    elif node_name == "answer":
                        yield "**Câu trả lời:**\n\n"
                # --- TRƯỜNG HỢP: LLM ĐANG GÕ (Node Answer) ---
                if kind == "on_chat_model_stream":
                    if event["metadata"].get("langgraph_node") == "answer":
                        # Lấy mẩu tin nhắn thô
                        content = event["data"]["chunk"].content
                        
                        # Xử lý nếu Gradio gửi dạng list (cho tương lai)
                        if isinstance(content, list):
                            content = "".join([c.get("text", "") for c in content if isinstance(c, dict)])
                        
                        if not content or not isinstance(content, str):
                            continue

                        accumulated_text += content

                        # A. Tìm điểm bắt đầu: Bỏ qua rác '{"final_answer": "'
                        if not has_started:
                            start_match = re.search(r'\"final_answer\":\s*\"', accumulated_text)
                            if start_match:
                                has_started = True
                                yielded_ptr = start_match.end()
                            continue

                        # B. Lọc và in nội dung sạch
                        if has_started:
                            end_match = re.search(r'\",\s*\"citations\"', accumulated_text)
                            
                            if end_match:
                                safe_content = accumulated_text[yielded_ptr : end_match.start()]
                                if safe_content:
                                    # --- SỬA TẠI ĐÂY: Giải mã ký tự xuống dòng và dấu nháy ---
                                    clean_out = safe_content.rstrip('"').replace('\\n', '\n').replace('\\"', '"')
                                    yield clean_out
                                yielded_ptr = len(accumulated_text)
                            else:
                                safe_zone = len(accumulated_text) - 100
                                if safe_zone > yielded_ptr:
                                    to_yield = accumulated_text[yielded_ptr : safe_zone]
                                    
                                    # --- SỬA TẠI ĐÂY: Giải mã ký tự xuống dòng cho từng mẩu chữ ---
                                    clean_out = to_yield.replace('\\n', '\n').replace('\\"', '"')
                                    yield clean_out
                                    
                                    yielded_ptr = safe_zone

                # --- TRƯỜNG HỢP: KẾT THÚC NODE (Lấy Citations chuẩn) ---
                elif kind == "on_chain_end":
                    if event["name"] == "answer":
                        output = event["data"].get("output")
                        if output:
                            # Lấy citations từ Object (Pydantic) hoặc Dictionary
                            raw_cites = getattr(output, 'citations', [])
                            if not raw_cites and isinstance(output, dict):
                                raw_cites = output.get('citations', [])
                            final_citations = raw_cites

            # 4. HIỂN THỊ NGUỒN THAM KHẢO VÀ THỜI GIAN
            if final_citations:
                yield "\n\n-----  \n### 📚 Nguồn tham khảo:  \n" # Thêm khoảng trắng cuối để ép Markdown
                for cite in final_citations:
                    title = getattr(cite, 'title', "")
                    if not title and isinstance(cite, dict):
                        title = cite.get('title', str(cite))
                    yield f"- {title}\n"

            duration = round(time.time() - start_time, 2)
            yield f"\n\n*(Thời gian phản hồi: {duration}s)*"

        except Exception as e:
            print(f"Streaming Error: {str(e)}")
            yield f"\n\n❌ Lỗi trong quá trình stream: {str(e)}"

    return StreamingResponse(event_generator(), media_type="text/plain")

@router.post("/", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    graph = Depends(deps.get_graph)  # Inject graph vào đây
):
    try:
        start_time = time.time()
        # 1. Chuyển đổi ChatHistory từ JSON sang LangChain Objects
        langchain_history = []
        for msg in request.chat_history:
            if msg.role == "user":
                langchain_history.append(HumanMessage(content=msg.content))
            else:
                langchain_history.append(AIMessage(content=msg.content))
        
        
        # 1. Khởi tạo state ban đầu
        initial_state = create_initial_state(
            user_query=request.query,
            chat_history=langchain_history
        )
        
        # 2. Thực thi Graph
        # Thay vì dùng ID cố định, bạn có thể lấy từ request hoặc tạo mới
        # Nếu ChatRequest chưa có session_id, tạm thời dùng uuid hoặc fix cứng
        thread_id = str(uuid.uuid4()) 
        config = {"configurable": {"thread_id": thread_id}} 
        
        # Gọi ainvoke từ graph được inject qua Depends
        result = await graph.ainvoke(initial_state, config=config)
        
        processing_time = time.time() - start_time
        
        # 3. Format citations cho đẹp
        # Dùng .get() và cung cấp giá trị mặc định để tránh lỗi KeyError
        raw_citations = result.get("citations", [])
        formatted_citations = [f"{c.title} ({c.url})" for c in raw_citations]
        
        return ChatResponse(
            final_answer=result.get("final_answer", "Xin lỗi, tôi không tìm thấy câu trả lời phù hợp."),
            citations=formatted_citations,
            metadata=ResponseMetadata(
                retrieval_count=result.get("retrieval_count", 0),
                web_search_count=result.get("web_search_count", 0),
                processing_time=round(processing_time, 2)
            )
        )
    except Exception as e:
        # Trong thực tế 2026, bạn nên dùng logger thay vì print
        print(f"Error in chat_endpoint: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="Đã có lỗi xảy ra trong quá trình xử lý yêu cầu của bạn."
        )