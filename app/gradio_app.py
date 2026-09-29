import gradio as gr
import requests
import json
import os
# Giả sử bạn sẽ tạo một endpoint mới chuyên cho streaming ở backend
# API_URL = "http://127.0.0.1:8000/api/v1/chat/streaming" 
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000/api/v1/chat/streaming")

def predict(message, history):
    formatted_history = []

    # 1. XỬ LÝ SLIDING WINDOW (Giữ nguyên logic cũ của bạn)
    if len(history) > 0:
        raw_history = history[-6:] if isinstance(history[0], dict) else history[-3:]
        for msg in raw_history:
            if isinstance(msg, dict):
                role = msg.get("role")
                raw_content = msg.get("content", "")
                if isinstance(raw_content, list):
                    clean_text = raw_content[0].get("text", "") if len(raw_content) > 0 else ""
                else:
                    clean_text = raw_content
                formatted_history.append({"role": role, "content": clean_text})
            else:
                formatted_history.append({"role": "user", "content": msg[0]})
                formatted_history.append({"role": "assistant", "content": msg[1]})
    
    payload = {
        "query": message,
        "chat_history": formatted_history
    }

    try:
        # 1. Gửi request với stream=True
        with requests.post(API_URL, json=payload, stream=True, timeout=300) as r:
            if r.status_code != 200:
                yield "❌ Lỗi hệ thống: API không phản hồi đúng."
                return

            full_response = ""
            # 2. Đọc từng CHUNK văn bản (Không dùng r.json())
            for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
                if chunk:
                    # Gộp chữ vào chuỗi kết quả
                    full_response += chunk
                    # 3. YIELD ngay lập tức để Gradio hiển thị chữ nhảy
                    yield full_response
                    
    except Exception as e:
        yield f"❌ Lỗi kết nối: {str(e)}"
    
demo = gr.ChatInterface(
    fn=predict,
    title="Legal Tech AI Agent (Streaming Mode)",
    description="Hệ thống đã hỗ trợ nhảy chữ để giảm thời gian chờ đợi.",
    examples=["Dữ liệu cá nhân là gì?", "Mức xử phạt làm lộ dữ liệu cá nhân"]
)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)