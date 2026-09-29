from langchain_openai import ChatOpenAI


# ==========================================================
# CONFIG
# ==========================================================

OLLAMA_BASE_URL = (
    "http://localhost:11434/v1"
)


QWEN_MODEL = (
    "qwen3:8b"
)


# ==========================================================
# TEST
# ==========================================================

def main():

    print("=" * 80)
    print("TEST QWEN3:8B")
    print("=" * 80)


    llm = ChatOpenAI(

        model=QWEN_MODEL,

        base_url=OLLAMA_BASE_URL,

        api_key="ollama",

        temperature=0,

        timeout=300,

    )


    response = llm.invoke(

        """
Bạn là một hệ thống đánh giá RAG.

Hãy đánh giá câu trả lời sau.

Question:
Thời hạn bảo hộ quyền tài sản của tác giả là bao lâu?

Context:
Quyền tài sản được bảo hộ trong suốt cuộc đời tác giả
và 50 năm sau khi tác giả chết.

Answer:
Quyền tài sản được bảo hộ trong suốt cuộc đời tác giả
và 50 năm sau khi tác giả chết.

Hãy trả lời ngắn gọn.
        """

    )


    print("\nResponse:")
    print(response.content)



if __name__ == "__main__":

    main()