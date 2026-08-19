from __future__ import annotations
import logfire


class OCREngine:
    """PaddleOCR placeholder — swap implementation when real model is available."""

    async def extract_text(self, file_path: str) -> str:
        with logfire.span("ocr.extract_text", file_path=file_path):
            import os
            ext = os.path.splitext(file_path)[1].lower()
            if ext in (".txt", ".md"):
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            if ext == ".pdf":
                return await self._read_pdf(file_path)
            return f"[OCR placeholder: would process {file_path} with PaddleOCR]"

    async def _read_pdf(self, file_path: str) -> str:
        try:
            import fitz
            doc = fitz.open(file_path)
            return "\n".join(page.get_text() for page in doc)
        except ImportError:
            return "[PDF extraction requires PyMuPDF — install with: pip install pymupdf]"


class LayoutAnalyzer:
    """LayoutLMv3 placeholder — swap implementation when real model is available."""

    async def analyze(self, text: str, file_path: str | None = None) -> dict:
        with logfire.span("layout.analyze"):
            return {
                "sections": [{"type": "body", "content": text}],
                "tables": [],
                "headers": [],
            }


class FieldExtractor:
    """Extracts structured fields from document text using LLM."""

    async def extract(self, text: str, schema: dict | None = None) -> dict:
        with logfire.span("field_extractor.extract"):
            from app.core.llm import get_llm
            llm = get_llm(temperature=0.0)
            result = await llm.ainvoke([
                ("system", "Extract key fields from this document. Return a JSON object with field names and values."),
                ("human", text[:4000]),
            ])
            return {"raw_extraction": result.content}
