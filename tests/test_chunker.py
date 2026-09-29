from collections import Counter

from app.ingestion.pdf_loader import load_pdfs
from app.ingestion.structure_detector import StructureDetector
from app.ingestion.structure_aware_chunker import StructureAwareChunker


DATA_DIR = "data/documents"


def get_unit_key(chunk):
    metadata = chunk.metadata

    document = metadata.get("document")
    document_type = metadata.get("document_type")

    if document_type == "legal":
        unit = metadata.get("article")
    else:
        unit = metadata.get("level_1")

    return document, unit


def print_chunk_distribution(chunks):
    print("\n" + "=" * 80)
    print("PHÂN PHỐI CHUNK")
    print("=" * 80)

    # =========================================================
    # 1. Tổng quan
    # =========================================================

    print(f"\nTổng số chunk: {len(chunks)}")

    # =========================================================
    # 2. Phân phối kích thước chunk
    # =========================================================

    print("\n[1] PHÂN PHỐI KÍCH THƯỚC CHUNK")

    chunk_sizes = [
        chunk.metadata.get("chunk_size", 0)
        for chunk in chunks
    ]

    ranges = [
        (0, 999),
        (1000, 1499),
        (1500, 1799),
        (1800, 2199),
        (2200, 2999),
        (3000, 3999),
        (4000, 999999),
    ]

    for lower, upper in ranges:

        count = sum(
            lower <= size <= upper
            for size in chunk_sizes
        )

        if count == 0:
            continue

        percentage = (
            count / len(chunk_sizes) * 100
        )

        label = (
            f"{lower}-{upper}"
            if upper != 999999
            else f"{lower}+"
        )

        print(
            f"{label:>12} chars : "
            f"{count:>4} chunks "
            f"({percentage:>5.1f}%)"
        )

    # =========================================================
    # 3. Phân phối số chunk / structural unit
    # =========================================================

    print(
        "\n[2] PHÂN PHỐI SỐ CHUNK / STRUCTURAL UNIT"
    )

    unit_distribution = Counter()
    processed_units = set()

    for chunk in chunks:

        key = get_unit_key(chunk)

        if key in processed_units:
            continue

        processed_units.add(key)

        chunk_count = chunk.metadata.get(
            "chunk_count",
            1,
        )

        unit_distribution[chunk_count] += 1

    total_units = sum(
        unit_distribution.values()
    )

    for chunk_count in sorted(
        unit_distribution
    ):

        count = unit_distribution[
            chunk_count
        ]

        percentage = (
            count / total_units * 100
        )

        print(
            f"{chunk_count:>2} chunk/unit : "
            f"{count:>4} units "
            f"({percentage:>5.1f}%)"
        )

    # =========================================================
    # 4. Các structural unit > 3000
    # =========================================================

    print(
        "\n[3] STRUCTURAL UNIT > 3000 CHARACTERS"
    )

    long_units = []
    processed_units.clear()

    for chunk in chunks:

        key = get_unit_key(chunk)

        if key in processed_units:
            continue

        processed_units.add(key)

        unit_size = chunk.metadata.get(
            "unit_size",
            0,
        )

        if unit_size <= 3000:
            continue

        document, unit = key

        # Lấy toàn bộ chunk thuộc structural unit
        unit_chunks = [
            c
            for c in chunks
            if get_unit_key(c) == key
        ]

        sizes = [
            c.metadata.get(
                "chunk_size",
                0,
            )
            for c in unit_chunks
        ]

        long_units.append(
            (
                document,
                unit,
                unit_size,
                len(unit_chunks),
                sizes,
            )
        )

    print(
        f"Tổng unit > 3000: "
        f"{len(long_units)}"
    )

    for (
        document,
        unit,
        unit_size,
        chunk_count,
        sizes,
    ) in long_units:

        print("\n" + "-" * 70)

        print(
            f"Tài liệu : {document}"
        )

        print(
            f"Đơn vị   : {unit}"
        )

        print(
            f"Unit size: {unit_size}"
        )

        print(
            f"Số chunk : {chunk_count}"
        )

        print(
            f"Kích thước: {sizes}"
        )


def print_sample_chunks(chunks):
    print("\n" + "=" * 80)
    print("MỘT SỐ CHUNK MẪU")
    print("=" * 80)

    # Chỉ lấy tối đa 10 chunk đầu tiên
    for index, chunk in enumerate(
        chunks[:10],
        start=1,
    ):

        metadata = chunk.metadata

        print("\n" + "-" * 80)

        print(
            f"Chunk #{index}"
        )

        print(
            f"Tài liệu : "
            f"{metadata.get('document')}"
        )

        print(
            f"Loại     : "
            f"{metadata.get('document_type')}"
        )

        if metadata.get("document_type") == "legal":

            print(
                f"Điều     : "
                f"{metadata.get('article')}"
            )

        else:

            print(
                f"Cấp 1    : "
                f"{metadata.get('level_1')}"
            )

        print(
            f"Unit size: "
            f"{metadata.get('unit_size')}"
        )

        print(
            f"Chunk    : "
            f"{metadata.get('chunk_index') + 1}/"
            f"{metadata.get('chunk_count')}"
        )

        print(
            f"Chunk size: "
            f"{metadata.get('chunk_size')}"
        )

        preview = (
            chunk.page_content[:500]
            .replace("\n", " ")
        )

        print(
            f"\nPreview:\n{preview}..."
        )


def main():

    # =========================================================
    # 1. Load PDF
    # =========================================================

    documents = load_pdfs(DATA_DIR)

    print(
        f"Tổng số page: "
        f"{len(documents)}"
    )

    # =========================================================
    # 2. Detect structure
    # =========================================================

    detector = StructureDetector()

    structure_nodes = detector.detect(
        documents
    )

    print(
        f"Tổng số structure node: "
        f"{len(structure_nodes)}"
    )

    # =========================================================
    # 3. Chunking
    # =========================================================

    chunker = StructureAwareChunker()

    chunks = chunker.chunk(
        documents=documents,
        structure_nodes=structure_nodes,
    )

    print(
        f"Tổng số chunk: "
        f"{len(chunks)}"
    )

    # =========================================================
    # 4. Distribution
    # =========================================================

    print_chunk_distribution(
        chunks
    )

    # =========================================================
    # 5. Sample
    # =========================================================

    print_sample_chunks(
        chunks
    )


if __name__ == "__main__":
    main()