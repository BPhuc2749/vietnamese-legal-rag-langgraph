import asyncio

from app.models.model_manager import ModelManager
from app.graph.nodes.planning_node import planning_node
from app.state.state import create_initial_state


async def main():
    # 1. Load LLM
    model_manager = ModelManager()
    model_manager.load_models()

    llm = model_manager.get_llm()

    # 2. Create initial state
    state = create_initial_state(
        user_query="So sánh quy định hiện hành và quy định cũ về dữ liệu cá nhân.",
        chat_history=[],
    )

    # 3. Run Planning Node
    state = await planning_node(
        state=state,
        llm=llm,
    )

    # 4. Print result
    print("\n=== PLANNING RESULT ===")
    print(f"Intent: {state['intent']}")
    print(f"Search Mode: {state['search_mode']}")
    print(f"Evidence Plan: {state['evidence_plan']}")


if __name__ == "__main__":
    asyncio.run(main())
