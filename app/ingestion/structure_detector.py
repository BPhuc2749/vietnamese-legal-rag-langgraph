import re

from langchain_core.documents import Document

from app.schemas.structure import StructureNode


class StructureDetector:
    """
    Phân tích cấu trúc tài liệu.

    V1 hỗ trợ 3 loại:
    - LEGAL: văn bản pháp luật
    - NUMBERED: tài liệu có cấu trúc đánh số
    - UNSTRUCTURED: không phát hiện được cấu trúc rõ ràng
    """

    # =========================================================
    # Document type detection
    # =========================================================

    LEGAL_CHAPTER_PATTERN = re.compile(
        r"^\s*Chương\s+[IVXLCDM]+\b",
        re.IGNORECASE,
    )

    # =========================================================
    # LEGAL structure
    # =========================================================

    ARTICLE_PATTERN = re.compile(
        r"^\s*Điều\s+(\d+)\b",
        re.IGNORECASE,
    )

    CLAUSE_PATTERN = re.compile(
        r"^\s*(\d+)[.)]\s+"
    )

    POINT_PATTERN = re.compile(
        r"^\s*([a-zđ])[\.)]\s+",
        re.IGNORECASE,
    )

    # =========================================================
    # NUMBERED structure
    # =========================================================

    ROMAN_PATTERN = re.compile(
        r"^\s*([IVXLCDM]+)[.)]?\s+",
        re.IGNORECASE,
    )

    NUMBERED_PATTERN = re.compile(
        r"^\s*(\d+)[.)]\s+"
    )

    DECIMAL_PATTERN = re.compile(
        r"^\s*(\d+\.\d+)[.)]?\s+"
    )

    LETTER_PATTERN = re.compile(
        r"^\s*([a-zđ])[\.)]\s+",
        re.IGNORECASE,
    )

    # =========================================================
    # Public
    # =========================================================

    def detect(self, documents: list[Document]) -> list[StructureNode]:
        """
        Phân tích cấu trúc của các page thuộc nhiều PDF.

        Mỗi PDF sẽ được xác định document type riêng trước,
        sau đó áp dụng rule tương ứng.
        """

        grouped_documents = self._group_by_document(documents)

        nodes: list[StructureNode] = []

        for document_name, document_pages in grouped_documents.items():

            document_type = self._detect_document_type(
                document_pages
            )

            if document_type == "LEGAL":
                nodes.extend(
                    self._detect_legal_structure(
                        document_pages
                    )
                )

            elif document_type == "NUMBERED":
                nodes.extend(
                    self._detect_numbered_structure(
                        document_pages
                    )
                )

            # UNSTRUCTURED:
            # Không cố gán structure.

        return nodes

    # =========================================================
    # Document type
    # =========================================================

    def _detect_document_type(
        self,
        documents: list[Document],
    ) -> str:
        """
        Kiểm tra 5 dòng đầu tiên có nội dung.

        Nếu xuất hiện:
            Chương + số La Mã

        → LEGAL

        Nếu không:
        → NUMBERED

        NUMBERED ở V1 được dùng cho các tài liệu
        có cấu trúc đánh số như 1, 1.1, a, I...
        """

        first_lines: list[str] = []

        for document in documents:
            for line in document.page_content.splitlines():
                line = line.strip()

                if line:
                    first_lines.append(line)

                if len(first_lines) >= 5:
                    break

            if len(first_lines) >= 5:
                break

        for line in first_lines:
            if self.LEGAL_CHAPTER_PATTERN.match(line):
                return "LEGAL"

        return "NUMBERED"

    # =========================================================
    # LEGAL
    # =========================================================

    def _detect_legal_structure(
        self,
        documents: list[Document],
    ) -> list[StructureNode]:

        nodes: list[StructureNode] = []

        for document in documents:

            document_name = document.metadata.get(
                "document",
                "",
            )

            page = document.metadata.get("page")

            if page is None:
                continue

            for line_index, line in enumerate(
                document.page_content.splitlines()
            ):
                line = line.strip()

                if not line:
                    continue

                # Chương
                chapter_match = self.LEGAL_CHAPTER_PATTERN.match(
                    line
                )

                if chapter_match:
                    nodes.append(
                        StructureNode(
                            document=document_name,
                            level="chapter",
                            value=chapter_match.group(0).strip(),
                            page=page,
                            line_index=line_index,
                        )
                    )
                    continue

                # Điều
                article_match = self.ARTICLE_PATTERN.match(
                    line
                )

                if article_match:
                    nodes.append(
                        StructureNode(
                            document=document_name,
                            level="article",
                            value=f"Điều {article_match.group(1)}",
                            page=page,
                            line_index=line_index,
                        )
                    )
                    continue

                # Khoản
                clause_match = self.CLAUSE_PATTERN.match(
                    line
                )

                if clause_match:
                    nodes.append(
                        StructureNode(
                            document=document_name,
                            level="clause",
                            value=clause_match.group(1),
                            page=page,
                            line_index=line_index,
                        )
                    )
                    continue

                # Điểm
                point_match = self.POINT_PATTERN.match(
                    line
                )

                if point_match:
                    nodes.append(
                        StructureNode(
                            document=document_name,
                            level="point",
                            value=point_match.group(1),
                            page=page,
                            line_index=line_index,
                        )
                    )

        return nodes

    # =========================================================
    # NUMBERED
    # =========================================================

    def _detect_numbered_structure(
        self,
        documents: list[Document],
    ) -> list[StructureNode]:

        nodes: list[StructureNode] = []

        for document in documents:

            document_name = document.metadata.get(
                "document",
                "",
            )

            page = document.metadata.get("page")

            if page is None:
                continue

            for line_index, line in enumerate(
                document.page_content.splitlines()
            ):
                line = line.strip()

                if not line:
                    continue

                # 1.1 / 1.2 / 4.5
                decimal_match = self.DECIMAL_PATTERN.match(
                    line
                )

                if decimal_match:
                    nodes.append(
                        StructureNode(
                            document=document_name,
                            level="level_2",
                            value=decimal_match.group(1),
                            page=page,
                            line_index=line_index,
                        )
                    )
                    continue

                # a. / b. / c. hoặc a) / b) / c)
                letter_match = self.LETTER_PATTERN.match(
                    line
                )

                if letter_match:
                    nodes.append(
                        StructureNode(
                            document=document_name,
                            level="level_3",
                            value=letter_match.group(1),
                            page=page,
                            line_index=line_index,
                        )
                    )
                    continue

                # I. / II. / III.
                roman_match = self.ROMAN_PATTERN.match(
                    line
                )

                if roman_match:
                    nodes.append(
                        StructureNode(
                            document=document_name,
                            level="level_1",
                            value=roman_match.group(1),
                            page=page,
                            line_index=line_index,
                        )
                    )
                    continue

                # 1. / 2. / 3.
                numbered_match = self.NUMBERED_PATTERN.match(
                    line
                )

                if numbered_match:
                    nodes.append(
                        StructureNode(
                            document=document_name,
                            level="level_1",
                            value=numbered_match.group(1),
                            page=page,
                            line_index=line_index,
                        )
                    )

        return nodes

    # =========================================================
    # Utils
    # =========================================================

    @staticmethod
    def _group_by_document(
        documents: list[Document],
    ) -> dict[str, list[Document]]:

        grouped: dict[str, list[Document]] = {}

        for document in documents:

            document_name = document.metadata.get(
                "document",
                "",
            )

            grouped.setdefault(
                document_name,
                [],
            ).append(document)

        return grouped