"""
NyayaShastra - Retriever Service
Hybrid retrieval with Smart Domain Guardrails:
1. SQL queries for IPC-BNS comparisons (hallucination-free)
2. Vector search for document retrieval with category filtering
3. Smart fallback with explicit disclaimers
"""

import os
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import asyncio
from app.schemas import LegalDomain

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =============================================================================
# CONFIGURATION
# =============================================================================

CHROMA_PERSIST_DIR = Path(__file__).parent.parent / "chroma_db"

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "")


# =============================================================================
# DATA CLASSES
# =============================================================================

class QueryType(Enum):
    COMPARISON = "comparison"  # IPC vs BNS comparison
    DOCUMENT_SEARCH = "document_search"  # Vector search
    GENERAL = "general"  # General legal question


@dataclass
class RetrievalResult:
    """Result from retrieval operations."""
    success: bool
    query_type: QueryType
    documents: List[Dict[str, Any]]
    sql_results: List[Dict[str, Any]]
    fallback_used: bool
    fallback_message: str
    category_requested: Optional[str]
    category_found: Optional[str]


# =============================================================================
# QUERY CLASSIFIER
# =============================================================================

class QueryClassifier:
    """Classifies queries to route to appropriate data source."""
    
    COMPARISON_PATTERNS = [
        r"compare\s+ipc\s+(\d+)\s+(?:and|vs|with|to)\s+bns\s+(\d+)",
        r"ipc\s+(\d+)\s+(?:and|vs|with|to)\s+bns\s+(\d+)",
        r"bns\s+(\d+)\s+(?:and|vs|with|to)\s+ipc\s+(\d+)",
        r"difference\s+between\s+ipc\s+(\d+)\s+and\s+bns\s+(\d+)",
        r"what\s+is\s+bns\s+equivalent\s+of\s+ipc\s+(\d+)",
        r"ipc\s+(\d+)\s+(?:ka|ki)?\s*bns\s+(?:mein|me)\s+kya\s+(?:hai|he)",
        r"ipc\s+section\s+(\d+)",
        r"bns\s+section\s+(\d+)",
        r"mapping\s+(?:of\s+)?ipc\s+(\d+)",
    ]
    
    # Domain keywords for classification
    DOMAIN_KEYWORDS = {
        LegalDomain.TRAFFIC.value: [
            "traffic", "vehicle", "motor", "driving", "accident", "road", "challan", "license", "signals", 
            "overloading", "fine", "penalty", "helmet", "seatbelt", "speeding", "drunk driving", "drink and drive",
            "rc", "registration", "puc", "insurance", "one way", "parking", "no entry", "overtaking", "zebra crossing",
            "signal jumping", "red light", "transport", "mvi", "rto", "hit and run"
        ],
        LegalDomain.CRIMINAL.value: [
            "murder", "theft", "robbery", "assault", "arrest", "fir", "bail", "crime", "offense", "prison", 
            "punishment", "ipc", "bns", "jail", "kidnapping", "rape", "molestation", "fraud", "cheating", 
            "extortion", "bribery", "homicide", "culpable", "conspiracy", "abetment", "forgery", "perjury",
            "defamation", "terror", "uapa", "pmla", "ndps", "drugs", "arms act"
        ],
        LegalDomain.IT_CYBER.value: [
            "cyber", "it act", "hacking", "data", "privacy", "computer", "online", "digital", "phishing", 
            "identity theft", "server", "electronic", "spam", "virus", "malware", "credit card fraud",
            "social media", "harassment", "cyberstalking", "deepfake", "cryptocurrency", "bitcoin", "it rules"
        ],
        LegalDomain.CORPORATE.value: [
            "company", "corporate", "sebi", "contract", "business", "director", "shareholder", "merger", 
            "acquisition", "tax", "gst", "income tax", "insolvency", "bankruptcy", "mca", "roc", "shares",
            "audit", "compliance", "partnership", "llp", "tender", "arbitration", "msme"
        ],
        LegalDomain.ENVIRONMENT.value: [
            "environment", "pollution", "ngt", "forest", "wildlife", "green", "waste", "eia", "climate",
            "emissions", "water act", "air act", "coastal", "crz", "plastic", "garbage", "sanitation"
        ],
        LegalDomain.PROPERTY.value: [
            "property", "land", "registration", "real estate", "rent", "tenant", "lease", "sale deed", 
            "apartment", "flat", "possession", "eviction", "encroachment", "stamp duty", "partition",
            "succession", "rera", "mutation", "khata", "registry"
        ],
        LegalDomain.CIVIL_FAMILY.value: [
            "divorce", "marriage", "custody", "alimony", "family", "maintenance", "domestic violence", 
            "dowry", "will", "succession", "inheritance", "adoption", "guardianship", "restitution",
            "nuisance", "negligence", "defamation", "consumer", "forum", "compensation"
        ],
        LegalDomain.CONSTITUTIONAL.value: [
            "constitution", "fundamental", "rights", "article", "writ", "pil", "supreme court", "rti", 
            "high court", "judiciary", "secular", "democracy", "parliament", "amendment", "state", "center",
            "federal", "governor", "president", "election", "ecil"
        ]
    }
    
    @classmethod
    def classify(cls, query: str) -> Tuple[QueryType, Optional[Dict]]:
        """Classify query and extract relevant parameters."""
        query_lower = query.lower()
        
        # Check for comparison patterns
        for pattern in cls.COMPARISON_PATTERNS:
            match = re.search(pattern, query_lower)
            if match:
                groups = match.groups()
                return QueryType.COMPARISON, {
                    "sections": [g for g in groups if g],
                    "pattern": pattern
                }
        
        # Default to document search
        return QueryType.DOCUMENT_SEARCH, None
    
    @classmethod
    def is_query_relevant_to_domain(cls, query: str, domain: str) -> bool:
        """Deprecated: Use BM25DomainClassifier.classify instead."""
        return True # Fallback to allow search, guardrail happens in RetrieverService or ResponseAgent


# =============================================================================
# SQL RETRIEVER (Structured Data)
# =============================================================================

class SQLRetriever:
    """Retrieves IPC-BNS mappings from PostgreSQL."""
    
    def __init__(self):
        self.engine = None
        self._init_engine()
    
    def _init_engine(self):
        """Initialize database engine."""
        if DATABASE_URL:
            try:
                from sqlalchemy import create_engine
                self.engine = create_engine(DATABASE_URL)
            except Exception as e:
                logger.warning(f"Could not connect to database: {e}")
    
    def search_mapping(self, section: str, code_type: str = "ipc") -> List[Dict[str, Any]]:
        """Search for IPC or BNS section mapping."""
        if not self.engine:
            return []
        
        try:
            from sqlalchemy import text
            
            if code_type.lower() == "ipc":
                query = text("""
                    SELECT * FROM legal_mappings 
                    WHERE ipc_section LIKE :section
                    OR ipc_section = :exact_section
                """)
            else:
                query = text("""
                    SELECT * FROM legal_mappings 
                    WHERE bns_section LIKE :section
                    OR bns_section = :exact_section
                """)
            
            with self.engine.connect() as conn:
                result = conn.execute(query, {
                    "section": f"%{section}%",
                    "exact_section": section
                })
                rows = result.fetchall()
                
                return [{
                    "ipc_section": row.ipc_section,
                    "bns_section": row.bns_section,
                    "topic": row.topic,
                    "description": row.description,
                    "change_note": row.change_note,
                    "penalty_old": row.penalty_old,
                    "penalty_new": row.penalty_new
                } for row in rows]
                
        except Exception as e:
            logger.error(f"SQL query failed: {e}")
            return []
    
    def compare_sections(self, ipc_section: str, bns_section: str = None) -> List[Dict[str, Any]]:
        """Compare IPC and BNS sections."""
        results = self.search_mapping(ipc_section, "ipc")
        
        if bns_section:
            bns_results = self.search_mapping(bns_section, "bns")
            # Merge results
            results.extend([r for r in bns_results if r not in results])
        
        return results


# =============================================================================
# VECTOR RETRIEVER (Unstructured Data)
# =============================================================================

class VectorRetriever:
    """Retrieves documents from ChromaDB with category filtering."""
    
    def __init__(self):
        self.client = None
        self.collection = None
        self._init_chroma()
    
    def _init_chroma(self):
        """Initialize ChromaDB client."""
        try:
            import chromadb
            from chromadb.config import Settings
            
            self.client = chromadb.PersistentClient(
                path=str(CHROMA_PERSIST_DIR),
                settings=Settings(anonymized_telemetry=False)
            )
            self.collection = self.client.get_or_create_collection(
                name="legal_documents"
            )
            logger.info(f"ChromaDB initialized with {self.collection.count()} documents")
        except Exception as e:
            logger.warning(f"ChromaDB not available: {e}")
    
    def search(
        self, 
        query: str, 
        category: Optional[str] = None, 
        limit: int = 5
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Search documents with optional category filter.
        Returns (results, used_fallback)
        """
        if not self.collection:
            return [], False
        
        used_fallback = False
        
        # Build where filter
        where_filter = None
        if category and category.lower() != "all":
            where_filter = {"category": category}
        
        try:
            # First, try with category filter
            results = self.collection.query(
                query_texts=[query],
                n_results=limit,
                where=where_filter
            )
            
            # Check if we got meaningful results
            if results and results["documents"] and results["documents"][0]:
                documents = []
                for i, doc in enumerate(results["documents"][0]):
                    metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                    distance = results["distances"][0][i] if results["distances"] else 0
                    
                    documents.append({
                        "content": doc,
                        "category": metadata.get("category", ""),
                        "filename": metadata.get("filename", ""),
                        "chunk_index": metadata.get("chunk_index", 0),
                        "relevance_score": 1 - distance,  # Convert distance to similarity
                        "source": "chromadb"
                    })
                
                return documents, False
            
            # If no results with filter, try without filter (fallback)
            if category and category.lower() != "all":
                logger.info(f"No results in category '{category}', trying fallback...")
                
                results = self.collection.query(
                    query_texts=[query],
                    n_results=limit
                )
                
                if results and results["documents"] and results["documents"][0]:
                    documents = []
                    for i, doc in enumerate(results["documents"][0]):
                        metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                        distance = results["distances"][0][i] if results["distances"] else 0
                        
                        documents.append({
                            "content": doc,
                            "category": metadata.get("category", ""),
                            "filename": metadata.get("filename", ""),
                            "chunk_index": metadata.get("chunk_index", 0),
                            "relevance_score": 1 - distance,
                            "source": "chromadb_fallback"
                        })
                    
                    return documents, True
            
            return [], False
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return [], False
    
    def get_categories(self) -> List[str]:
        """Get all available categories."""
        if not self.collection:
            return []
        
        try:
            results = self.collection.get(limit=1000, include=["metadatas"])
            categories = set()
            for meta in results["metadatas"]:
                if meta.get("category"):
                    categories.add(meta["category"])
            return sorted(list(categories))
        except:
            return []


# =============================================================================
# HYBRID RETRIEVER SERVICE
# =============================================================================

class RetrieverService:
    """
    Main retrieval service with Smart Domain Guardrails.
    Routes queries to appropriate data sources and handles fallbacks.
    """
    
    async def _init_components(self):
        """Initialize async components."""
        from app.services.bm25_service import get_domain_classifier
        self.domain_classifier = await get_domain_classifier()

    def __init__(self):
        self.sql_retriever = SQLRetriever()
        self.vector_retriever = VectorRetriever()
        self.classifier = QueryClassifier()
        self.domain_classifier = None # Will be initialized async
    
    async def retrieve(
        self, 
        query: str, 
        selected_category: Optional[str] = None
    ) -> RetrievalResult:
        """
        Main retrieval method with smart guardrails.
        """
        # Step 0: Ensure components are initialized
        if not self.domain_classifier:
            await self._init_components()
            
        # Step 1: Classify the query
        query_type, params = self.classifier.classify(query)
        
        # Step 2: Route to appropriate retriever
        if query_type == QueryType.COMPARISON:
            return await self._handle_comparison(query, params)
        else:
            return await self._handle_document_search(query, selected_category)
    
    async def _handle_comparison(self, query: str, params: Dict) -> RetrievalResult:
        """Handle IPC-BNS comparison queries using SQL."""
        sections = params.get("sections", [])
        
        sql_results = []
        for section in sections:
            # Try both IPC and BNS
            results = self.sql_retriever.search_mapping(section, "ipc")
            if not results:
                results = self.sql_retriever.search_mapping(section, "bns")
            sql_results.extend(results)
        
        # Deduplicate
        seen = set()
        unique_results = []
        for r in sql_results:
            key = (r.get("ipc_section"), r.get("bns_section"))
            if key not in seen:
                seen.add(key)
                unique_results.append(r)
        
        return RetrievalResult(
            success=len(unique_results) > 0,
            query_type=QueryType.COMPARISON,
            documents=[],
            sql_results=unique_results,
            fallback_used=False,
            fallback_message="",
            category_requested=None,
            category_found=None
        )
    
    async def _handle_document_search(self, query: str, category: Optional[str]) -> RetrievalResult:
        """Handle document search with smart guardrails."""
        
        # Check if query is relevant to selected category
        is_relevant = True
        rejection_message = ""
        
        if category and category.lower() != "all":
            # RE-RANKING DOMAIN CHECK: Best implementation using BM25
            predicted_domain, confidence, all_scores = await self.domain_classifier.classify(query)
            
            # STICKY DOMAIN LOGIC: 
            # 1. If predicted == selected, it's a match.
            # 2. If selected category scores high enough (relative to top), it's a match.
            # 3. If selected category has a significant absolute score (>0.15), it's a match.
            
            selected_score = all_scores.get(category, 0)
            top_score = confidence
            
            # Is the user's selected category "Close Enough" or "Strong Enough"?
            is_match = (predicted_domain == category)
            is_close = (selected_score > (top_score * 0.5) and selected_score > 0.1)
            is_strong = (selected_score > 0.2)
            
            if not (is_match or is_close or is_strong):
                is_relevant = False
                rejection_message = (
                    f"⚠️ This query appears to be related to **{predicted_domain}** law, "
                    f"not **{category}** law. Please switch to the correct domain."
                )
            
            # Special case for extremely specific keywords (Double Check)
            if is_relevant:
                # We can keep this simple keyword check as a safety net if needed
                pass 
        
        # Search with category filter
        documents, used_fallback = await self.vector_retriever.search(
            query=query,
            category=category if category and category.lower() != "all" else None,
            limit=5
        )
        
        # Determine fallback message
        fallback_message = ""
        if used_fallback and documents:
            actual_category = documents[0].get("category", "general")
            fallback_message = (
                f"⚠️ **Note:** This answer is based on general legal principles "
                f"as the specific document was not found in the selected '{category}' documents. "
                f"The information is sourced from '{actual_category}' domain documents."
            )
        elif not documents and category:
            fallback_message = (
                f"⚠️ No relevant documents found in the '{category}' category. "
                "Providing general legal knowledge."
            )
        
        # Add rejection message if query is irrelevant
        if rejection_message:
            fallback_message = rejection_message
        
        return RetrievalResult(
            success=len(documents) > 0 or used_fallback,
            query_type=QueryType.DOCUMENT_SEARCH,
            documents=documents,
            sql_results=[],
            fallback_used=used_fallback,
            fallback_message=fallback_message,
            category_requested=category,
            category_found=documents[0].get("category") if documents else None
        )
    
    def get_available_categories(self) -> List[str]:
        """Get list of available document categories."""
        return self.vector_retriever.get_categories()


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_retriever_service: Optional[RetrieverService] = None

def get_retriever_service() -> RetrieverService:
    """Get singleton instance of retriever service."""
    global _retriever_service
    if _retriever_service is None:
        _retriever_service = RetrieverService()
    return _retriever_service


# =============================================================================
# TESTING
# =============================================================================

if __name__ == "__main__":
    service = get_retriever_service()
    
    print("\n" + "="*60)
    print("🔍 Testing Hybrid Retriever")
    print("="*60)
    
    # Test 1: IPC-BNS Comparison
    print("\n📊 Test 1: IPC-BNS Comparison")
    result = service.retrieve("Compare IPC 302 and BNS 103")
    print(f"   Query Type: {result.query_type}")
    print(f"   SQL Results: {len(result.sql_results)}")
    if result.sql_results:
        print(f"   First Result: {result.sql_results[0]}")
    
    # Test 2: Category-filtered search
    print("\n📚 Test 2: Traffic Law Query")
    result = service.retrieve("What is the penalty for drunk driving?", "Traffic")
    print(f"   Query Type: {result.query_type}")
    print(f"   Documents: {len(result.documents)}")
    print(f"   Fallback Used: {result.fallback_used}")
    print(f"   Message: {result.fallback_message}")
    
    # Test 3: Wrong domain query
    print("\n⚠️ Test 3: Irrelevant Query")
    result = service.retrieve("What are divorce laws?", "Traffic")
    print(f"   Message: {result.fallback_message}")
    
    print("\n" + "="*60)
