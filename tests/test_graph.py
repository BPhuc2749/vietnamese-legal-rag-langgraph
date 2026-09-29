import asyncio
import time

from app.loader import load_application
from app.models.graph_manager import graph_manager
from app.state.state import create_initial_state


async def main():

    print("=" * 60)
    print("Loading Dependencies...")
    print("=" * 60)

    # --------------------------------------------------
    # Load Models + Retrieval + Tavily
    # --------------------------------------------------

    load_application()

    print("=" * 60)
    print("Building Graph...")
    print("=" * 60)

    # --------------------------------------------------
    # Build Graph
    # --------------------------------------------------

    graph_manager.load_graph()

    graph = graph_manager.get_graph()

    # --------------------------------------------------
    # Initial State
    # --------------------------------------------------

    state = create_initial_state(
        user_query=(
            "Dựa vào tài liệu đã có hãy cho biết các loại Dữ Liệu Cá Nhân cơ bản được quy định ở đâu trong tài liệu nào"
        ),
        chat_history=[],
    )

    print("=" * 60)
    print("Workflow Started")
    print("=" * 60)

    start = time.perf_counter()

    async for step in graph.astream(
        state,
        stream_mode="updates",
    ):

        print("\n" + "=" * 60)

        for node_name, node_output in step.items():

            print(f"NODE : {node_name}")
            print("-" * 60)

            for key, value in node_output.items():

                print(f"{key}:")

                if isinstance(value, list):

                    print(f"(List length = {len(value)})")

                    for item in value:
                        print(item)

                else:
                    print(value)

                print()

    end = time.perf_counter()

    print("=" * 60)
    print("Workflow Finished")
    print("=" * 60)

    print(f"Processing Time : {end - start:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())