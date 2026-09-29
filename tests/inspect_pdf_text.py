from pathlib import Path

from app.ingestion.pdf_loader import load_pdf


DATA_DIR = Path("data/documents")
SAMPLE_LENGTH = 500
NUM_FILES = 7


def main():
    pdf_files = sorted(DATA_DIR.glob("*.pdf"))

    if len(pdf_files) < NUM_FILES:
        print(f"Found only {len(pdf_files)} PDF files.")
        return

    selected_files = pdf_files[:NUM_FILES]

    for index, pdf_file in enumerate(selected_files, start=1):
        documents = load_pdf(pdf_file)

        print("\n" + "=" * 80)
        print(f"FILE {index}: {pdf_file.name}")
        print(f"Total pages with text: {len(documents)}")
        print("=" * 80)

        if not documents:
            print("No extracted text.")
            continue

        # Lấy trang nằm giữa tài liệu
        middle_index = len(documents) // 2
        sample = documents[middle_index]

        text = sample.page_content.strip()

        print(f"Page: {sample.metadata['page']}")
        print(f"Characters: {len(text)}")

        print("\n--- SAMPLE TEXT ---")
        print(text[:SAMPLE_LENGTH])
        print("\n--- END SAMPLE ---")


if __name__ == "__main__":
    main()