"""
NyayaShastra - Documents API Routes
Handles document upload and summarization.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

from app.schemas import DocumentUploadResponse, DocumentStatusResponse
from app.services.document_service import get_document_service

router = APIRouter(prefix="/api/documents", tags=["documents"])


class CitationHighlightRequest(BaseModel):
    """Request model for citation highlighting."""
    document_id: str
    excerpt: str


class CitationHighlightResponse(BaseModel):
    """Response model for citation highlighting."""
    found: bool
    exactMatch: Optional[bool] = None
    confidence: Optional[int] = None
    documentContent: Optional[str] = None
    highlightedSections: Optional[list] = None
    error: Optional[str] = None


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a legal document for AI analysis and summarization.
    Supports PDF files (court orders, judgments, FIRs, legal notices).
    """
    # Validate file type
    allowed_extensions = ('.pdf', '.doc', '.docx', '.txt')
    if not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(
            status_code=400, 
            detail="Supported formats: PDF, DOC, DOCX, TXT"
        )
    
    # Check file size (10MB limit)
    file_content = await file.read()
    if len(file_content) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 10MB limit"
        )
    
    # Upload and process
    document_service = get_document_service()
    result = await document_service.upload_document(file_content, file.filename)
    
    return result


@router.post("/highlight", response_model=CitationHighlightResponse)
async def highlight_citation(request: CitationHighlightRequest):
    """
    Find and highlight a citation excerpt within an uploaded document.
    Used for Advanced Trust & Verification feature.
    """
    document_service = get_document_service()
    result = await document_service.find_citation_in_document(
        request.document_id, 
        request.excerpt
    )
    
    return result


@router.get("/coordinates/{document_id}")
async def get_document_coordinates(document_id: str):
    """
    Extract text with word-level coordinates from a PDF document.
    Enables precise highlighting in PDF viewers.
    """
    document_service = get_document_service()
    result = await document_service.extract_text_with_coordinates(document_id)
    
    if "error" in result and not result.get("words"):
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@router.get("/status/{document_id}", response_model=DocumentStatusResponse)
async def get_document_status(document_id: str):
    """Get the processing status and summary of an uploaded document."""
    document_service = get_document_service()
    status = await document_service.get_document_status(document_id)
    
    if not status:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return status


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete an uploaded document."""
    document_service = get_document_service()
    success = await document_service.delete_document(document_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return {"message": "Document deleted successfully"}


@router.get("/download/{filename}")
async def download_pdf_document(filename: str):
    """
    Download or view a PDF document from the data directories.
    Searches for the file name in all subfolders of backend/data/.
    """
    data_dir = Path(__file__).parent.parent.parent / "data"
    
    # Search for file
    for path in data_dir.glob(f"**/{filename}"):
        if path.is_file():
            return FileResponse(
                path,
                media_type="application/pdf",
                filename=filename
            )
            
    # Also check uploads directory in case it's an uploaded file
    uploads_dir = Path("./uploads")
    for path in uploads_dir.glob(f"**/*{filename}"):
        if path.is_file():
            return FileResponse(
                path,
                media_type="application/pdf",
                filename=filename
            )
            
    raise HTTPException(status_code=404, detail=f"PDF document '{filename}' not found")
