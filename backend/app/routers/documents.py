import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List
from backend.app.config import UPLOAD_DIR
from backend.app.models.schemas import (
    DocumentResponse, DocumentQueryRequest, DocumentQueryResponse, StudyGuideResponse
)
from backend.app.services.rag_service import rag_service

router = APIRouter(prefix="/api/documents", tags=["documents"])

@router.post("/upload", response_model=DocumentResponse)
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
    saved_path = UPLOAD_DIR / unique_filename

    try:
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        doc_resp = rag_service.process_pdf(saved_path, file.filename)
        return doc_resp
    except Exception as e:
        if saved_path.exists():
            saved_path.unlink()
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@router.get("", response_model=List[DocumentResponse])
def get_all_documents():
    return rag_service.list_documents()

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document_details(document_id: int):
    doc = rag_service.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.post("/{document_id}/query", response_model=DocumentQueryResponse)
async def query_document(document_id: int, req: DocumentQueryRequest):
    try:
        return await rag_service.query_document(document_id, req.query, top_k=req.top_k or 4)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{document_id}/study-guide", response_model=StudyGuideResponse)
def get_study_guide(document_id: int):
    try:
        return rag_service.generate_study_guide(document_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{document_id}")
def delete_document(document_id: int):
    success = rag_service.delete_document(document_id)
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted", "id": document_id}

