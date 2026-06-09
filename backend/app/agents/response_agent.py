"""
NyayaShastra - Response Synthesis Agent
Generates final comprehensive legal responses.
"""

from typing import Dict, Any, List, Optional
import logging
import re

from app.agents.base import BaseAgent, AgentContext
from app.schemas import AgentType

logger = logging.getLogger(__name__)


# Response templates
DISCLAIMER_EN = "\n\n⚖️ *Disclaimer: This information is for educational purposes only and does not constitute legal advice. Please consult a qualified legal professional for specific legal matters.*"

DISCLAIMER_HI = "\n\n⚖️ *अस्वीकरण: यह जानकारी केवल शैक्षिक उद्देश्यों के लिए है और कानूनी सलाह नहीं है। विशिष्ट कानूनी मामलों के लिए कृपया किसी योग्य कानूनी पेशेवर से परामर्श करें।*"


class ResponseSynthesisAgent(BaseAgent):
    """Agent for synthesizing final comprehensive responses."""
    
    def __init__(self, llm_service=None):
        super().__init__()
        self.agent_type = AgentType.RESPONSE
        self.name = "Response Synthesis"
        self.name_hi = "प्रतिक्रिया संश्लेषण"
        self.description = "Generates comprehensive legal responses"
        self.color = "#9c27b0"
        
        self.llm_service = llm_service

    def _determine_response_style(self, query: str) -> str:
        """Choose how structured the response should be."""
        text = query.lower()

        if any(word in text for word in ["citation", "cites", "sources", "source", "with citations", "legal basis"]):
            return "citations"
        if any(word in text for word in ["explain", "how", "why", "break down", "step by step", "detailed", "elaborate"]):
            return "explanatory"
        if any(word in text for word in ["compare", "difference", "vs", "versus", "compare with"]):
            return "comparison"
        if any(word in text for word in ["summary", "summarize", "brief", "short answer", "quick"]):
            return "brief"

        return "conversational"
    
    async def process(self, context: AgentContext) -> AgentContext:
        """Synthesize final response from all gathered information."""
        
        # Ensure LLM service is available
        if not self.llm_service:
            try:
                from app.services.llm_service import get_llm_service
                self.llm_service = await get_llm_service()
            except Exception as e:
                logger.error(f"Failed to initialize LLM service in ResponseSynthesisAgent: {e}")
        
        # Build response based on available data
        if self.llm_service and self.llm_service.provider:
            response = await self._generate_llm_response(context)
        else:
            response = self._generate_template_response(context)
        
        # Use primary response (in detected language) as the main content
        context.response = response.get("primary", response.get("en", ""))
        context.response_hi = response.get("hi", "")
        
        logger.info(f"Response synthesis completed in language: {response.get('detected_language', 'en')}")
        
        return context
    
    async def _generate_llm_response(self, context: AgentContext) -> Dict[str, str]:
        """Generate response using LLM and SystemPromptBuilder with strict domain guardrails."""
        try:
            from app.services.system_prompt import get_system_prompt
            # 1. Use centralized relevance guardrail from context (set by Query Agent with BM25)
            is_relevant = context.is_relevant
            rejection_message = context.rejection_message or ""
            
            # 2. Build the System Prompt with Context
            response_style = self._determine_response_style(context.query)
            docs = []
            for s in context.statutes:
                docs.append({
                    "content": s.get("content_en", ""),
                    "filename": s.get("filename") or s.get("act_code") or "Statute",
                    "category": s.get("domain", "")
                })
            
            system_prompt = get_system_prompt(
                user_query=context.query,
                documents=docs,
                sql_results=context.ipc_bns_mappings,
                fallback_message=rejection_message,
                selected_category=context.specified_domain,
                response_style=response_style
            )
            
            # 3. Handle strict rejection
            if not is_relevant and rejection_message:
                logger.warning(f"Domain mismatch detected. Query: {context.query}, Domain: {context.specified_domain}. Rejecting.")
                
                # If Hindi/Hinglish detected, translate rejection
                if context.detected_language == "hi":
                    rejection_message_hi = await self._translate_to_hindi(rejection_message)
                else:
                    rejection_message_hi = rejection_message # Fallback
                
                return {
                    "en": rejection_message,
                    "hi": rejection_message_hi,
                    "primary": rejection_message_hi if context.detected_language == "hi" else rejection_message,
                    "detected_language": context.detected_language or "en"
                }

            # 4. Generate response
            response_language = context.detected_language or "en"
            
            # We use a single prompt now that handles language mirroring
            messages = [{"role": "system", "content": system_prompt}]
            
            # Append chat history messages for conversational continuity
            # Limit history to the last 6 messages to keep the context size optimal
            for msg in context.chat_history[-6:]:
                role = msg.get("role")
                content = msg.get("content", "")
                
                # If assistant, use Hindi response if response language is Hindi
                if role == "assistant" and response_language == "hi" and msg.get("content_hi"):
                    content = msg.get("content_hi")
                
                if role in ("user", "assistant") and content:
                    messages.append({"role": role, "content": content})
            
            # Append the current query
            messages.append({"role": "user", "content": context.query})
            
            primary_response = await self.llm_service.generate_chat(messages)
            
            # Generate Hindi translation if not already in Hindi
            secondary_response = ""
            if response_language != "hi":
                translate_prompt = f"Translate this legal response to Hindi, maintaining professional legal terminology:\n\n{primary_response}"
                secondary_response = await self.llm_service.generate(translate_prompt)
            else:
                secondary_response = primary_response
            
            # 5. Extract takeaways and update context citations
            parsed_citations = self._parse_takeaways(primary_response)
            for c_info in parsed_citations:
               # Clean the takeaway text
               takeaway = self._clean_legal_text(c_info['takeaway'])
               
               # Find matching citation in context and add takeaway
               for existing_c in context.citations:
                   # Match by source name or section number
                   match_source = c_info['source'].lower() in existing_c.get('title', '').lower()
                   match_section = c_info['section'] in existing_c.get('title', '')
                   
                   if match_source and match_section:
                       existing_c['takeaway'] = takeaway
                       # Also clean the existing excerpt if it's messy
                       if existing_c.get('excerpt'):
                           existing_c['excerpt'] = self._clean_legal_text(existing_c['excerpt'])
                       break
            
            # Clean all context excerpts regardless of takeaway match
            for c in context.citations:
                if c.get('excerpt'):
                    c['excerpt'] = self._clean_legal_text(c['excerpt'])
            
            # Translate to English if needed (before stripping)
            english_response = ""
            if response_language == "en":
                english_response = primary_response
            else:
                english_response = await self.llm_service.generate(f"Translate this to English:\n\n{primary_response}")
                
            # Keep the response natural unless the user asked for citations or a formal breakdown.
            if response_style not in ("citations", "comparison", "explanatory"):
                primary_response = self._normalize_conversational_response(primary_response)
                secondary_response = self._normalize_conversational_response(secondary_response)
                english_response = self._normalize_conversational_response(english_response)
            elif not self._should_keep_inline_citations(context.query):
                logger.info("User did not request inline citations. Stripping citation blocks from response text.")
                primary_response = self._strip_citations_from_text(primary_response)
                secondary_response = self._strip_citations_from_text(secondary_response)
                english_response = self._strip_citations_from_text(english_response)
                
            return {
                "en": english_response,
                "hi": secondary_response,
                "primary": primary_response,
                "detected_language": response_language
            }
        except Exception as e:
            logger.error(f"LLM response generation failed: {e}")
            return self._generate_template_response(context)
    
    def _build_llm_context(self, context: AgentContext) -> str:
        """Build context string for LLM."""
        parts = []
        
        # Add statutes
        if context.statutes:
            parts.append("## Relevant Statutes:")
            for statute in context.statutes[:5]:
                parts.append(f"- {statute.get('act_code')} Section {statute.get('section_number')}: {statute.get('title_en')}")
                parts.append(f"  Content: {statute.get('content_en', '')[:300]}...")
        
        # Add IPC-BNS mappings
        if context.ipc_bns_mappings:
            parts.append("\n## IPC to BNS Mappings:")
            for mapping in context.ipc_bns_mappings:
                parts.append(f"- IPC {mapping.get('ipc_section')} → BNS {mapping.get('bns_section')}")
                if mapping.get('changes'):
                    for change in mapping['changes']:
                        parts.append(f"  • {change.get('description')}")
        
        # Add case laws
        if context.case_laws:
            parts.append("\n## Relevant Case Laws:")
            for case in context.case_laws[:3]:
                landmark = " (LANDMARK)" if case.get('is_landmark') else ""
                parts.append(f"- {case.get('case_name')}{landmark}")
                if case.get('summary_en'):
                    parts.append(f"  Summary: {case['summary_en'][:200]}...")
        
        # Add regulatory notes
        if hasattr(context, 'regulatory_notes') and context.regulatory_notes:
            parts.append(f"\n## Jurisdiction: {context.regulatory_notes.get('domain', 'N/A')}")
        
        return "\n".join(parts)
    
    def _generate_template_response(self, context: AgentContext) -> Dict[str, str]:
        """Generate response using templates (fallback)."""
        
        response_parts_en = []
        response_parts_hi = []
        
        # Opening line
        response_parts_en.append(f"Here’s the practical answer to your question about \"{context.query}\":\n")
        response_parts_hi.append(f"आपके सवाल \"{context.query}\" का व्यावहारिक जवाब यह है:\n")
        
        # Statutes section
        if context.statutes:
            response_parts_en.append("The main legal provisions likely relevant are:\n")
            response_parts_hi.append("मुख्य रूप से ये कानूनी प्रावधान लागू हो सकते हैं:\n")
            
            for statute in context.statutes[:3]:
                act = statute.get("act_code", "")
                section = statute.get("section_number", "")
                title = statute.get("title_en", "")
                content = statute.get("content_en", "")
                
                response_parts_en.append(f"- {act} Section {section} - {title}: {content}\n")
                
                title_hi = statute.get("title_hi", title)
                content_hi = statute.get("content_hi", content)
                response_parts_hi.append(f"- {act} धारा {section} - {title_hi}: {content_hi}\n")
                
                # Punishment info
                if statute.get("punishment_description"):
                    response_parts_en.append(f"  Punishment: {statute['punishment_description']}\n")
                    response_parts_hi.append(f"  सजा: {statute['punishment_description']}\n")
        
        # IPC-BNS Comparison
        if context.ipc_bns_mappings:
            response_parts_en.append("\nIf you want the IPC to BNS mapping, the key transitions are:\n")
            response_parts_hi.append("\nAgar aap IPC aur BNS mapping chahte hain, to main transitions ye hain:\n")
            
            for mapping in context.ipc_bns_mappings[:2]:
                ipc = mapping.get("ipc_section", "")
                bns = mapping.get("bns_section", "")
                
                response_parts_en.append(f"- IPC Section {ipc} → BNS Section {bns}\n")
                response_parts_hi.append(f"- IPC धारा {ipc} → BNS धारा {bns}\n")
                
                changes = mapping.get("changes", [])
                if changes:
                    response_parts_en.append("  Key changes:\n")
                    response_parts_hi.append("  मुख्य बदलाव:\n")
                    for change in changes:
                        response_parts_en.append(f"  - {change.get('description', '')}\n")
                        response_parts_hi.append(f"  - {change.get('description', '')}\n")
                
                punishment = mapping.get("punishment_change")
                if punishment:
                    old = punishment.get("old", "")
                    new = punishment.get("new", "")
                    response_parts_en.append(f"\n  Punishment change: {old} → {new}\n")
                    response_parts_hi.append(f"\n  सजा में परिवर्तन: {old} → {new}\n")
        
        # Case Laws
        if context.case_laws:
            response_parts_en.append("\nA few relevant cases are worth noting:\n")
            response_parts_hi.append("\nकुछ संबंधित मामले भी ध्यान देने योग्य हैं:\n")
            
            for case in context.case_laws[:3]:
                name = case.get("case_name", "")
                court = case.get("court_name", "")
                year = case.get("reporting_year", "")
                summary = case.get("summary_en", "")
                landmark = " ⭐ LANDMARK" if case.get("is_landmark") else ""
                
                response_parts_en.append(f"- {name}{landmark} ({court}, {year}): {summary}\n")
                
                name_hi = case.get("case_name_hi", name)
                summary_hi = case.get("summary_hi", summary)
                landmark_hi = " ⭐ ऐतिहासिक" if case.get("is_landmark") else ""
                response_parts_hi.append(f"- {name_hi}{landmark_hi} ({court}, {year}): {summary_hi}\n")
                
                # Key holdings
                holdings = case.get("key_holdings", [])
                if holdings:
                    response_parts_en.append("  Key holdings:\n")
                    response_parts_hi.append("  मुख्य निर्णय:\n")
                    for holding in holdings[:3]:
                        response_parts_en.append(f"    - {holding}\n")
                        response_parts_hi.append(f"    - {holding}\n")
        
        # Regulatory Notes
        if hasattr(context, 'regulatory_notes') and context.regulatory_notes:
            notes = context.regulatory_notes
            
            response_parts_en.append("\nFor context, the relevant regulatory landscape includes:\n")
            response_parts_hi.append("\nसंदर्भ के लिए, संबंधित नियामक ढांचा यह है:\n")
            
            if notes.get("applicable_acts"):
                response_parts_en.append(f"- Applicable laws: {', '.join(notes['applicable_acts'][:5])}\n")
                response_parts_hi.append(f"- लागू कानून: {', '.join(notes['applicable_acts'][:5])}\n")
            
            if notes.get("key_authorities"):
                response_parts_en.append(f"- Key authorities: {', '.join(notes['key_authorities'][:4])}\n")
                response_parts_hi.append(f"- मुख्य प्राधिकरण: {', '.join(notes['key_authorities'][:4])}\n")
        
        # Citations reference
        if context.citations:
            response_parts_en.append("\nIf you want, I can also list the sources I relied on:\n")
            response_parts_hi.append("\nAgar chahen, main sources bhi alag se list kar sakta hoon:\n")
            
            for i, citation in enumerate(context.citations[:5], 1):
                response_parts_en.append(f"- {citation.get('title', '')} ({citation.get('source_name', '')}) - {citation.get('url', '')}\n")
                response_parts_hi.append(f"- {citation.get('title_hi') or citation.get('title', '')} ({citation.get('source_name', '')}) - {citation.get('url', '')}\n")
        
        # Join all parts
        response_en = self._normalize_conversational_response("".join(response_parts_en)) + DISCLAIMER_EN
        response_hi = self._normalize_conversational_response("".join(response_parts_hi)) + DISCLAIMER_HI
        
        return {
            "en": response_en,
            "hi": response_hi
        }
    
    async def _verify_relevance_with_llm(self, query: str, domain: str) -> bool:
        """Reliable Method: Verify query relevance to domain using LLM."""
        if not self.llm_service:
            return False
            
        prompt = f"""Task: Determine if the following legal query is relevant to the "{domain}" domain of Indian law.
Relevant topics for "{domain}" include:
- traffic: Vehicle rules, accidents, fines, licenses, road safety.
- criminal: Murder, theft, crimes, FIR, bail, prison.
- it_cyber: Hacking, data privacy, online fraud.
- civil_family: Divorce, marriage, inheritance, property disputes.
- corporate: Companies, tax, business contracts.
- constitutional: Rights, Supreme Court, Articles.

Query: "{query}"

Is this query relevant to the "{domain}" domain? 
Answer with ONLY "YES" or "NO". Keep it simple.
"""
        try:
            response = await self.llm_service.generate(prompt, max_tokens=10, temperature=0.1)
            result = response.strip().upper()
            logger.info(f"Reliable LLM Check for '{domain}': {result}")
            return "YES" in result
        except Exception as e:
            logger.error(f"Reliable check failed: {e}")
            return False

    async def _translate_to_hindi(self, text: str) -> str:
        """Translate text to Hindi using LLM or fallback."""
        if self.llm_service:
            try:
                prompt = f"Translate to Hindi, maintaining legal terminology:\n\n{text}"
                return await self.llm_service.generate(prompt)
            except Exception as e:
                logger.warning(f"Hindi translation failed: {e}")
        return text  # Return English as fallback

    def _normalize_conversational_response(self, text: str) -> str:
        """Lightly clean overly rigid output while preserving useful content."""
        cleaned = re.sub(r'^\s*#{1,6}\s*', '', text, flags=re.MULTILINE)
        cleaned = re.sub(r'\*\*(.*?)\*\*', r'\1', cleaned)
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        return cleaned.strip()

    def _parse_takeaways(self, response_text: str) -> List[Dict[str, str]]:
        """Parse structured citation blocks to extract takeaways with robust regex."""
        results = []
        # Split by the citation header
        blocks = re.split(r'📌 \*\*(?:Citation|Hawaala|उद्धरण):\*\*', response_text)
        
        for block in blocks[1:]:
            try:
                # More flexible regex to handle markdown variations like "- **Source:**" or "Source:"
                source_match = re.search(r'(?:- \*\*)?Source:\s*\*\*(.*?)(?:\*\*|\n)', block, re.IGNORECASE)
                if not source_match:
                    source_match = re.search(r'Source:\s*(.*?)(?:\n|$)', block, re.IGNORECASE)
                
                section_match = re.search(r'(?:- \*\*)?Section:\s*\*\*(.*?)(?:\*\*|\n)', block, re.IGNORECASE)
                if not section_match:
                    section_match = re.search(r'Section:\s*(.*?)(?:\n|$)', block, re.IGNORECASE)
                
                # Takeaway regex - handle English, Hindi, and common labels
                takeaway_patterns = [
                    r'(?:- \*\*)?Takeaway:\s*\*\*(.*?)(?:\*\*|\n|$)',
                    r'(?:- \*\*)?Takeaway:\s*(.*?)(?:\n|$)',
                    r'(?:- \*\*)?निष्कर्ष:\s*\*\*(.*?)(?:\*\*|\n|$)',
                    r'(?:- \*\*)?निष्कर्ष:\s*(.*?)(?:\n|$)',
                    r'Takeaway:\s*(.*?)(?:\n\n|\n$)'
                ]
                
                takeaway = ""
                for pattern in takeaway_patterns:
                    match = re.search(pattern, block, re.IGNORECASE | re.DOTALL)
                    if match:
                        takeaway = match.group(1).strip()
                        break
                
                if source_match and section_match and takeaway:
                    results.append({
                        "source": source_match.group(1).strip(),
                        "section": section_match.group(1).strip(),
                        "takeaway": takeaway
                    })
            except Exception as e:
                logger.warning(f"Failed to parse citation block: {e}")
                
        return results

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
        
        # Fix multiple spaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _should_keep_inline_citations(self, query: str) -> bool:
        """Check if the user explicitly requested citations inside the chat text."""
        query_lower = query.lower()
        keywords = ["inline citation", "citation inside", "in the chat", "in-chat citation", "show citation", "with citation"]
        return any(kw in query_lower for kw in keywords)

    def _strip_citations_from_text(self, text: str) -> str:
        """Strip raw citation blocks from response text to make it clean and conversational."""
        if not text:
            return ""
        
        lines = text.split('\n')
        cleaned_lines = []
        skip_mode = False
        
        # Keywords that indicate we are inside a citation block
        citation_keywords = ["source:", "section:", "quote:", "takeaway:", "hawaala:", "निष्कर्ष:", "पाठ:", "स्रोत:"]
        
        for line in lines:
            line_stripped = line.strip().lower()
            
            # Start skipping when we see the pin emoji with Citation/Hawaala/उद्धरण
            if "📌" in line and any(kw in line_stripped for kw in ["citation", "hawaala", "उद्धरण"]):
                skip_mode = True
                continue
                
            if skip_mode:
                # If we are in skip mode, check if the line belongs to the citation block
                # A line belongs if it is empty, or starts with one of our citation keywords
                is_citation_line = (
                    line_stripped == "" or 
                    any(line_stripped.startswith(kw) or 
                        line_stripped.startswith("- " + kw) or 
                        line_stripped.startswith("- **" + kw) or 
                        line_stripped.startswith("**" + kw)
                        for kw in citation_keywords)
                )
                if is_citation_line:
                    continue
                else:
                    # We hit a line that is not part of the citation block. Stop skipping.
                    skip_mode = False
            
            cleaned_lines.append(line)
            
        # Reconstruct and clean up multiple newlines
        result = '\n'.join(cleaned_lines)
        result = re.sub(r'\n{3,}', '\n\n', result).strip()
        return result
