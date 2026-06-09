"""
NyayaShastra - Summarization Agent
Summarizes legal documents and extracts key information.
"""

from typing import Dict, Any, List, Optional
import logging
import re

from app.agents.base import BaseAgent, AgentContext
from app.schemas import AgentType

logger = logging.getLogger(__name__)


class SummarizationAgent(BaseAgent):
    """Agent for summarizing legal documents and extracting key information."""
    
    def __init__(self, llm_service=None):
        super().__init__()
        self.agent_type = AgentType.SUMMARY
        self.name = "Summarization"
        self.name_hi = "सारांश"
        self.description = "Summarizes legal documents and extracts key information"
        self.color = "#00bcd4"
        
        self.llm_service = llm_service
    
    async def process(self, context: AgentContext) -> AgentContext:
        """Process and summarize document if available."""
        
        # Ensure LLM service is available
        if not self.llm_service:
            try:
                from app.services.llm_service import get_llm_service
                self.llm_service = await get_llm_service()
            except Exception as e:
                logger.error(f"Failed to initialize LLM service in SummarizationAgent: {e}")
        
        # If there's a document to summarize
        if context.document_summary:
            # Already processed, enhance if possible
            context.document_summary = await self._enhance_summary(context.document_summary)
        
        # Summarize retrieved statutes for quick reference
        if context.statutes:
            context.statute_summaries = self._summarize_statutes(context.statutes)
        
        # Summarize case laws
        if context.case_laws:
            context.case_summaries = self._summarize_cases(context.case_laws)
        
        logger.info("Summarization completed")
        
        return context
    
    async def summarize_document(self, text: str, doc_type: str = "judgment") -> Dict[str, Any]:
        """Summarize a legal document."""
        
        summary = {
            "key_arguments": [],
            "verdict": None,
            "cited_sections": [],
            "parties": None,
            "court_name": None,
            "date": None,
            "judges": [],
            "legal_issues": [],
            "ratio_decidendi": None
        }
        
        # Extract parties (petitioner v. respondent)
        parties_match = re.search(
            r'([A-Za-z\s\.]+)\s*(?:v\.|vs\.?|versus)\s*([A-Za-z\s\.]+)',
            text[:1000],
            re.IGNORECASE
        )
        if parties_match:
            summary["parties"] = f"{parties_match.group(1).strip()} v. {parties_match.group(2).strip()}"
        
        # Extract court name
        court_patterns = [
            r'Supreme Court of India',
            r'High Court of [\w\s]+',
            r'[\w\s]+ High Court',
            r'District Court',
            r'Sessions Court'
        ]
        for pattern in court_patterns:
            match = re.search(pattern, text[:2000], re.IGNORECASE)
            if match:
                summary["court_name"] = match.group(0)
                break
        
        # Extract date
        date_match = re.search(
            r'(?:dated?|decided on|judgment dated?)\s*[:\-]?\s*(\d{1,2}[\-\/\.]\d{1,2}[\-\/\.]\d{4}|\d{1,2}\s+\w+\s+\d{4})',
            text,
            re.IGNORECASE
        )
        if date_match:
            summary["date"] = date_match.group(1)
        
        # Extract cited sections
        section_pattern = r'(?:Section|Sec\.|धारा|§)\s*(\d+[A-Za-z]?)\s*(?:of|,)?\s*(?:the\s+)?(IPC|BNS|CrPC|IT Act|Indian Penal Code|Bhartiya Nyaya Sanhita)?'
        citations = re.findall(section_pattern, text, re.IGNORECASE)
        seen = set()
        for section, act in citations:
            act = act.upper() if act else "IPC"
            key = f"{act}_{section}"
            if key not in seen:
                seen.add(key)
                summary["cited_sections"].append({"act": act, "section": section})
        
        # Extract judgment patterns for verdict
        verdict_patterns = [
            r'(?:appeal|petition|application)\s+(?:is\s+)?(?:hereby\s+)?(allowed|dismissed|partly allowed|remanded)',
            r'(?:we|court)\s+(?:hereby\s+)?(?:order|direct|hold)\s+that',
            r'conviction\s+(?:under\s+[^.]+)?\s*(?:is\s+)?(upheld|set aside|modified)',
            r'accused\s+is\s+(?:hereby\s+)?(acquitted|convicted)'
        ]
        
        for pattern in verdict_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                summary["verdict"] = match.group(0).strip().capitalize()
                break
        
        # Use LLM for deeper analysis if available
        if self.llm_service:
            llm_summary = await self._llm_summarize(text, doc_type)
            if llm_summary:
                summary["key_arguments"] = llm_summary.get("key_arguments", [])
                summary["legal_issues"] = llm_summary.get("legal_issues", [])
                summary["ratio_decidendi"] = llm_summary.get("ratio_decidendi")
                if not summary["verdict"]:
                    summary["verdict"] = llm_summary.get("verdict")
        else:
            # Fallback: Extract key sentences as arguments
            summary["key_arguments"] = self._extract_key_sentences(text)
        
        return summary
    
    async def _enhance_summary(self, summary: Dict) -> Dict:
        """Enhance an existing summary."""
        # Add any additional processing
        return summary
    
    def _summarize_statutes(self, statutes: List[Dict]) -> List[Dict]:
        """Create quick summaries of statutes."""
        summaries = []
        
        for statute in statutes:
            summary = {
                "section": statute.get("section_number"),
                "act": statute.get("act_code"),
                "title": statute.get("title_en"),
                "brief": self._create_brief(statute.get("content_en", "")),
                "punishment": statute.get("punishment_description")
            }
            summaries.append(summary)
        
        return summaries
    
    def _summarize_cases(self, cases: List[Dict]) -> List[Dict]:
        """Create quick summaries of case laws."""
        summaries = []
        
        for case in cases:
            summary = {
                "case_name": case.get("case_name"),
                "court": case.get("court_name"),
                "year": case.get("reporting_year"),
                "brief": case.get("summary_en", "")[:300],
                "key_holdings": case.get("key_holdings", [])[:3],
                "is_landmark": case.get("is_landmark", False)
            }
            summaries.append(summary)
        
        return summaries
    
    def _create_brief(self, content: str, max_length: int = 150) -> str:
        """Create a brief summary of content."""
        if not content:
            return ""
        
        # Get first sentence or truncate
        sentences = re.split(r'[.!?]', content)
        if sentences and len(sentences[0]) <= max_length:
            return sentences[0].strip() + "."
        
        return content[:max_length].strip() + "..."
    
    def _extract_key_sentences(self, text: str, max_sentences: int = 5) -> List[str]:
        """Extract key sentences from text as arguments."""
        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Key phrases that indicate important sentences
        key_phrases = [
            "held that", "court observed", "it was held",
            "issue before", "question of law", "appellant contended",
            "respondent submitted", "therefore", "accordingly",
            "we are of the view", "in our opinion"
        ]
        
        key_sentences = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(phrase in sentence_lower for phrase in key_phrases):
                if len(sentence) > 50 and len(sentence) < 500:
                    key_sentences.append(sentence.strip())
                    if len(key_sentences) >= max_sentences:
                        break
        
        return key_sentences
    
    async def _llm_summarize(self, text: str, doc_type: str) -> Optional[Dict]:
        """Use LLM to summarize document."""
        try:
            prompt = f"""Analyze this legal {doc_type} and extract:
1. Key arguments presented by each party (list format)
2. Main legal issues involved
3. The final verdict/decision
4. The ratio decidendi (principle of law established)

Document:
{text[:8000]}

Provide response in JSON format with keys: key_arguments, legal_issues, verdict, ratio_decidendi"""
            
            response = await self.llm_service.generate(prompt)
            # Parse JSON response
            import json
            return json.loads(response)
        except Exception as e:
            logger.error(f"LLM summarization failed: {e}")
            return None
