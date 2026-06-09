"""
NyayaShastra - Data Ingestion Pipeline
Chunks, embeds, and indexes legal data for semantic search.
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

from app.config import settings
from app.database import init_db, get_db_context
from app.models import Statute, CaseLaw, IPCBNSMapping
from app.services.vector_store import VectorStoreService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LegalDataIngestionPipeline:
    """Pipeline for ingesting and indexing legal data."""
    
    def __init__(self):
        self.vector_store: Optional[VectorStoreService] = None
        self.chunk_size = 500  # characters
        self.chunk_overlap = 100  # characters
    
    async def initialize(self):
        """Initialize the pipeline."""
        logger.info("Initializing data ingestion pipeline...")
        init_db()
        
        self.vector_store = VectorStoreService()
        await self.vector_store.initialize()
        logger.info("Pipeline initialized successfully")
    
    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Split text into overlapping chunks with metadata."""
        if not text or len(text) < self.chunk_size:
            return [{
                "text": text,
                "chunk_index": 0,
                "total_chunks": 1,
                **metadata
            }]
        
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to end at sentence boundary
            if end < len(text):
                sentence_end = text.rfind('.', start, end)
                if sentence_end > start + self.chunk_size // 2:
                    end = sentence_end + 1
            
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "chunk_index": chunk_index,
                    **metadata
                })
                chunk_index += 1
            
            start = end - self.chunk_overlap
        
        # Add total_chunks to all
        for chunk in chunks:
            chunk["total_chunks"] = len(chunks)
        
        return chunks
    
    async def ingest_statutes(self) -> int:
        """Ingest all statutes into vector store."""
        logger.info("Ingesting statutes...")
        
        with get_db_context() as db:
            statutes = db.query(Statute).all()
            
            if not statutes:
                logger.warning("No statutes found in database")
                return 0
            
            texts = []
            metadatas = []
            ids = []
            
            for statute in statutes:
                # Create searchable text combining all fields
                searchable_text = f"""
                {statute.act_code} Section {statute.section_number}
                {statute.title_en or ''}
                {statute.title_hi or ''}
                {statute.content_en or ''}
                {statute.content_hi or ''}
                """.strip()
                
                # Chunk the content
                metadata_base = {
                    "type": "statute",
                    "section_number": statute.section_number,
                    "act_code": statute.act_code,
                    "act_name": statute.act_name or "",
                    "title_en": statute.title_en or "",
                    "title_hi": statute.title_hi or "",
                    "domain": statute.domain or "criminal",
                    "is_cognizable": statute.is_cognizable if statute.is_cognizable else False,
                    "is_bailable": statute.is_bailable if statute.is_bailable else True,
                    "db_id": str(statute.id)
                }
                
                chunks = self.chunk_text(searchable_text, metadata_base)
                
                for chunk in chunks:
                    texts.append(chunk.pop("text"))
                    ids.append(f"statute_{statute.id}_{chunk['chunk_index']}")
                    metadatas.append(chunk)
            
            # Add to vector store
            if self.vector_store and texts:
                await self.vector_store.add_texts(
                    texts=texts,
                    metadatas=metadatas,
                    ids=ids,
                    collection_name="statutes"
                )
            
            logger.info(f"Ingested {len(statutes)} statutes ({len(texts)} chunks)")
            return len(statutes)
    
    async def ingest_case_laws(self) -> int:
        """Ingest all case laws into vector store."""
        logger.info("Ingesting case laws...")
        
        with get_db_context() as db:
            cases = db.query(CaseLaw).all()
            
            if not cases:
                logger.warning("No case laws found in database")
                return 0
            
            texts = []
            metadatas = []
            ids = []
            
            for case in cases:
                # Create searchable text
                searchable_text = f"""
                {case.case_name or ''}
                {case.case_name_hi or ''}
                {case.case_number or ''}
                {case.summary_en or ''}
                {case.summary_hi or ''}
                {' '.join(case.key_holdings or [])}
                """.strip()
                
                metadata_base = {
                    "type": "case_law",
                    "case_name": case.case_name or "",
                    "case_number": case.case_number or "",
                    "court": case.court.value if hasattr(case.court, "value") else case.court if case.court else "supreme_court",
                    "court_name": case.court_name or "",
                    "reporting_year": case.reporting_year or 0,
                    "is_landmark": case.is_landmark if case.is_landmark else False,
                    "domain": case.domain or "criminal",
                    "citation_string": case.citation_string or "",
                    "source_url": case.source_url or "",
                    "cited_sections": ",".join([s.section_number for s in case.cited_statutes]),
                    "db_id": str(case.id)
                }
                
                chunks = self.chunk_text(searchable_text, metadata_base)
                
                for chunk in chunks:
                    texts.append(chunk.pop("text"))
                    ids.append(f"case_{case.id}_{chunk['chunk_index']}")
                    metadatas.append(chunk)
            
            # Add to vector store  
            if self.vector_store and texts:
                await self.vector_store.add_texts(
                    texts=texts,
                    metadatas=metadatas,
                    ids=ids,
                    collection_name="case_laws"
                )
            
            logger.info(f"Ingested {len(cases)} case laws ({len(texts)} chunks)")
            return len(cases)
    
    async def ingest_ipc_bns_mappings(self) -> int:
        """Ingest IPC-BNS mappings for cross-reference search."""
        logger.info("Ingesting IPC-BNS mappings...")
        
        with get_db_context() as db:
            mappings = db.query(IPCBNSMapping).all()
            
            if not mappings:
                logger.warning("No IPC-BNS mappings found")
                return 0
            
            texts = []
            metadatas = []
            ids = []
            
            for mapping in mappings:
                # Get related statutes
                ipc_section = db.query(Statute).filter(Statute.id == mapping.ipc_section_id).first()
                bns_section = db.query(Statute).filter(Statute.id == mapping.bns_section_id).first()
                
                if not ipc_section or not bns_section:
                    continue
                
                searchable_text = f"""
                IPC Section {ipc_section.section_number} maps to BNS Section {bns_section.section_number}
                {ipc_section.title_en or ''} - {bns_section.title_en or ''}
                {mapping.mapping_type or 'exact'} mapping
                {str(mapping.changes) if mapping.changes else ''}
                """.strip()
                
                metadata = {
                    "type": "ipc_bns_mapping",
                    "ipc_section": ipc_section.section_number,
                    "bns_section": bns_section.section_number,
                    "ipc_title": ipc_section.title_en or "",
                    "bns_title": bns_section.title_en or "",
                    "mapping_type": mapping.mapping_type or "exact",
                    "punishment_changed": mapping.punishment_changed if mapping.punishment_changed else False,
                    "db_id": str(mapping.id)
                }
                
                texts.append(searchable_text)
                metadatas.append(metadata)
                ids.append(f"mapping_{mapping.id}")
            
            if self.vector_store and texts:
                await self.vector_store.add_texts(
                    texts=texts,
                    metadatas=metadatas,
                    ids=ids,
                    collection_name="mappings"
                )
            
            logger.info(f"Ingested {len(mappings)} IPC-BNS mappings")
            return len(mappings)
    
    async def run_full_ingestion(self) -> Dict[str, int]:
        """Run complete data ingestion pipeline."""
        logger.info("Starting full data ingestion...")
        start_time = datetime.now()
        
        results = {
            "statutes": await self.ingest_statutes(),
            "case_laws": await self.ingest_case_laws(),
            "mappings": await self.ingest_ipc_bns_mappings()
        }
        
        # Ingest PDF documents from legal_data folders
        try:
            pdf_count = await self.ingest_pdf_documents()
            results["documents"] = pdf_count
        except Exception as e:
            logger.error(f"PDF ingestion failed: {e}")
            results["documents"] = 0
        
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"Full ingestion completed in {duration:.2f}s")
        logger.info(f"Results: {results}")
        
        return results
    
    async def ingest_pdf_documents(self) -> int:
        """Ingest PDF documents from legal_data subfolders with domain metadata."""
        logger.info("Ingesting PDF documents...")
        
        try:
            from app.services.pdf_ingestion import get_pdf_ingestion_service
            
            pdf_service = get_pdf_ingestion_service()
            documents = pdf_service.ingest_all_documents()
            
            if documents and self.vector_store:
                await self.vector_store.add_documents(documents)
                logger.info(f"Added {len(documents)} PDF document chunks to vector store")
                return len(documents)
            
            return 0
        except ImportError as e:
            logger.warning(f"PDF ingestion not available: {e}")
            return 0
        except Exception as e:
            logger.error(f"Error ingesting PDFs: {e}")
            return 0
    
    async def search(self, query: str, collection: str = "statutes", 
                    filters: Optional[Dict] = None, limit: int = 5) -> List[Dict]:
        """Search the vector store."""
        if not self.vector_store:
            return []
        
        return await self.vector_store.search(
            query=query,
            collection_name=collection,
            filters=filters,
            limit=limit
        )


async def main():
    """Main entry point for data ingestion."""
    # First run the database seeding
    from app.seed_database import seed_database
    seed_database()
    
    # Then run ingestion
    pipeline = LegalDataIngestionPipeline()
    await pipeline.initialize()
    results = await pipeline.run_full_ingestion()
    
    print("\n" + "="*50)
    print("DATA INGESTION COMPLETE")
    print("="*50)
    print(f"Statutes indexed: {results['statutes']}")
    print(f"Case laws indexed: {results['case_laws']}")
    print(f"Mappings indexed: {results['mappings']}")
    print(f"PDF documents indexed: {results.get('documents', 0)}")
    print("="*50)


if __name__ == "__main__":
    asyncio.run(main())

