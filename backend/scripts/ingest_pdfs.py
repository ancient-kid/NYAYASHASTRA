"""
PDF Ingestion Script - Indexes PDFs from data copy folder with domain metadata
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def ingest_pdfs():
    """Ingest all PDFs from data copy folder into vector store."""
    
    print("\n" + "="*50)
    print("PDF DOCUMENT INGESTION")
    print("="*50)
    
    try:
        from app.services.pdf_ingestion import get_pdf_ingestion_service
        from app.services.vector_store import get_vector_store
        
        # Initialize services
        pdf_service = get_pdf_ingestion_service()
        vector_store = await get_vector_store()
        
        print(f"\nScanning folder: {pdf_service.data_dir}")
        
        # Ingest all documents
        documents = pdf_service.ingest_all_documents()
        
        if not documents:
            print("No PDF documents found to ingest.")
            return 0
        
        print(f"\nFound {len(documents)} document chunks")
        
        # Show domain breakdown
        domain_counts = {}
        for doc in documents:
            domain = doc.get("domain", "unknown")
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        print("\nDomain breakdown:")
        for domain, count in domain_counts.items():
            print(f"  - {domain}: {count} chunks")
        
        # Add to vector store
        print("\nIndexing documents in vector store...")
        await vector_store.add_documents(documents)
        
        print("\n" + "="*50)
        print("INGESTION COMPLETE")
        print("="*50)
        print(f"Total chunks indexed: {len(documents)}")
        print("="*50)
        
        return len(documents)
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        return 0


if __name__ == "__main__":
    result = asyncio.run(ingest_pdfs())
    print(f"\nIngested {result} document chunks")
