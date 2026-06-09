"""
NyayaShastra - Query Understanding Agent
Analyzes user queries to detect language, legal domain, and reformulate for precision.
"""

import re
from typing import List, Dict, Any, Optional
import logging

from app.agents.base import BaseAgent, AgentContext
from app.schemas import AgentType, LegalDomain

logger = logging.getLogger(__name__)


# Legal domain keywords moved to bm25_service.py corpus

# IPC/BNS section patterns
SECTION_PATTERN = re.compile(r'(?:section|sec|धारा|§)\s*(\d+[a-zA-Z]?)', re.IGNORECASE)
IPC_PATTERN = re.compile(r'\b(?:ipc|indian penal code|भारतीय दंड संहिता)\b', re.IGNORECASE)
BNS_PATTERN = re.compile(r'\b(?:bns|bhartiya nyaya sanhita|भारतीय न्याय संहिता)\b', re.IGNORECASE)


def map_to_legal_domain(domain_str: Optional[str]) -> Optional[LegalDomain]:
    if not domain_str:
        return None
    normalized = domain_str.lower().strip()
    if normalized == "criminal":
        return LegalDomain.CRIMINAL
    elif normalized in ("civil", "family", "civil_family"):
        return LegalDomain.CIVIL_FAMILY
    elif normalized == "corporate":
        return LegalDomain.CORPORATE
    elif normalized in ("it_cyber", "cyber", "it"):
        return LegalDomain.IT_CYBER
    elif normalized in ("environmental", "environment"):
        return LegalDomain.ENVIRONMENT
    elif normalized in ("constitutional",):
        return LegalDomain.CONSTITUTIONAL
    elif normalized == "property":
        return LegalDomain.PROPERTY
    elif normalized == "traffic":
        return LegalDomain.TRAFFIC
    elif normalized == "all":
        return LegalDomain.ALL
    
    try:
        for member in LegalDomain:
            if member.value.lower() == normalized or member.name.lower() == normalized:
                return member
    except:
        pass
    return None



class QueryUnderstandingAgent(BaseAgent):
    """Agent for understanding and analyzing user queries."""
    
    def __init__(self):
        super().__init__()
        self.agent_type = AgentType.QUERY
        self.name = "Query Understanding"
        self.name_hi = "प्रश्न समझ"
        self.description = "Analyzes queries for language, domain, and intent"
        self.color = "#00d4ff"
        self.domain_classifier = None # Async init

    async def _init_classifier(self):
        if not self.domain_classifier:
            from app.services.bm25_service import get_domain_classifier
            self.domain_classifier = await get_domain_classifier()
    
    async def process(self, context: AgentContext) -> AgentContext:
        """Process the query to understand intent and context."""
        
        query = context.query.lower()
        
        # 1. Detect language
        context.detected_language = self._detect_language(context.query)
        logger.info(f"Detected language: {context.detected_language}")
        
        # 2. Extract section numbers
        sections = self._extract_sections(context.query)
        if sections:
            context.entities.extend([{"type": "section", "value": s} for s in sections])
            logger.info(f"Extracted sections: {sections}")
        
        # 3. Detect legal domain
        await self._init_classifier()
        predicted_domain, confidence, all_scores = await self.domain_classifier.classify(query)
        
        # Check guardrail mode from settings
        from app.config import settings
        guardrail_mode = getattr(settings, "domain_guardrail_mode", "soft").lower()
        logger.info(f"Domain guardrail mode: {guardrail_mode}")
        
        if context.specified_domain and context.specified_domain != "all":
            context.detected_domain = context.specified_domain
            logger.info(f"Using specified domain: {context.detected_domain}")
            
            if guardrail_mode == "strict":
                # Original strict guardrail check
                selected_score = all_scores.get(context.specified_domain, 0)
                top_score = confidence
                is_match = (predicted_domain == context.specified_domain)
                is_close = (selected_score > (top_score * 0.5) and selected_score > 0.1)
                is_strong = (selected_score > 0.2)
                
                if not (is_match or is_close or is_strong):
                    context.is_relevant = False
                    context.rejection_message = (
                        f"⚠️ This query appears to be related to **{predicted_domain}** law, "
                        f"not **{context.specified_domain}** law. "
                        f"To ensure legal accuracy, I only answer {context.specified_domain} queries in this mode. "
                        f"Please switch to the **{predicted_domain}** domain for a detailed response."
                    )
                    logger.warning(f"Strict domain guardrail triggered: query '{query}' is {predicted_domain}, not {context.specified_domain} (scores: top={top_score:.2f}, selected={selected_score:.2f})")
            
            elif guardrail_mode == "llm":
                # LLM-based guardrail validation
                try:
                    from app.services.llm_service import get_llm_service
                    llm_service = await get_llm_service()
                    
                    sys_prompt = """You are a legal domain classifier. Your task is to check if a user query belongs to or is related to a target legal domain.
                    
The possible legal domains are:
- criminal: Criminal law, murder, theft, assault, police, FIR, bail, IPC, BNS, etc.
- civil: Civil law, family law, marriage, divorce, child custody, alimony, succession, inheritance, consumer protection, etc.
- corporate: Business contracts, Company Act, tax, corporate governance, arbitration, mergers, ROC, IBC, etc.
- it_cyber: Cyber law, IT Act, hacking, phishing, data privacy, social media defamation, computer fraud, etc.
- property: Ownership, lease, landlord-tenant disputes, eviction, sale deeds, RERA, registration, mortgages, etc.
- constitutional: Fundamental rights, writs, PIL, articles of constitution, election laws, supreme court, high court, etc.
- environment: Environment protection, pollution, forest conservation, NGT, wildlife, EIA, etc.
- traffic: Road accidents, traffic violation fines, motor vehicles act, driving license, RTO rules, hit and run, etc.

Given the USER QUERY and the SELECTED TARGET DOMAIN:
If the query is related to the selected target domain (even partially, implicitly, or as a crossover/intersection like domestic violence which is both family/civil and criminal), reply with exactly 'YES'.
If the query is completely unrelated to the selected target domain, reply with 'NO | <explanation of why and what domain it actually is>'.
Format: 'YES' or 'NO | <explanation>'"""
                    
                    user_prompt = f"USER QUERY: {context.query}\nSELECTED TARGET DOMAIN: {context.specified_domain}"
                    messages = [
                        {"role": "system", "content": sys_prompt},
                        {"role": "user", "content": user_prompt}
                    ]
                    
                    llm_response = await llm_service.generate_chat(messages, max_tokens=100, temperature=0.0)
                    llm_response = llm_response.strip()
                    logger.info(f"LLM domain validation response: {llm_response}")
                    
                    if llm_response.startswith("NO"):
                        context.is_relevant = False
                        explanation = llm_response.split("|")[1].strip() if "|" in llm_response else f"This query does not match the selected domain **{context.specified_domain}**."
                        context.rejection_message = f"⚠️ {explanation}\n\nPlease switch to the correct domain to get a response."
                        logger.warning(f"LLM domain guardrail triggered: query '{context.query}' rejected for domain {context.specified_domain}")
                except Exception as e:
                    logger.error(f"Error in LLM domain guardrail: {e}")
                    pass
                    
            # For "soft" and "none" modes, we do not reject the query.
        else:
            context.detected_domain = predicted_domain
            logger.info(f"Automatically detected domain: {context.detected_domain} (conf: {confidence:.2f})")
        
        # 4. Detect if IPC or BNS specific
        is_ipc = bool(IPC_PATTERN.search(context.query))
        is_bns = bool(BNS_PATTERN.search(context.query))
        
        if is_ipc:
            context.applicable_acts.append("IPC")
        if is_bns:
            context.applicable_acts.append("BNS")
            
        # Add acts based on domain if none specified
        if not context.applicable_acts and context.detected_domain:
            from app.agents.regulatory_agent import JURISDICTION_ACTS
            try:
                # Convert string to LegalDomain enum to match keys in JURISDICTION_ACTS
                domain_enum = map_to_legal_domain(context.detected_domain)
                if domain_enum:
                    context.applicable_acts.extend(JURISDICTION_ACTS.get(domain_enum, []))
            except Exception as e:
                logger.warning(f"Error getting acts for domain {context.detected_domain}: {e}")
        
        # If still no acts and sections found, default to both criminal codes
        if not context.applicable_acts and sections:
            context.applicable_acts.extend(["IPC", "BNS"])
        
        # 5. Extract keywords
        context.keywords = self._extract_keywords(context.query)
        
        # 6. Reformulate query for better retrieval
        context.reformulated_query = await self._reformulate_query(context)
        
        return context
    
    def _detect_language(self, text: str) -> str:
        """Detect the language of the text using Unicode script detection.
        Supports multiple Indian and international languages."""
        
        # Language detection based on Unicode character ranges
        language_patterns = {
            # Indian Languages
            "hi": r'[\u0900-\u097F]',  # Devanagari (Hindi, Marathi, Sanskrit)
            "ta": r'[\u0B80-\u0BFF]',  # Tamil
            "te": r'[\u0C00-\u0C7F]',  # Telugu
            "bn": r'[\u0980-\u09FF]',  # Bengali
            "gu": r'[\u0A80-\u0AFF]',  # Gujarati
            "kn": r'[\u0C80-\u0CFF]',  # Kannada
            "ml": r'[\u0D00-\u0D7F]',  # Malayalam
            "pa": r'[\u0A00-\u0A7F]',  # Punjabi (Gurmukhi)
            "or": r'[\u0B00-\u0B7F]',  # Odia
            "as": r'[\u0980-\u09FF]',  # Assamese (uses Bengali script)
            # Other Languages
            "ar": r'[\u0600-\u06FF]',  # Arabic
            "ur": r'[\u0600-\u06FF]',  # Urdu (uses Arabic script)
            "zh": r'[\u4E00-\u9FFF]',  # Chinese
            "ja": r'[\u3040-\u30FF]',  # Japanese (Hiragana + Katakana)
            "ko": r'[\uAC00-\uD7AF]',  # Korean
            "th": r'[\u0E00-\u0E7F]',  # Thai
            "ru": r'[\u0400-\u04FF]',  # Russian (Cyrillic)
            "es": r'[áéíóúñ¿¡]',  # Spanish
            "fr": r'[àâçéèêëïîôùûü]',  # French
            "de": r'[äöüß]',  # German
        }
        
        # Count characters for each language
        char_counts = {}
        for lang, pattern in language_patterns.items():
            count = len(re.findall(pattern, text, re.IGNORECASE))
            if count > 0:
                char_counts[lang] = count
        
        # Count English characters
        english_chars = len(re.findall(r'[a-zA-Z]', text))
        
        # If any non-English language has more characters, use that language
        if char_counts:
            max_lang = max(char_counts, key=char_counts.get)
            if char_counts[max_lang] > english_chars * 0.3:  # At least 30% of English chars
                return max_lang
        
        return "en"  # Default to English
    
    def _extract_sections(self, text: str) -> List[str]:
        """Extract section numbers from query."""
        matches = SECTION_PATTERN.findall(text)
        
        # Also look for standalone numbers that might be sections
        standalone = re.findall(r'\b(\d{2,3}[a-zA-Z]?)\b', text)
        
        # Common IPC sections
        common_sections = {"302", "307", "376", "420", "498", "304", "306", "323", "354", "506", "379", "380"}
        
        for num in standalone:
            if num in common_sections and num not in matches:
                matches.append(num)
        
        return list(set(matches))
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract important keywords from query."""
        # Remove common words
        stop_words = {"what", "is", "the", "of", "for", "in", "and", "or", "a", "an",
                      "to", "how", "can", "under", "about", "which", "क्या", "है", 
                      "के", "का", "की", "में", "और", "या", "एक", "कैसे"}
        
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords[:10]  # Return top 10 keywords
    
    async def _reformulate_query(self, context: AgentContext) -> str:
        """Reformulate query for better retrieval using chat history if available."""
        # If there is chat history, use the LLM to rewrite the query into a standalone query
        if context.chat_history:
            try:
                from app.services.llm_service import get_llm_service
                llm_service = await get_llm_service()
                
                # Format history for the LLM
                history_text = ""
                for msg in context.chat_history[-5:]: # Last 5 messages are enough context
                    role_name = "User" if msg.get("role") == "user" else "Assistant"
                    history_text += f"{role_name}: {msg.get('content')}\n"
                
                sys_prompt = """You are a legal search assistant. Your task is to reformulate the user's latest query to be a standalone, self-contained legal search query, incorporating any necessary context (such as sections, laws, crimes, parties, or facts) from the previous chat history.
        
Rules:
1. Identify if the user's query refers to previous context (e.g., using pronouns or phrases like 'these laws', 'this section', 'them', 'that case', 'what about the punishment?', 'explain further').
2. If it does, rewrite the query to be completely self-contained and descriptive, so it can be used for search/retrieval.
3. Make sure to explicitly name any specific legal sections (e.g. 'IPC Section 325', 'BNS Section 117(2)'), crimes, or topics mentioned in the history that the user is asking about.
4. If the query is already standalone or there is no history, do not change it or only clean it up.
5. Return ONLY the reformulated query text. Do not add any introduction, headers, quotes, or explanation."""
                
                user_prompt = f"CHAT HISTORY:\n{history_text}\nUSER'S LATEST QUERY: {context.query}"
                messages = [
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt}
                ]
                
                reformulated = await llm_service.generate_chat(messages, max_tokens=150, temperature=0.0)
                reformulated = reformulated.strip()
                # Clean up any potential markdown quotes from LLM
                reformulated = re.sub(r'^["\'`]+|["\'`]+$', '', reformulated).strip()
                
                if reformulated and len(reformulated) > 3:
                    logger.info(f"LLM reformulated query from '{context.query}' to '{reformulated}'")
                    return reformulated
            except Exception as e:
                logger.error(f"Error in LLM query reformulation: {e}")
        
        # Fallback to simple reformulation if LLM fails or no history
        parts = []
        
        # Add domain context
        if context.detected_domain:
            parts.append(f"[{context.detected_domain}]")
        
        # Add original query
        parts.append(context.query)
        
        # Add section context if found
        sections = [e["value"] for e in context.entities if e["type"] == "section"]
        if sections:
            parts.append(f"(Sections: {', '.join(sections)})")
        
        return " ".join(parts)
