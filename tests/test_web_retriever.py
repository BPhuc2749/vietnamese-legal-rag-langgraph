from pprint import pprint

from app.models.model_manager import ModelManager
from app.retrieval.tavily_retriever import TavilyRetriever


def main():

    retriever = TavilyRetriever()

    while True:

        query = input("\nQuery (exit để thoát): ")

        if query.lower() == "exit":
            break

        result = retriever.retrieve(
            topic="Khái niệm",
            query=query,
        )

        print("\n" + "=" * 80)

        print("TOPIC")
        print(result.topic)

        print("\nQUERY")
        print(result.query)

        print("\nANSWER")
        print(result.answer)

        print("\nCITATIONS")

        for i, citation in enumerate(result.citations, start=1):

            print(f"\n[{i}]")
            print(f"Title : {citation.title}")
            print(f"URL   : {citation.url}")

        print("=" * 80)


if __name__ == "__main__":
    main()