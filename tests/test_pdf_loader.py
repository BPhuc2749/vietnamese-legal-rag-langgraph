from pathlib import Path

from app.ingestion.pdf_loader import load_pdfs


DATA_DIR = Path("data/documents")


def main():
    documents = load_pdfs(DATA_DIR)

    print("=== PDF LOADER RESULT ===")
    print(f"Total pages loaded: {len(documents)}")

    if not documents:
        print("No PDF pages were loaded.")
        return

    print("\n=== SAMPLE DOCUMENT ===")

    sample = documents[0]

    print(f"Document: {sample.metadata['document']}")
    print(f"Page: {sample.metadata['page']}")
    print(f"Content:\n{sample.page_content[:1000]}")


if __name__ == "__main__":
    main()