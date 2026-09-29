from pathlib import Path

from langchain_core.documents import Document
from pypdf import PdfReader


def load_pdf(file_path: str | Path) -> list[Document]:
    """
    Load a single PDF file.

    Each PDF page is converted into one LangChain Document.

    Metadata:
        - document: PDF filename
        - page: 1-based page number
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    if file_path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected a PDF file, got: {file_path.suffix}")

    reader = PdfReader(file_path)

    documents: list[Document] = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        if not text.strip():
            continue

        documents.append(
            Document(
                page_content=text,
                metadata={
                    "document": file_path.name,
                    "page": page_number,
                },
            )
        )

    return documents


def load_pdfs(directory: str | Path) -> list[Document]:
    """
    Load all PDF files from a directory.

    Returns:
        A list of Documents where each Document represents one PDF page.
    """
    directory = Path(directory)

    if not directory.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    if not directory.is_dir():
        raise NotADirectoryError(f"Expected directory: {directory}")

    documents: list[Document] = []

    pdf_files = sorted(directory.glob("*.pdf"))

    for pdf_file in pdf_files:
        documents.extend(load_pdf(pdf_file))

    return documents