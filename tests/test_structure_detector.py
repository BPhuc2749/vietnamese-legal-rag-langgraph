from pathlib import Path

from app.ingestion.pdf_loader import load_pdfs
from app.ingestion.structure_detector import StructureDetector


DATA_DIR = Path("data/documents")


LEVEL_NAMES = {
    "chapter": "Chương",
    "article": "Điều",
    "clause": "Khoản",
    "point": "Điểm",
    "level_1": "Cấp 1",
    "level_2": "Cấp 2",
    "level_3": "Cấp 3",
    "level_4": "Cấp 4",
}


def main():
    documents = load_pdfs(DATA_DIR)

    detector = StructureDetector()

    nodes = detector.detect(documents)

    print("=" * 80)
    print("KẾT QUẢ PHÂN TÍCH CẤU TRÚC")
    print("=" * 80)

    print(f"Tổng số trang: {len(documents)}")
    print(f"Tổng số cấu trúc phát hiện: {len(nodes)}")

    print("\n" + "=" * 80)
    print("DANH SÁCH CẤU TRÚC")
    print("=" * 80)

    for node in nodes[:100]:
        level_name = LEVEL_NAMES.get(node.level, node.level)

        print(
            f"Tài liệu : {node.document}\n"
            f"Trang    : {node.page}\n"
            f"Dòng     : {node.line_index}\n"
            f"Loại     : {level_name}\n"
            f"Giá trị  : {node.value}\n"
            f"{'-' * 80}"
        )


if __name__ == "__main__":
    main()