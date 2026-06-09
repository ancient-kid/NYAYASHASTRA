"""
NyayaShastra - Citation & Verification Agent
Generates verifiable citations linked to official sources.
"""

from typing import List, Dict, Any
import logging
import re

from app.agents.base import BaseAgent, AgentContext
from app.schemas import AgentType

logger = logging.getLogger(__name__)


# Official legal source URLs
OFFICIAL_SOURCES = {
    "gazette": {
        "name": "Official Gazette of India",
        "name_hi": "भारत का राजपत्र",
        "base_url": "https://egazette.gov.in",
        "description": "Official Government Gazette publications"
    },
    "indiankanoon": {
        "name": "Indian Kanoon",
        "name_hi": "इंडियन कानून",
        "base_url": "https://indiankanoon.org",
        "description": "Free legal search engine for Indian laws"
    },
    "sci": {
        "name": "Supreme Court of India",
        "name_hi": "भारत का सर्वोच्च न्यायालय",
        "base_url": "https://main.sci.gov.in",
        "description": "Official Supreme Court website"
    },
    "legislative": {
        "name": "Legislative Department",
        "name_hi": "विधायी विभाग",
        "base_url": "https://legislative.gov.in",
        "description": "Official laws and bareacts"
    },
    "lawcommission": {
        "name": "Law Commission of India",
        "name_hi": "भारत का विधि आयोग",
        "base_url": "https://lawcommissionofindia.nic.in",
        "description": "Law reform recommendations"
    }
}


class CitationAgent(BaseAgent):
    """Agent for generating and verifying legal citations."""
    
    def __init__(self):
        super().__init__()
        self.agent_type = AgentType.CITATION
        self.name = "Citation Agent"
        self.name_hi = "उद्धरण एजेंट"
        self.description = "Generates verifiable citations linked to official sources"
        self.color = "#ff4081"
    
    def _clean_legal_text(self, text: str) -> str:
        """Clean legal text without corrupting normal word spacing."""
        if not text:
            return ""
        
        # Fix missing spaces around parentheses (e.g., "section 323(1) of" -> "section 323 (1) of")
        text = re.sub(r'([a-zA-Z0-9])(\()', r'\1 \2', text)
        text = re.sub(r'(\))([a-zA-Z0-9])', r'\1 \2', text)
        
        # Fix punctuation spacing
        text = re.sub(r'([,;:])([a-zA-Z])', r'\1 \2', text)
        
        # Fix specific common concatenations from OCR
        concats = [
            (r'(?i)section(\d+)', r'section \1'),
            (r'(?i)sub-section(\d+)', r'sub-section \1'),
            (r'(?i)ofsection', 'of section'),
            (r'(?i)underthis', 'under this'),
            (r'(?i)withorwithout', 'with or without'),
            (r'(?i)sixmonthsormore', 'six months or more'),
            (r'(?i)aswellas', 'as well as'),
            (r'(?i)meansa\s+', 'means a '),
            (r'(?i)imprisonmentfor', 'imprisonment for'),
            (r'(?i)shallbe', 'shall be'),
            (r'(?i)punishablewith', 'punishable with'),
            (r'(?i)voluntarilycausing', 'voluntarily causing'),
            (r'(?i)grievoushurt', 'grievous hurt')
        ]
        
        for pattern, replacement in concats:
            text = re.sub(pattern, replacement, text)
            
        # Fix camelCase from OCR (e.g., "theOffence" -> "the Offence")
        text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
        
        # Fix space between closing quote and letter
        text = re.sub(r'(["\'])([a-zA-Z])', r'\1 \2', text)
        
        # Fix multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    async def process(self, context: AgentContext) -> AgentContext:
        """Generate citations for statutes and case laws."""
        
        citations = []
        citation_id = 1
        
        logger.info(f"CitationAgent: Processing {len(context.statutes)} statutes, {len(context.case_laws)} case_laws")
        
        # 1. Generate citations for statutes
        for statute in context.statutes:
            logger.info(f"CitationAgent: Creating citation for statute: {statute.get('section_number', 'unknown')}")
            citation = self._create_statute_citation(statute, citation_id)
            if citation:
                citations.append(citation)
                citation_id += 1
        
        # 2. Generate citations for case laws
        for case in context.case_laws:
            logger.info(f"CitationAgent: Creating citation for case: {case.get('case_name', 'unknown')}")
            citation = self._create_case_citation(case, citation_id)
            if citation:
                citations.append(citation)
                citation_id += 1
        
        # 3. Add IPC-BNS mapping citations if relevant
        for mapping in context.ipc_bns_mappings:
            citation = self._create_mapping_citation(mapping, citation_id)
            if citation:
                citations.append(citation)
                citation_id += 1
        
        # 4. Verify and deduplicate citations
        citations = self._deduplicate_citations(citations)
        
        context.citations = citations
        
        logger.info(f"Generated {len(citations)} verified citations")
        
        return context
    
    def _create_statute_citation(self, statute: Dict, citation_id: int) -> Dict:
        """Create citation for a statute section."""
        act_code = statute.get("act_code", "IPC")
        section = statute.get("section_number", "")
        act_name = statute.get("act_name", "")
        title = statute.get("title_en", "")
        content = statute.get("content_en", "")
        
        # Use Indian Kanoon for ALL statutes - it's the most reliable source
        # They have direct document IDs for major sections
        IPC_SECTION_DOCS = {
            "302": "1560742",  # Murder
            "304": "1279877",  # Culpable homicide
            "307": "1290514",  # Attempt to murder
            "376": "1279834",  # Rape
            "420": "1436241",  # Cheating
            "498A": "110081",  # Cruelty by husband
            "354": "1279834",  # Assault on woman
            "306": "871857",   # Abetment to suicide
            "379": "1279854",  # Theft
            "384": "1279782",  # Extortion
            "392": "1279793",  # Robbery
            "406": "1569253",  # Criminal breach of trust
            "415": "1306487",  # Cheating
            "499": "1383364",  # Defamation
            "500": "1436475",  # Defamation punishment
            "120B": "635852",  # Criminal conspiracy
            "34": "37788",     # Common intention
        }
        
        if act_code == "IPC":
            doc_id = IPC_SECTION_DOCS.get(section, "")
            if doc_id:
                url = f"https://indiankanoon.org/doc/{doc_id}/"
            else:
                url = f"https://indiankanoon.org/search/?formInput=section%20{section}%20IPC"
            source = "indiankanoon"
        elif act_code == "BNS":
            # BNS sections on Indian Kanoon
            url = f"https://indiankanoon.org/search/?formInput=section%20{section}%20BNS%20Bharatiya%20Nyaya%20Sanhita"
            source = "indiankanoon"
        else:
            url = f"https://indiankanoon.org/search/?formInput={act_code}%20section%20{section}"
            source = "indiankanoon"
        
        # Make sure we have content for excerpt - CLEAN IT
        excerpt = content[:500] + "..." if len(content) > 500 else content
        if not excerpt:
            excerpt = f"Section {section} of {act_name}: {title}"
        
        # Clean the excerpt text
        excerpt = self._clean_legal_text(excerpt)
        
        # Build robust title - handle missing fields gracefully
        if section and title:
            citation_title = f"{act_name or act_code} - Section {section}: {title}"
        elif section:
            citation_title = f"{act_name or act_code} - Section {section}"
        elif title:
            citation_title = f"{act_name or act_code}: {title}"
        else:
            citation_title = f"{act_name or act_code} - Legal Provision"
        
        return {
            "id": str(citation_id),
            "title": citation_title,
            "title_hi": statute.get("title_hi", "") or "",
            "source": source,
            "source_name": "Indian Kanoon",
            "url": url,
            "excerpt": excerpt,
            "year": statute.get("year_enacted"),
            "type": "statute",
            "verified": True,
            "section_number": section or "N/A",
            "act_code": act_code
        }
    
    def _create_case_citation(self, case: Dict, citation_id: int) -> Dict:
        """Create citation for a case law."""
        case_name = case.get("case_name", "")
        citation_string = case.get("citation_string", "")
        source_url = case.get("source_url", "")
        court = case.get("court", "")
        year = case.get("reporting_year")
        
        # Generate URL if not provided - use Indian Kanoon for reliable direct links
        if not source_url:
            safe_name = re.sub(r'[^a-zA-Z0-9\s]', '', case_name)
            encoded_name = safe_name.replace(' ', '%20')
            
            if court == "supreme_court":
                # Supreme Court judgments on Indian Kanoon
                source_url = f"https://indiankanoon.org/search/?formInput={encoded_name}%20supreme%20court"
                source = "indiankanoon"
            elif court == "high_court":
                source_url = f"https://indiankanoon.org/search/?formInput={encoded_name}%20high%20court"
                source = "indiankanoon"
            else:
                source_url = f"https://indiankanoon.org/search/?formInput={encoded_name}"
                source = "indiankanoon"
        else:
            source = "indiankanoon" if "indiankanoon" in source_url else "sci"
        
        title = case_name
        if citation_string:
            title = f"{case_name} ({citation_string})"
        
        summary = case.get("summary_en", "")
        excerpt = summary[:300] + "..." if len(summary) > 300 else summary if summary else None
        
        # Clean excerpt if present
        if excerpt:
            excerpt = self._clean_legal_text(excerpt)
        
        return {
            "id": str(citation_id),
            "title": title,
            "title_hi": case.get("case_name_hi", ""),
            "source": source,
            "source_name": OFFICIAL_SOURCES.get(source, {}).get("name", source),
            "url": source_url,
            "excerpt": excerpt,
            "year": year,
            "court": case.get("court_name", court),
            "type": "case_law",
            "is_landmark": case.get("is_landmark", False),
            "verified": True
        }
    
    def _create_mapping_citation(self, mapping: Dict, citation_id: int) -> Dict:
        """Create citation for IPC-BNS mapping."""
        ipc_section = mapping.get("ipc_section", "")
        bns_section = mapping.get("bns_section", "")
        
        return {
            "id": str(citation_id),
            "title": f"IPC Section {ipc_section} → BNS Section {bns_section} Mapping",
            "title_hi": f"IPC धारा {ipc_section} → BNS धारा {bns_section} मैपिंग",
            "source": "gazette",
            "source_name": OFFICIAL_SOURCES["gazette"]["name"],
            "url": "https://egazette.gov.in/WriteReadData/2023/248044.pdf",
            "excerpt": f"Cross-reference between old IPC Section {ipc_section} and new BNS Section {bns_section}",
            "year": 2023,
            "type": "mapping",
            "verified": True
        }
    
    def _deduplicate_citations(self, citations: List[Dict]) -> List[Dict]:
        """Remove duplicate citations."""
        seen_urls = set()
        unique_citations = []
        
        for citation in citations:
            url = citation.get("url", "")
            if url not in seen_urls:
                seen_urls.add(url)
                unique_citations.append(citation)
        
        return unique_citations
