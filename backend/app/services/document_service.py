"""
NyayaShastra - Document Service
Handles PDF upload, parsing, and summarization.
"""

import os
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import asyncio

logger = logging.getLogger(__name__)

try:
    import pdfplumber
    PDF_AVAILABLE = True
    logger.info("pdfplumber successfully loaded")
except ImportError as e:
    PDF_AVAILABLE = False
    logger.warning(f"pdfplumber NOT available: {e}")

try:
    from PyPDF2 import PdfReader
    PYPDF2_AVAILABLE = True
    logger.info("PyPDF2 successfully loaded")
except ImportError as e:
    PYPDF2_AVAILABLE = False
    logger.warning(f"PyPDF2 NOT available: {e}")

from app.config import settings
from app.agents.summarization_agent import SummarizationAgent



class DocumentService:
    """Service for document processing and summarization."""
    
    def __init__(self, upload_dir: str = "./uploads"):
        self.upload_dir = upload_dir
        self.summarization_agent = SummarizationAgent()
        
        # Ensure upload directory exists
        os.makedirs(upload_dir, exist_ok=True)
        
        # In-memory document store (replace with DB in production)
        self.documents: Dict[str, Dict[str, Any]] = {}
    
    async def upload_document(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Upload and store a document."""
        document_id = str(uuid.uuid4())
        
        # Save file
        file_path = os.path.join(self.upload_dir, f"{document_id}_{filename}")
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Create document record
        document = {
            "document_id": document_id,
            "filename": filename,
            "file_path": file_path,
            "file_size": len(file_content),
            "status": "pending",
            "uploaded_at": datetime.now().isoformat(),
            "summary": None,
            "error_message": None
        }
        
        self.documents[document_id] = document
        
        # Start async processing
        asyncio.create_task(self._process_document(document_id))
        
        return {
            "document_id": document_id,
            "filename": filename,
            "status": "pending",
            "message": "Document uploaded successfully. Processing started."
        }
    
    async def get_document_status(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document processing status."""
        document = self.documents.get(document_id)
        
        if not document:
            return None
        
        # Calculate progress based on status
        progress_map = {
            "pending": 10,
            "extracting": 30,
            "analyzing": 60,
            "summarizing": 80,
            "completed": 100,
            "error": 0
        }
        
        return {
            "document_id": document_id,
            "filename": document["filename"],
            "status": document["status"],
            "progress": progress_map.get(document["status"], 0),
            "summary": document.get("summary"),
            "error_message": document.get("error_message")
        }
    
    async def _process_document(self, document_id: str):
        """Process document in background."""
        document = self.documents.get(document_id)
        if not document:
            return
        
        try:
            # Update status to extracting
            document["status"] = "extracting"
            await asyncio.sleep(0.5)  # Simulate processing time
            
            # Extract text from PDF
            text = await self._extract_text(document["file_path"])
            
            if not text:
                raise ValueError("Could not extract text from document")
            
            # Update status to analyzing
            document["status"] = "analyzing"
            await asyncio.sleep(0.5)
            
            # Analyze document type
            doc_type = self._detect_document_type(text)
            
            # Update status to summarizing
            document["status"] = "summarizing"
            await asyncio.sleep(0.5)
            
            # Generate summary
            summary = await self.summarization_agent.summarize_document(text, doc_type)
            
            # Store summary
            document["summary"] = summary
            document["status"] = "completed"
            document["processed_at"] = datetime.now().isoformat()
            
            logger.info(f"Document {document_id} processed successfully")
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            document["status"] = "error"
            document["error_message"] = str(e)
            file_path = document.get("file_path")
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError as cleanup_error:
                    logger.warning(f"Failed to clean up {file_path}: {cleanup_error}")
    
    async def _extract_text(self, file_path: str) -> str:
        """Extract text from PDF file."""
        text = ""
        
        # Late-bind check for libraries in case of reload issues
        global PDF_AVAILABLE, PYPDF2_AVAILABLE
        if not PDF_AVAILABLE:
            try:
                import pdfplumber
                PDF_AVAILABLE = True
            except ImportError:
                pass
        
        if not PYPDF2_AVAILABLE:
            try:
                from PyPDF2 import PdfReader
                PYPDF2_AVAILABLE = True
            except ImportError:
                pass
        
        try:
            if PDF_AVAILABLE:
                # Use pdfplumber for better extraction
                import pdfplumber
                with pdfplumber.open(file_path) as pdf:
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n\n"
            
            elif PYPDF2_AVAILABLE:
                # Fallback to PyPDF2
                from PyPDF2 import PdfReader
                reader = PdfReader(file_path)
                for page in reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
            
            else:
                raise ImportError("No PDF library available. Please run: pip install pdfplumber pypdf2")
            
        except Exception as e:
            logger.error(f"Error extracting text: {e}")
            raise
        
        return text.strip()
    
    def _detect_document_type(self, text: str) -> str:
        """Detect the type of legal document."""
        text_lower = text.lower()
        
        if "judgment" in text_lower or "order" in text_lower:
            if "supreme court" in text_lower:
                return "supreme_court_judgment"
            elif "high court" in text_lower:
                return "high_court_judgment"
            else:
                return "judgment"
        
        if "fir" in text_lower or "first information report" in text_lower:
            return "fir"
        
        if "charge sheet" in text_lower or "chargesheet" in text_lower:
            return "chargesheet"
        
        if "petition" in text_lower:
            return "petition"
        
        if "contract" in text_lower or "agreement" in text_lower:
            return "contract"
        
        if "notice" in text_lower:
            return "notice"
        
        return "legal_document"
    
    async def find_citation_in_document(
        self, 
        document_id: str, 
        excerpt: str
    ) -> Dict[str, Any]:
        """
        Find and highlight a citation excerpt in a document.
        Returns the document content with highlight coordinates.
        """
        document = self.documents.get(document_id)
        
        if not document:
            return {
                "found": False,
                "error": "Document not found"
            }
        
        content = document.get("content", "")
        if not content:
            return {
                "found": False,
                "error": "Document content not available"
            }
        
        # Normalize text for fuzzy matching
        normalized_excerpt = excerpt.lower().strip()
        normalized_content = content.lower()
        
        # Try exact match first
        start_idx = normalized_content.find(normalized_excerpt)
        
        if start_idx != -1:
            return {
                "found": True,
                "startIndex": start_idx,
                "endIndex": start_idx + len(excerpt),
                "exactMatch": True,
                "confidence": 100,
                "documentContent": content,
                "highlightedSections": [{
                    "text": content[start_idx:start_idx + len(excerpt)],
                    "startIndex": start_idx,
                    "endIndex": start_idx + len(excerpt),
                    "confidence": 100
                }]
            }
        
        # Try fuzzy matching - find the best matching substring
        from difflib import SequenceMatcher
        
        best_match = None
        best_ratio = 0.0
        window_size = len(excerpt) + 50  # Allow for some variance
        
        for i in range(0, len(content) - len(excerpt), 20):
            window = content[i:i + window_size]
            ratio = SequenceMatcher(None, excerpt.lower(), window.lower()).ratio()
            
            if ratio > best_ratio and ratio > 0.7:  # 70% similarity threshold
                best_ratio = ratio
                best_match = {
                    "text": window[:len(excerpt)],
                    "startIndex": i,
                    "endIndex": i + len(excerpt),
                    "confidence": int(ratio * 100)
                }
        
        if best_match:
            return {
                "found": True,
                "exactMatch": False,
                "confidence": best_match["confidence"],
                "documentContent": content,
                "highlightedSections": [best_match]
            }
        
        return {
            "found": False,
            "error": "Citation excerpt not found in document",
            "documentContent": content,
            "highlightedSections": []
        }
    
    async def extract_text_with_coordinates(self, document_id: str) -> Dict[str, Any]:
        """
        Extract text with word-level coordinates from a PDF document.
        Useful for precise highlighting in PDF viewers.
        """
        document = self.documents.get(document_id)
        
        if not document:
            return {"error": "Document not found", "words": []}
        
        file_path = document.get("file_path", "")
        
        if not file_path.lower().endswith('.pdf'):
            return {"error": "Only PDF files support coordinate extraction", "words": []}
        
        if not PDF_AVAILABLE:
            return {"error": "pdfplumber not available", "words": []}
        
        try:
            words_with_coords = []
            
            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    words = page.extract_words()
                    
                    for word in words:
                        words_with_coords.append({
                            "text": word["text"],
                            "page": page_num,
                            "x0": word["x0"],
                            "y0": word["top"],
                            "x1": word["x1"],
                            "y1": word["bottom"]
                        })
            
            return {
                "success": True,
                "totalPages": len(pdf.pages) if 'pdf' in dir() else 0,
                "words": words_with_coords
            }
            
        except Exception as e:
            logger.error(f"Error extracting coordinates: {e}")
            return {"error": str(e), "words": []}
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete a document."""
        document = self.documents.get(document_id)
        
        if not document:
            return False
        
        try:
            # Delete file
            if os.path.exists(document["file_path"]):
                os.remove(document["file_path"])
            
            # Remove from store
            del self.documents[document_id]
            
            return True
        except Exception as e:
            logger.error(f"Error deleting document: {e}")
            return False


# Singleton
_document_service: Optional[DocumentService] = None


def get_document_service() -> DocumentService:
    """Get or create document service singleton."""
    global _document_service
    if _document_service is None:
        _document_service = DocumentService()
    return _document_service
