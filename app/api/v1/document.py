from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.connection import get_db
from app.document_processing.pipeline import DocumentPipeline
from app.database.repositories import DocumentRepository
import os
import uuid
import logfire

router = APIRouter(prefix="/documents", tags=["Documents"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_document(
    user_id: str = "anonymous",
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    with logfire.span("api.upload_document", filename=file.filename):
        ext = os.path.splitext(file.filename or "file")[1]
        file_path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4()}{ext}")
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        pipeline = DocumentPipeline(db)
        result = await pipeline.process(user_id, file_path, file.filename or "file")
        return result


@router.get("/")
async def list_documents(user_id: str = "anonymous", db: AsyncSession = Depends(get_db)):
    repo = DocumentRepository(db)
    docs = await repo.get_by_user(user_id)
    return [
        {"id": d.id, "filename": d.filename, "status": d.status, "created_at": str(d.created_at)}
        for d in docs
    ]
