"""
SECUROXI AI Document Intelligence Stage 4 — Structure Extraction & Semantic Chunking System
Maintains Dual Document Representation:
1. Forensic Document (TextSpans / Layout / Visual Metadata)
2. Semantic Document (Sections / Chunks / Provenance Metadata)
"""

import uuid
import re
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from securoxi.models import TextSpan, Verdict


class ChunkingStrategy(str, Enum):
    SECTION = "SECTION"
    PARAGRAPH = "PARAGRAPH"
    FIXED_TOKEN = "FIXED_TOKEN"
    HYBRID_SEMANTIC = "HYBRID_SEMANTIC"


@dataclass
class DocumentChunk:
    """Represents a semantic chunk of a document traceable back to original layout spans."""
    chunk_id: str
    document_id: str
    tenant_id: str
    section_heading: str
    text: str
    start_page: int = 1
    end_page: int = 1
    bbox: Optional[List[float]] = None
    source_spans: List[TextSpan] = field(default_factory=list)
    token_count: int = 0
    char_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    security_status: str = "SAFE"

    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk into JSON-serializable dictionary."""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "tenant_id": self.tenant_id,
            "section_heading": self.section_heading,
            "text": self.text,
            "start_page": self.start_page,
            "end_page": self.end_page,
            "bbox": self.bbox,
            "token_count": self.token_count,
            "char_count": self.char_count,
            "security_status": self.security_status,
            "source_spans_count": len(self.source_spans),
            "metadata": self.metadata
        }


class SecuroxiChunker:
    """
    Deterministic Semantic Chunker for SECUROXI AI.
    Segments document layout text spans into semantic chunks while preserving exact span provenance.
    """

    def __init__(
        self,
        strategy: ChunkingStrategy = ChunkingStrategy.HYBRID_SEMANTIC,
        max_chunk_tokens: int = 512,
        overlap_tokens: int = 64
    ):
        self.strategy = strategy
        self.max_chunk_tokens = max_chunk_tokens
        self.overlap_tokens = overlap_tokens

    def estimate_tokens(self, text: str) -> int:
        """Rough estimation of token count (~4 characters per token)."""
        if not text:
            return 0
        return max(1, len(text.split()) * 4 // 3)

    def chunk_document(
        self,
        spans: List[TextSpan],
        document_id: str,
        tenant_id: str = "TENANT-DEFAULT",
        security_status: str = "SAFE"
    ) -> List[DocumentChunk]:
        """
        Main entrypoint: Chunk document spans according to configured strategy.
        """
        if not spans:
            return []

        if self.strategy == ChunkingStrategy.SECTION:
            return self._chunk_by_section(spans, document_id, tenant_id, security_status)
        elif self.strategy == ChunkingStrategy.PARAGRAPH:
            return self._chunk_by_paragraph(spans, document_id, tenant_id, security_status)
        elif self.strategy == ChunkingStrategy.FIXED_TOKEN:
            return self._chunk_fixed_tokens(spans, document_id, tenant_id, security_status)
        else:
            return self._chunk_hybrid_semantic(spans, document_id, tenant_id, security_status)

    def _chunk_by_section(
        self,
        spans: List[TextSpan],
        document_id: str,
        tenant_id: str,
        security_status: str
    ) -> List[DocumentChunk]:
        """Groups spans by heading section headers (SUMMARY, EXPERIENCE, EDUCATION, SKILLS)."""
        section_headers = ["WORK EXPERIENCE", "PREFERRED SKILLS", "SUMMARY", "EXPERIENCE", "EDUCATION", "SKILLS", "PROJECTS", "CERTIFICATIONS", "REQUIREMENTS", "RESPONSIBILITIES"]
        chunks: List[DocumentChunk] = []

        current_heading = "HEADER"
        current_spans: List[TextSpan] = []

        for span in spans:
            text_strip = span.text.strip().upper()
            matched_header = next((h for h in section_headers if h in text_strip), None)

            if matched_header and len(span.text.strip()) < 40:
                if current_spans:
                    chunks.append(self._create_chunk(current_spans, current_heading, document_id, tenant_id, security_status))
                current_heading = matched_header
                current_spans = [span]
            else:
                current_spans.append(span)

        if current_spans:
            chunks.append(self._create_chunk(current_spans, current_heading, document_id, tenant_id, security_status))

        return chunks

    def _chunk_by_paragraph(
        self,
        spans: List[TextSpan],
        document_id: str,
        tenant_id: str,
        security_status: str
    ) -> List[DocumentChunk]:
        """Groups spans into paragraph-sized chunks."""
        chunks: List[DocumentChunk] = []
        current_spans: List[TextSpan] = []
        current_chars = 0

        for span in spans:
            current_spans.append(span)
            current_chars += len(span.text)

            if current_chars >= 400 or "\n\n" in span.text:
                chunks.append(self._create_chunk(current_spans, "PARAGRAPH", document_id, tenant_id, security_status))
                current_spans = []
                current_chars = 0

        if current_spans:
            chunks.append(self._create_chunk(current_spans, "PARAGRAPH", document_id, tenant_id, security_status))

        return chunks

    def _chunk_fixed_tokens(
        self,
        spans: List[TextSpan],
        document_id: str,
        tenant_id: str,
        security_status: str
    ) -> List[DocumentChunk]:
        """Fixed token window chunking with sliding overlap."""
        chunks: List[DocumentChunk] = []
        i = 0
        while i < len(spans):
            current_spans: List[TextSpan] = []
            tokens = 0
            j = i
            while j < len(spans) and tokens < self.max_chunk_tokens:
                span_tokens = self.estimate_tokens(spans[j].text)
                current_spans.append(spans[j])
                tokens += span_tokens
                j += 1

            if current_spans:
                chunks.append(self._create_chunk(current_spans, "FIXED_WINDOW", document_id, tenant_id, security_status))

            # Advance by step size subtracting overlap
            step = max(1, len(current_spans) // 2)
            i += step

        return chunks

    def _chunk_hybrid_semantic(
        self,
        spans: List[TextSpan],
        document_id: str,
        tenant_id: str,
        security_status: str
    ) -> List[DocumentChunk]:
        """Hybrid section-aware semantic chunking with token size limits."""
        section_chunks = self._chunk_by_section(spans, document_id, tenant_id, security_status)
        final_chunks: List[DocumentChunk] = []

        for schunk in section_chunks:
            if schunk.token_count <= self.max_chunk_tokens:
                final_chunks.append(schunk)
            else:
                # Split large section into sub-chunks
                sub_chunks = self._chunk_fixed_tokens(schunk.source_spans, document_id, tenant_id, security_status)
                for sub in sub_chunks:
                    sub.section_heading = f"{schunk.section_heading}_SUB"
                    final_chunks.append(sub)

        return final_chunks

    def _create_chunk(
        self,
        spans: List[TextSpan],
        heading: str,
        document_id: str,
        tenant_id: str,
        security_status: str
    ) -> DocumentChunk:
        """Helper to construct a DocumentChunk from spans."""
        chunk_text = "\n".join(s.text for s in spans)
        start_page = min((s.page for s in spans), default=1)
        end_page = max((s.page for s in spans), default=1)
        
        # Calculate bounding box bounds if available
        valid_bboxes = [s.bbox for s in spans if s.bbox and len(s.bbox) == 4]
        combined_bbox = None
        if valid_bboxes:
            x0 = min(b[0] for b in valid_bboxes)
            y0 = min(b[1] for b in valid_bboxes)
            x1 = max(b[2] for b in valid_bboxes)
            y1 = max(b[3] for b in valid_bboxes)
            combined_bbox = [x0, y0, x1, y1]

        char_count = len(chunk_text)
        token_count = self.estimate_tokens(chunk_text)
        chunk_id = f"CHUNK-{uuid.uuid4().hex[:8]}"

        # Preserve security metadata
        has_hidden = any(getattr(s, "is_hidden", False) for s in spans)
        sources = list(set(getattr(s, "source", "NATIVE_PDF") for s in spans))

        metadata = {
            "sources": sources,
            "has_hidden_spans": has_hidden,
            "spans_count": len(spans)
        }

        return DocumentChunk(
            chunk_id=chunk_id,
            document_id=document_id,
            tenant_id=tenant_id,
            section_heading=heading,
            text=chunk_text,
            start_page=start_page,
            end_page=end_page,
            bbox=combined_bbox,
            source_spans=spans,
            token_count=token_count,
            char_count=char_count,
            metadata=metadata,
            security_status=security_status
        )
