"""
NyayaShastra - Hybrid Data Ingestion Script
Ingests:
1. PDFs into ChromaDB with folder-based category metadata
2. IPC-BNS CSV into NeonDB PostgreSQL table
"""

import os
import sys
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pdfplumber
from sqlalchemy import create_engine, Column, String, Text, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import insert

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

DATA_DIR = Path(__file__).parent.parent / "data"
CHROMA_PERSIST_DIR = Path(__file__).parent.parent / "chroma_db"

# Load from environment
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "")
CHUNK_SIZE = 800  # Characters per chunk
CHUNK_OVERLAP = 100

# =============================================================================
# DATABASE MODELS
# =============================================================================

Base = declarative_base()

class LegalMapping(Base):
    """IPC to BNS mapping table for structured queries."""
    __tablename__ = "legal_mappings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ipc_section = Column(String(50), index=True)
    bns_section = Column(String(50), index=True)
    topic = Column(String(200))
    description = Column(Text)
    change_note = Column(Text)
    penalty_old = Column(String(200))
    penalty_new = Column(String(200))


# =============================================================================
# PDF INGESTION (ChromaDB)
# =============================================================================

def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk.strip())
        start = end - overlap
    return chunks


def extract_pdf_text(pdf_path: Path) -> str:
    """Extract text from PDF using pdfplumber."""
    text_parts = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
    except Exception as e:
        logger.error(f"Error extracting {pdf_path}: {e}")
    return "\n\n".join(text_parts)


def ingest_pdfs_to_chroma():
    """Ingest all PDFs from data folders into ChromaDB with category metadata."""
    try:
        import chromadb
        from chromadb.config import Settings
    except ImportError:
        logger.error("ChromaDB not installed. Run: pip install chromadb")
        return 0
    
    # Initialize ChromaDB
    client = chromadb.PersistentClient(
        path=str(CHROMA_PERSIST_DIR),
        settings=Settings(anonymized_telemetry=False)
    )
    
    # Delete and recreate collection to clear existing documents
    try:
        existing_collection = client.get_collection("legal_documents")
        existing_count = existing_collection.count()
        if existing_count > 0:
            logger.info(f"Clearing {existing_count} existing documents...")
            client.delete_collection("legal_documents")
    except:
        pass  # Collection doesn't exist yet
    
    # Create fresh collection
    collection = client.get_or_create_collection(
        name="legal_documents",
        metadata={"description": "Legal documents with category metadata"}
    )
    
    documents = []
    metadatas = []
    ids = []
    
    # Walk through data directory
    for category_folder in DATA_DIR.iterdir():
        if not category_folder.is_dir():
            continue
        
        category = category_folder.name  # e.g., "Traffic", "Criminal", "IT_Cyber"
        logger.info(f"\n📁 Processing category: {category}")
        
        for pdf_file in category_folder.glob("*.pdf"):
            logger.info(f"   📄 {pdf_file.name}")
            
            # Extract text
            full_text = extract_pdf_text(pdf_file)
            if not full_text:
                logger.warning(f"   ⚠️ No text extracted from {pdf_file.name}")
                continue
            
            # Chunk text
            chunks = chunk_text(full_text)
            logger.info(f"   → {len(chunks)} chunks created")
            
            for i, chunk in enumerate(chunks):
                doc_id = f"{category}_{pdf_file.stem}_{i}"
                
                documents.append(chunk)
                metadatas.append({
                    "category": category,
                    "filename": pdf_file.name,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "source": "pdf"
                })
                ids.append(doc_id)
    
    if not documents:
        logger.warning("No documents found to ingest!")
        return 0
    
    # Add to ChromaDB in batches
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        batch_docs = documents[i:i+batch_size]
        batch_metas = metadatas[i:i+batch_size]
        batch_ids = ids[i:i+batch_size]
        
        collection.add(
            documents=batch_docs,
            metadatas=batch_metas,
            ids=batch_ids
        )
        logger.info(f"   Added batch {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
    
    logger.info(f"\n✅ ChromaDB Ingestion Complete: {len(documents)} chunks indexed")
    return len(documents)


# =============================================================================
# CSV INGESTION (NeonDB PostgreSQL)
# =============================================================================

def ingest_csv_to_neondb():
    """Ingest IPC-BNS mapping CSV into PostgreSQL."""
    if not DATABASE_URL:
        logger.warning("DATABASE_URL not configured. Skipping NeonDB ingestion.")
        return 0
    
    csv_path = DATA_DIR / "Criminal" / "ipc_bns_chart.csv"
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        return 0
    
    # Create engine and tables
    engine = create_engine(DATABASE_URL)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Read CSV
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        
        logger.info(f"📊 Found {len(rows)} rows in CSV")
        
        # Clear existing data
        session.query(LegalMapping).delete()
        session.commit()
        
        # Insert rows
        count = 0
        for row in rows:
            # Skip empty rows
            if not row.get('IPC_Section') and not row.get('BNS_Section'):
                continue
            
            mapping = LegalMapping(
                ipc_section=row.get('IPC_Section', '').strip(),
                bns_section=row.get('BNS_Section', '').strip(),
                topic=row.get('Topic', '').strip(),
                description=row.get('Description', '').strip(),
                change_note=row.get('Change_Note', '').strip(),
                penalty_old=row.get('Penalty_Old', '').strip(),
                penalty_new=row.get('Penalty_New', '').strip()
            )
            session.add(mapping)
            count += 1
        
        session.commit()
        logger.info(f"✅ NeonDB Ingestion Complete: {count} mappings inserted")
        return count
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ NeonDB ingestion failed: {e}")
        import traceback
        traceback.print_exc()
        return 0
    finally:
        session.close()


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("\n" + "="*60)
    print("🏛️  NyayaShastra - Hybrid Data Ingestion")
    print("="*60)
    
    print("\n📚 Step 1: Ingesting PDFs to ChromaDB...")
    pdf_count = ingest_pdfs_to_chroma()
    
    print("\n📊 Step 2: Ingesting CSV to NeonDB...")
    csv_count = ingest_csv_to_neondb()
    
    print("\n" + "="*60)
    print("📋 INGESTION SUMMARY")
    print("="*60)
    print(f"   ChromaDB Chunks: {pdf_count}")
    print(f"   NeonDB Mappings: {csv_count}")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
