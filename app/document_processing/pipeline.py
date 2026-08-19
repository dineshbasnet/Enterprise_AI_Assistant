from __future__ import annotations
import os
import shutil
from sqlalchemy.ext.asyncio import AsyncSession
from app.document_processing.processors import OCREngine, LayoutAnalyzer, FieldExtractor
from app.rag.pipeline import RAGPipeline
from app.database.repositories import DocumentRepository
import logfire


class DocumentPipeline:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ocr = OCREngine()
        self.layout = LayoutAnalyzer()
        self.extractor = FieldExtractor()
        self.rag = RAGPipeline(db)
        self.doc_repo = DocumentRepository(db)

    async def process(self, user_id: str, file_path: str, filename: str) -> dict:
        with logfire.span("document_pipeline.process", filename=filename):
            mime = self._detect_mime(filename)
            doc = await self.doc_repo.create(user_id, filename, file_path, mime)
            await self.doc_repo.update_status(doc.id, "processing")

            try:
                text = await self.ocr.extract_text(file_path)
                layout = await self.layout.analyze(text, file_path)
                fields = await self.extractor.extract(text)
                chunk_count = await self.rag.ingest(doc.id, text, metadata={"filename": filename})
                await self.doc_repo.update_status(doc.id, "completed")
                return {
                    "document_id": doc.id,
                    "filename": filename,
                    "status": "completed",
                    "chunks": chunk_count,
                    "layout": layout,
                    "fields": fields,
                }
            except Exception as e:
                await self.doc_repo.update_status(doc.id, "failed")
                logfire.error("Document processing failed", error=str(e))
                raise

    def _detect_mime(self, filename: str) -> str:
        ext = os.path.splitext(filename)[1].lower()
        return {
            ".pdf": "application/pdf",
            ".txt": "text/plain",
            ".md": "text/markdown",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".csv": "text/csv",
            ".json": "application/json",
        }.get(ext, "application/octet-stream")
