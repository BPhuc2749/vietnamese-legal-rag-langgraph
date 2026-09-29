from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.schemas.structure import StructureNode


class StructureAwareChunker:
    """
    Structure-aware chunker V1.

    LEGAL:
        Structural unit = Điều

    NUMBERED:
        Structural unit = Cấp 1

    Chunking rule:
        - Structural unit <= 3000 characters:
            giữ nguyên 1 chunk.
        - Structural unit > 3000 characters:
            dùng RecursiveCharacterTextSplitter.
        - Recursive splitter:
            chunk_size = 1600
            chunk_overlap = 150

    Structural boundary luôn được ưu tiên:
        - Không chunk xuyên qua Điều.
        - Không chunk xuyên qua Cấp 1.
    """

    UNIT_THRESHOLD = 2500
    CHUNK_SIZE = 1300
    CHUNK_OVERLAP = 150

    def __init__(
        self,
        unit_threshold: int = UNIT_THRESHOLD,
        chunk_size: int = CHUNK_SIZE,
        chunk_overlap: int = CHUNK_OVERLAP,
    ):
        self.unit_threshold = unit_threshold
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=[
                "\n\n",
                "\n",
                ". ",
                "; ",
                ", ",
                " ",
                "",
            ],
        )

    # =========================================================
    # PUBLIC
    # =========================================================

    def chunk(
        self,
        documents: list[Document],
        structure_nodes: list[StructureNode],
    ) -> list[Document]:

        grouped_documents = self._group_documents(
            documents
        )

        grouped_nodes = self._group_structure_nodes(
            structure_nodes
        )

        final_chunks: list[Document] = []

        for document_name, pages in grouped_documents.items():

            nodes = grouped_nodes.get(
                document_name,
                [],
            )

            if not nodes:
                final_chunks.extend(
                    self._fallback_chunk(pages)
                )
                continue

            document_type = self._detect_document_type(
                nodes
            )

            if document_type == "legal":

                chunks = self._chunk_legal_document(
                    pages,
                    nodes,
                )

            else:

                chunks = self._chunk_numbered_document(
                    pages,
                    nodes,
                )

            final_chunks.extend(chunks)

        return final_chunks

    # =========================================================
    # LEGAL
    # =========================================================

    def _chunk_legal_document(
        self,
        pages: list[Document],
        nodes: list[StructureNode],
    ) -> list[Document]:

        article_nodes = sorted(
            [
                node
                for node in nodes
                if node.level == "article"
            ],
            key=lambda node: (
                node.page,
                node.line_index,
            ),
        )

        chunks: list[Document] = []

        for index, article_node in enumerate(
            article_nodes
        ):

            next_article = (
                article_nodes[index + 1]
                if index + 1 < len(article_nodes)
                else None
            )

            (
                unit_text,
                page_start,
                page_end,
            ) = self._extract_structural_unit(
                pages=pages,
                start_node=article_node,
                end_node=next_article,
            )

            if not unit_text:
                continue

            metadata = self._build_legal_metadata(
                article_node=article_node,
                nodes=nodes,
                page_start=page_start,
                page_end=page_end,
            )

            chunks.extend(
                self._split_structural_unit(
                    text=unit_text,
                    metadata=metadata,
                )
            )

        return chunks

    # =========================================================
    # NUMBERED
    # =========================================================

    def _chunk_numbered_document(
        self,
        pages: list[Document],
        nodes: list[StructureNode],
    ) -> list[Document]:

        level_1_nodes = sorted(
            [
                node
                for node in nodes
                if node.level == "level_1"
            ],
            key=lambda node: (
                node.page,
                node.line_index,
            ),
        )

        chunks: list[Document] = []

        for index, node in enumerate(
            level_1_nodes
        ):

            next_node = (
                level_1_nodes[index + 1]
                if index + 1 < len(level_1_nodes)
                else None
            )

            (
                unit_text,
                page_start,
                page_end,
            ) = self._extract_structural_unit(
                pages=pages,
                start_node=node,
                end_node=next_node,
            )

            if not unit_text:
                continue

            metadata = self._build_numbered_metadata(
                node=node,
                page_start=page_start,
                page_end=page_end,
            )

            chunks.extend(
                self._split_structural_unit(
                    text=unit_text,
                    metadata=metadata,
                )
            )

        return chunks

    # =========================================================
    # STRUCTURAL UNIT EXTRACTION
    # =========================================================

    def _extract_structural_unit(
        self,
        pages: list[Document],
        start_node: StructureNode,
        end_node: StructureNode | None,
    ) -> tuple[str, int, int]:

        start_page = start_node.page
        start_line = start_node.line_index

        if end_node:
            end_page = end_node.page
            end_line = end_node.line_index
        else:
            end_page = pages[-1].metadata.get(
                "page",
                start_page,
            )
            end_line = None

        page_lookup = {
            page.metadata.get("page"): page
            for page in pages
        }

        selected_lines: list[str] = []

        for page_number in sorted(page_lookup):

            if page_number < start_page:
                continue

            if page_number > end_page:
                break

            page = page_lookup[page_number]

            lines = page.page_content.splitlines()

            # Start và end cùng page
            if (
                page_number == start_page
                and page_number == end_page
            ):

                lines = lines[
                    start_line:end_line
                    if end_line is not None
                    else None
                ]

            # Start page
            elif page_number == start_page:

                lines = lines[start_line:]

            # End page
            elif (
                page_number == end_page
                and end_line is not None
            ):

                lines = lines[:end_line]

            # Middle page
            # Giữ toàn bộ lines.

            selected_lines.extend(lines)

        text = "\n".join(
            line.rstrip()
            for line in selected_lines
        )

        return (
            text.strip(),
            start_page,
            end_page,
        )

    # =========================================================
    # SPLIT STRUCTURAL UNIT
    # =========================================================

    def _split_structural_unit(
        self,
        text: str,
        metadata: dict,
    ) -> list[Document]:

        text = text.strip()

        if not text:
            return []

        unit_size = len(text)

        # -----------------------------------------------------
        # Structural unit đủ nhỏ
        # -----------------------------------------------------

        if unit_size <= self.unit_threshold:

            return [
                Document(
                    page_content=text,
                    metadata={
                        **metadata,
                        "chunk_index": 0,
                        "chunk_count": 1,
                        "chunk_size": unit_size,
                        "unit_size": unit_size,
                    },
                )
            ]

        # -----------------------------------------------------
        # Structural unit quá dài
        # -----------------------------------------------------

        split_texts = self.text_splitter.split_text(
            text
        )

        documents: list[Document] = []

        for index, chunk_text in enumerate(
            split_texts
        ):

            documents.append(
                Document(
                    page_content=chunk_text,
                    metadata={
                        **metadata,
                        "chunk_index": index,
                        "chunk_count": len(
                            split_texts
                        ),
                        "chunk_size": len(
                            chunk_text
                        ),
                        "unit_size": unit_size,
                    },
                )
            )

        return documents

    # =========================================================
    # LEGAL METADATA
    # =========================================================

    def _build_legal_metadata(
        self,
        article_node: StructureNode,
        nodes: list[StructureNode],
        page_start: int,
        page_end: int,
    ) -> dict:

        chapter = self._find_parent_node(
            current_node=article_node,
            nodes=nodes,
            level="chapter",
        )

        return {
            "document": article_node.document,
            "document_type": "legal",
            "chapter": (
                chapter.value
                if chapter
                else None
            ),
            "article": article_node.value,
            "page_start": page_start,
            "page_end": page_end,
        }

    # =========================================================
    # NUMBERED METADATA
    # =========================================================

    @staticmethod
    def _build_numbered_metadata(
        node: StructureNode,
        page_start: int,
        page_end: int,
    ) -> dict:

        return {
            "document": node.document,
            "document_type": "numbered",
            "level_1": node.value,
            "page_start": page_start,
            "page_end": page_end,
        }

    # =========================================================
    # FIND PARENT
    # =========================================================

    @staticmethod
    def _find_parent_node(
        current_node: StructureNode,
        nodes: list[StructureNode],
        level: str,
    ) -> StructureNode | None:

        candidates = [
            node
            for node in nodes
            if (
                node.document
                == current_node.document
                and node.level == level
                and (
                    node.page < current_node.page
                    or (
                        node.page
                        == current_node.page
                        and node.line_index
                        < current_node.line_index
                    )
                )
            )
        ]

        if not candidates:
            return None

        candidates.sort(
            key=lambda node: (
                node.page,
                node.line_index,
            )
        )

        return candidates[-1]

    # =========================================================
    # DOCUMENT TYPE
    # =========================================================

    @staticmethod
    def _detect_document_type(
        nodes: list[StructureNode],
    ) -> str:

        if any(
            node.level == "article"
            for node in nodes
        ):
            return "legal"

        return "numbered"

    # =========================================================
    # GROUP DOCUMENTS
    # =========================================================

    @staticmethod
    def _group_documents(
        documents: list[Document],
    ) -> dict[str, list[Document]]:

        grouped: dict[
            str,
            list[Document],
        ] = {}

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

    # =========================================================
    # GROUP STRUCTURE NODES
    # =========================================================

    @staticmethod
    def _group_structure_nodes(
        nodes: list[StructureNode],
    ) -> dict[str, list[StructureNode]]:

        grouped: dict[
            str,
            list[StructureNode],
        ] = {}

        for node in nodes:

            grouped.setdefault(
                node.document,
                [],
            ).append(node)

        return grouped

    # =========================================================
    # FALLBACK
    # =========================================================

    def _fallback_chunk(
        self,
        pages: list[Document],
    ) -> list[Document]:

        text = "\n\n".join(
            page.page_content.strip()
            for page in pages
            if page.page_content.strip()
        )

        if not text:
            return []

        metadata = {
            "document": pages[0].metadata.get(
                "document",
                "",
            ),
            "document_type": "unstructured",
            "page_start": pages[0].metadata.get(
                "page"
            ),
            "page_end": pages[-1].metadata.get(
                "page"
            ),
        }

        return self._split_structural_unit(
            text=text,
            metadata=metadata,
        )