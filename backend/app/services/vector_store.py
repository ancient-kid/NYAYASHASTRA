"""
NyayaShastra - Vector Store Service
Handles vector embeddings and semantic search using ChromaDB.
"""

from typing import List, Dict, Any, Optional
import logging

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    from rank_bm25 import BM25Okapi
    import re
    import numpy as np
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from app.config import settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    """Service for vector storage and semantic search."""
    
    def __init__(self):
        self.client = None
        self.embedding_model = None
        self.statutes_collection = None
        self.cases_collection = None
        self.documents_collection = None  # For PDF documents
        self.mappings_collection = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize vector store and embedding model."""
        if self._initialized:
            return
        
        try:
            if CHROMA_AVAILABLE:
                # Initialize ChromaDB with new API
                self.client = chromadb.PersistentClient(
                    path=settings.chroma_persist_dir
                )
                
                # Get or create collections
                self.statutes_collection = self.client.get_or_create_collection(
                    name="statutes",
                    metadata={"description": "Legal statutes and sections"}
                )
                
                self.cases_collection = self.client.get_or_create_collection(
                    name="case_laws",
                    metadata={"description": "Court judgments and case laws"}
                )
                
                # Documents collection for PDFs with domain metadata
                self.documents_collection = self.client.get_or_create_collection(
                    name="documents",
                    metadata={"description": "PDF documents with domain categories"}
                )
                
                logger.info("ChromaDB initialized successfully")
            
            if SENTENCE_TRANSFORMERS_AVAILABLE:
                # Initialize embedding model
                self.embedding_model = SentenceTransformer(settings.embedding_model)
                logger.info(f"Embedding model '{settings.embedding_model}' loaded")
            
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text."""
        if self.embedding_model:
            return self.embedding_model.encode(text).tolist()
        return []
    
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if self.embedding_model:
            return self.embedding_model.encode(texts).tolist()
        return []
    
    async def add_statutes(self, statutes: List[Dict[str, Any]]):
        """Add statutes to vector store."""
        if not self.statutes_collection:
            logger.warning("Vector store not initialized")
            return
        
        documents = []
        metadatas = []
        ids = []
        
        for statute in statutes:
            # Combine title and content for embedding
            doc_text = f"{statute.get('title_en', '')}. {statute.get('content_en', '')}"
            documents.append(doc_text)
            
            metadatas.append({
                "section_number": statute.get("section_number", ""),
                "act_code": statute.get("act_code", ""),
                "act_name": statute.get("act_name", ""),
                "domain": statute.get("domain", ""),
                "title_en": statute.get("title_en", ""),
                "title_hi": statute.get("title_hi", "")
            })
            
            ids.append(f"{statute.get('act_code', 'UNK')}_{statute.get('section_number', 'UNK')}")
        
        # Generate embeddings
        embeddings = self.embed_texts(documents)
        
        # Add to collection
        self.statutes_collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Added {len(statutes)} statutes to vector store")
    
    async def add_cases(self, cases: List[Dict[str, Any]]):
        """Add case laws to vector store."""
        if not self.cases_collection:
            logger.warning("Vector store not initialized")
            return
        
        documents = []
        metadatas = []
        ids = []
        
        for case in cases:
            doc_text = f"{case.get('case_name', '')}. {case.get('summary_en', '')}"
            documents.append(doc_text)
            
            metadatas.append({
                "case_number": case.get("case_number", ""),
                "case_name": case.get("case_name", ""),
                "court": case.get("court", ""),
                "domain": case.get("domain", ""),
                "is_landmark": case.get("is_landmark", False),
                "reporting_year": case.get("reporting_year", 0)
            })
            
            ids.append(str(case.get("id", f"case_{len(ids)}")))
        
        embeddings = self.embed_texts(documents)
        
        self.cases_collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        
        logger.info(f"Added {len(cases)} cases to vector store")
    
    async def search_statutes(self, query: str, act_codes: Optional[List[str]] = None,
                             domain: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant statutes."""
        if not self.statutes_collection:
            logger.warning("Vector store not initialized")
            return []
        
        # Build where filter
        filters = []
        if act_codes:
            filters.append({"act_code": {"$in": act_codes}})
        if domain and domain != "all":
            filters.append({"domain": domain})
            
        where_filter = None
        if len(filters) == 1:
            where_filter = filters[0]
        elif len(filters) > 1:
            where_filter = {"$and": filters}
        
        # Generate query embedding
        query_embedding = self.embed_text(query)
        
        # Search
        results = self.statutes_collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where_filter
        )
        
        # Format results
        formatted = []
        if results and results["ids"]:
            for i, doc_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                formatted.append({
                    "id": doc_id,
                    "content": results["documents"][0][i] if results["documents"] else "",
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                    **metadata
                })
        
        # Apply Re-ranking with BM25
        if formatted:
            formatted = self._rerank_with_bm25(query, formatted)
            
        return formatted[:limit]

    def _rerank_with_bm25(self, query: str, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Re-rank retrieved documents using BM25 for keyword relevance."""
        if not documents:
            return []

        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            return documents
            
        # Get contents for BM25
        contents = [doc.get("content", "") for doc in documents]
        
        # Tokenize
        def tokenize(text):
            return re.sub(r'[^\w\s]', ' ', text.lower()).split()
            
        tokenized_query = tokenize(query)
        tokenized_corpus = [tokenize(doc) for doc in contents]
        
        # Calculate BM25 scores
        bm25 = BM25Okapi(tokenized_corpus)
        bm25_scores = bm25.get_scores(tokenized_query)
        
        # Normalize BM25 scores
        if max(bm25_scores) > 0:
            bm25_scores = bm25_scores / max(bm25_scores)
            
        # Combine with Vector score (1 - distance)
        for i, doc in enumerate(documents):
            vector_score = doc.get("relevance_score", 1 - doc.get("distance", 0))
            # Hybrid score: 60% BM25, 40% Vector (keywords are king for statutes)
            doc["hybrid_score"] = (0.6 * bm25_scores[i]) + (0.4 * vector_score)
            
        # Sort by hybrid score
        documents.sort(key=lambda x: x.get("hybrid_score", 0), reverse=True)
        return documents
    
    async def search_cases(self, query: str, domain: Optional[str] = None,
                          court: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant case laws."""
        if not self.cases_collection:
            logger.warning("Vector store not initialized")
            return []
        
        where_filter = None
        if domain:
            where_filter = {"domain": domain}
        elif court:
            where_filter = {"court": court}
        
        query_embedding = self.embed_text(query)
        
        results = self.cases_collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where_filter
        )
        
        formatted = []
        if results and results["ids"]:
            for i, doc_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                formatted.append({
                    "id": doc_id,
                    "content": results["documents"][0][i] if results["documents"] else "",
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                    **metadata
                })
        
        # Apply Re-ranking with BM25
        if formatted:
            formatted = self._rerank_with_bm25(query, formatted)
            
        return formatted[:limit]

    async def add_texts(self, texts: List[str], metadatas: List[Dict[str, Any]], ids: List[str], collection_name: str):
        """Add texts to a specific collection in vector store."""
        if not self._initialized:
            await self.initialize()
            
        collection = None
        if collection_name == "statutes":
            collection = self.statutes_collection
        elif collection_name == "case_laws":
            collection = self.cases_collection
        elif collection_name == "documents":
            collection = self.documents_collection
        elif collection_name == "mappings":
            if not self.mappings_collection:
                self.mappings_collection = self.client.get_or_create_collection(
                    name="mappings",
                    metadata={"description": "IPC-BNS cross-mappings"}
                )
            collection = self.mappings_collection
            
        if not collection:
            logger.warning(f"Collection '{collection_name}' not found or initialized")
            return
            
        embeddings = self.embed_texts(texts)
        
        collection.add(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Added {len(texts)} items to collection '{collection_name}'")
    
    async def add_documents(self, documents: List[Dict[str, Any]]):
        """Add PDF documents to vector store with domain metadata.
        
        Args:
            documents: List of document chunks with 'text' and metadata fields
        """
        if not self.documents_collection:
            logger.warning("Vector store not initialized")
            return
        
        texts = []
        metadatas = []
        ids = []
        
        for i, doc in enumerate(documents):
            text = doc.get("text", "")
            if not text:
                continue
            
            texts.append(text)
            
            # Extract metadata
            metadatas.append({
                "filename": doc.get("filename", ""),
                "category": doc.get("category", ""),  # Domain from folder
                "domain": doc.get("domain", ""),
                "folder": doc.get("folder", ""),
                "source": doc.get("source", "pdf"),
                "chunk_index": doc.get("chunk_index", 0),
                "total_chunks": doc.get("total_chunks", 1),
            })
            
            # Create unique ID
            doc_id = f"doc_{doc.get('filename', 'unknown')}_{doc.get('chunk_index', i)}"
            ids.append(doc_id)
        
        if not texts:
            logger.warning("No documents to add")
            return
        
        # Generate embeddings
        embeddings = self.embed_texts(texts)
        
        # Add to collection in batches to prevent exceeding ChromaDB batch size limits (max 5461)
        batch_size = 2000
        total_docs = len(texts)
        for idx in range(0, total_docs, batch_size):
            batch_texts = texts[idx : idx + batch_size]
            batch_embeddings = embeddings[idx : idx + batch_size]
            batch_metadatas = metadatas[idx : idx + batch_size]
            batch_ids = ids[idx : idx + batch_size]
            
            self.documents_collection.add(
                documents=batch_texts,
                embeddings=batch_embeddings,
                metadatas=batch_metadatas,
                ids=batch_ids
            )
            logger.info(f"Indexed batch {idx // batch_size + 1} / {(total_docs - 1) // batch_size + 1}")
        
        logger.info(f"Added {len(texts)} document chunks to vector store")
    
    async def search_documents(self, query: str, domain: Optional[str] = None,
                              category: Optional[str] = None, limit: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant document chunks with domain filtering.
        
        Args:
            query: Search query
            domain: Filter by domain (e.g., 'criminal', 'corporate')
            category: Filter by category (same as domain)
            limit: Max results to return
            
        Returns:
            List of matching document chunks
        """
        if not self.documents_collection:
            logger.warning("Vector store not initialized")
            return []
        
        # Build where filter for domain
        where_filter = None
        filter_domain = domain or category
        
        if filter_domain and filter_domain.lower() not in ["all", ""]:
            where_filter = {"domain": filter_domain.lower()}
        
        # Generate query embedding
        query_embedding = self.embed_text(query)
        
        # Search with filter
        results = self.documents_collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where_filter
        )
        
        # Format results
        formatted = []
        if results and results["ids"]:
            for i, doc_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                formatted.append({
                    "id": doc_id,
                    "content": results["documents"][0][i] if results["documents"] else "",
                    "distance": results["distances"][0][i] if results["distances"] else 0,
                    "source": "document",
                    **metadata
                })
        
        # Apply Re-ranking with BM25
        if formatted:
            formatted = self._rerank_with_bm25(query, formatted)
            
        logger.info(f"Document search returned {len(formatted)} results (domain filter: {filter_domain})")
        return formatted[:limit]


# Singleton instance
_vector_store: Optional[VectorStoreService] = None


async def get_vector_store() -> VectorStoreService:
    """Get or create vector store singleton."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreService()
        await _vector_store.initialize()
    return _vector_store

