"""
NyayaShastra - Statute Retrieval Agent
Retrieves relevant IPC/BNS sections and handles cross-mapping.
NO MOCK DATA - Uses real database via StatuteService.
"""

from typing import List, Dict, Any, Optional
import logging

from app.agents.base import BaseAgent, AgentContext
from app.schemas import AgentType
from app.services.vector_store import VectorStoreService
from app.services.statute_service import StatuteService, get_statute_service

logger = logging.getLogger(__name__)


class StatuteRetrievalAgent(BaseAgent):
    """Agent for retrieving relevant statutes and sections from database."""
    
    def __init__(self, vector_store: Optional[VectorStoreService] = None, 
                 statute_service: Optional[StatuteService] = None):
        super().__init__()
        self.agent_type = AgentType.STATUTE
        self.name = "Statute Retrieval"
        self.name_hi = "विधि खोज"
        self.description = "Retrieves relevant IPC, BNS, and other statute sections"
        self.color = "#a855f7"
        
        self.vector_store = vector_store
        # Use provided service or get singleton
        self.statute_service = statute_service or get_statute_service()
    
    async def process(self, context: AgentContext) -> AgentContext:
        """Retrieve relevant statutes based on query from database."""
        
        # Ensure vector store is available
        if not self.vector_store:
            try:
                from app.services.vector_store import get_vector_store
                self.vector_store = await get_vector_store()
            except Exception as e:
                logger.warning(f"Vector store not available in StatuteRetrievalAgent: {e}")
        
        # Extract sections mentioned in query
        sections = [e["value"] for e in context.entities if e["type"] == "section"]
        
        retrieved_statutes = []
        
        # 1. Direct section lookup if sections are mentioned
        if sections:
            for section in sections:
                for act_code in context.applicable_acts or ["IPC", "BNS"]:
                    statute = await self.statute_service.get_section(section, act_code)
                    if statute:
                        retrieved_statutes.append(statute)
                        logger.info(f"Retrieved {act_code} Section {section} from database")
        
        # 2. Semantic search for additional relevant statutes with domain filter
        if self.vector_store:
            query = context.reformulated_query or context.query
            
            # Check guardrail mode
            from app.config import settings
            guardrail_mode = getattr(settings, "domain_guardrail_mode", "soft").lower()
            
            # Get domain from context (specified or detected)
            domain_filter = context.specified_domain if context.specified_domain and context.specified_domain != "all" else None
            logger.info(f"Retrieving statutes for domain: {domain_filter} (guardrail mode: {guardrail_mode})")
            if not domain_filter and context.detected_domain:
                domain_filter = context.detected_domain
            
            semantic_results = []
            doc_results = []
            
            if guardrail_mode == "soft":
                # In soft mode, retrieve both domain-filtered and unfiltered search results
                # to cover cross-domain crossovers (like Family + Criminal for domestic violence).
                
                # A. Retrieve filtered results (prioritizing selected domain)
                filtered_statutes = await self.vector_store.search_statutes(
                    query=query,
                    act_codes=context.applicable_acts,
                    domain=domain_filter,
                    limit=3
                )
                filtered_docs = await self.vector_store.search_documents(
                    query=query,
                    domain=domain_filter,
                    limit=2
                )
                
                # B. Retrieve unfiltered results (unrestricted semantic matching)
                unfiltered_statutes = await self.vector_store.search_statutes(
                    query=query,
                    act_codes=None,
                    domain=None,
                    limit=4
                )
                unfiltered_docs = await self.vector_store.search_documents(
                    query=query,
                    domain=None,
                    limit=3
                )
                
                # Merge and preserve order (filtered first, then unfiltered)
                seen_statute_ids = set()
                for r in filtered_statutes + unfiltered_statutes:
                    r_id = r.get("id")
                    if r_id not in seen_statute_ids:
                        seen_statute_ids.add(r_id)
                        semantic_results.append(r)
                
                seen_doc_ids = set()
                for d in filtered_docs + unfiltered_docs:
                    d_id = d.get("id")
                    if d_id not in seen_doc_ids:
                        seen_doc_ids.add(d_id)
                        doc_results.append(d)
            else:
                # Standard search (hard filtered by domain)
                semantic_results = await self.vector_store.search_statutes(
                    query=query,
                    act_codes=context.applicable_acts,
                    domain=domain_filter,
                    limit=5
                )
                doc_results = await self.vector_store.search_documents(
                    query=query,
                    domain=domain_filter,
                    limit=3
                )
            
            # Add unique results
            existing_ids = {s.get("id") for s in retrieved_statutes}
            for result in semantic_results:
                if result.get("id") not in existing_ids:
                    retrieved_statutes.append(result)
            
            # Add document results as context
            for doc in doc_results:
                if doc.get("id") not in existing_ids:
                    retrieved_statutes.append({
                        "id": doc.get("id"),
                        "content_en": doc.get("content", ""),
                        "source": "document",
                        "domain": doc.get("domain", ""),
                        "filename": doc.get("filename", "")
                    })
        
        # 3. If no specific sections found, do keyword search in database
        if not retrieved_statutes:
            query = context.reformulated_query or context.query
            retrieved_statutes = await self.statute_service.search_statutes(
                query=query,
                act_codes=context.applicable_acts,
                limit=5
            )
            logger.info(f"Keyword search returned {len(retrieved_statutes)} results from database")
        
        # 4. Get IPC-BNS mappings for retrieved sections
        ipc_sections = [s for s in retrieved_statutes if s.get("act_code") == "IPC"]
        
        mappings = await self._get_cross_mappings(ipc_sections)
        
        # Update context
        context.statutes = retrieved_statutes
        context.ipc_bns_mappings = mappings
        
        logger.info(f"Retrieved {len(retrieved_statutes)} statutes, {len(mappings)} mappings from database")
        
        return context
    
    async def _get_cross_mappings(self, ipc_sections: List[Dict]) -> List[Dict]:
        """Get cross-mappings between IPC and BNS sections from database."""
        mappings = []
        
        for ipc in ipc_sections:
            section_num = ipc.get("section_number")
            if section_num:
                mapping = await self.statute_service.get_ipc_bns_mapping(section_num)
                if mapping:
                    # Format mapping for frontend
                    mappings.append({
                        "id": str(mapping.get("id", "")),
                        "ipc_section": mapping.get("ipc_section", ""),
                        "ipc_title": mapping.get("ipc_title", ""),
                        "ipc_content": mapping.get("ipc_content", ""),
                        "bns_section": mapping.get("bns_section", ""),
                        "bns_title": mapping.get("bns_title", ""),
                        "bns_content": mapping.get("bns_content", ""),
                        "changes": mapping.get("changes", []),
                        "punishment_change": {
                            "old": mapping.get("old_punishment", ""),
                            "new": mapping.get("new_punishment", ""),
                            "increased": mapping.get("punishment_increased", False)
                        } if mapping.get("punishment_changed") else None,
                        "mapping_type": mapping.get("mapping_type", "exact")
                    })
                    logger.info(f"Found mapping: IPC {section_num} -> BNS {mapping.get('bns_section')}")
        
        return mappings
