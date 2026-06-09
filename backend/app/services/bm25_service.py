import logging
import re
from typing import List, Dict, Any, Optional, Tuple
from rank_bm25 import BM25Okapi
import numpy as np
from app.schemas import LegalDomain

logger = logging.getLogger(__name__)

# Common stop words to ignore during classification
STOP_WORDS = {
    "what", "is", "the", "a", "an", "and", "or", "for", "with", "about", "to", "at", "by", "from", "on", "in", 
    "of", "at", "as", "how", "can", "their", "them", "they", "who", "which", "where", "when", "why",
    "क्या", "है", "का", "की", "के", "में", "और", "या", "एक", "से", "पर", "को", "भी", "ही", "था", "थी", "थे"
}

# Detailed domain descriptions for BM25 indexing
DOMAIN_CORPUS = {
    LegalDomain.TRAFFIC.value: """
        Traffic laws, motor vehicle rules, driving violations, accidents on road, challan, 
        driving license, vehicle registration RC, traffic signals, red light jumping, 
        overspeeding, helmet rules, seatbelt requirements, drunk driving penalties, 
        overloading of vehicles, RTO office rules, hit and run cases, parking violations, 
        no entry zones, zebra crossing, vehicle insurance, pollution certificate PUC, 
        one way driving, transport department, motor vehicle act MVA, road safety regulations,
        pedestrian safety, hitting a pedestrian, walking on road, death by accident, 
        rash driving, negligent driving, vehicle collision, motor accident claims tribunal MACT,
        third party insurance, driving without license, minor driving, speeding fine.
    """,
    LegalDomain.CRIMINAL.value: """
        Criminal law, Indian Penal Code IPC, Bharatiya Nyaya Sanhita BNS, murder, theft, 
        burglary, robbery, kidnapping, assault, battery, rape, sexual offenses, molestation, 
        police FIR, arrest procedures, bail applications, jail, prison, punishment, 
        death penalty, homicide, fraud, cheating, extortion, bribery, corruption, 
        terrorism UAPA, drugs NDPS, arms act, conspiracy, abetment, criminal procedure code CrPC, 
        BNSS, BNSS procedure, confession, trial, prosecution, magistrate, cognizable offense, 
        non bailable warrant, section 302, section 307, attempt to murder, culpable homicide,
        causing death by negligence, criminal force, criminal trespass, forgery, defamation criminal.
    """,
    LegalDomain.CIVIL_FAMILY.value: """
        Civil law, family law, marriage, divorce, alimony, child custody, maintenance, 
        hindu marriage act, special marriage act, christian marriage, muslim personal law, 
        domestic violence, dowry prohibition act, will, inheritance, probate, succession, 
        adoption, guardianship, partition of family property, restitution of conjugal rights, 
        annulment, contract disputes, consumer protection, torts, negligence, defamation, 
        civil procedure code CPC, summary suit, injunction, specific performance, breach of contract,
        small causes court, civil appeal, legal notice.
    """,
    LegalDomain.CORPORATE.value: """
        Corporate law, companies act, SEBI regulations, business contracts, agreements, 
        mergers and acquisitions, M&A, taxation, income tax, GST, shareholder rights, 
        directors duties, boardroom disputes, insolvency and bankruptcy code IBC, 
        ROC filings, MCA website, auditing, corporate governance, partnership, LLP, 
        limited liability partnership, tender, bidding, arbitration and conciliation, 
        commercial courts, trade marks, MSME, intellectual property IPR, copyright, patent,
        corporate social responsibility CSR, company formation, board of directors.
    """,
    LegalDomain.IT_CYBER.value: """
        Information Technology act, IT Act, cyber law, hacking, phishing, data privacy, 
        identity theft, computer fraud, online harassment, social media defamation, 
        cyberbullying, deepfake, cryptocurrency, bitcoin, crypto regulation, 
        digital evidence, electronic records, password theft, server breach, 
        malware, virus, spamming, cyber stalking, DPDP act, digital personal data protection,
        social media intermediary rules, ecommerce regulations, dark web, encryption.
    """,
    LegalDomain.PROPERTY.value: """
        Property law, land ownership, real estate, RERA, registration act, transfer of property act TPA, 
        lease, rent, tenant, landlord, eviction process, sale deed, stamp duty, mutation, 
        khata, registry, encroachment, housing board, building plan sanction, 
        adverse possession, partition deed, gift deed, power of attorney POA, 
        mortgage, hypothecation, easement rights, free hold, lease hold properties.
    """,
    LegalDomain.CONSTITUTIONAL.value: """
        Constitutional law of India, fundamental rights, directive principles, 
        article 32, article 226, writ petitions, habeas corpus, mandamus, certiorari, 
        PIL, public interest litigation, supreme court of India, high court, 
        freedom of speech, right to privacy, reservation policy, election law, 
        federalism, center state relations, governor powers, president of India, 
        parliamentary procedure, speaker, emergency powers, constitutional amendments,
        judicial review, secularism, preamble.
    """,
    LegalDomain.ENVIRONMENT.value: """
        Environment protection act, pollution control, NGT, national green tribunal, 
        forest conservation, wildlife protection, air pollution, water pollution act, 
        environmental clearance, EIA, climate change, carbon emission, plastic waste, 
        hazardous waste management, coastal regulation zone CRZ, sanitation, noise pollution,
        sustainable development, bio diversity act, global warming, forest rights.
    """
}

class BM25DomainClassifier:
    """Uses BM25 and Semantic Re-ranking for high-precision domain detection."""
    
    def __init__(self, vector_store=None):
        self.domains = list(DOMAIN_CORPUS.keys())
        self.corpus_texts = [DOMAIN_CORPUS[d] for d in self.domains]
        self.tokenized_corpus = [self._tokenize(text) for text in self.corpus_texts]
        self.bm25 = BM25Okapi(self.tokenized_corpus)
        self.vector_store = vector_store
        self._domain_embeddings = {}
        
    def _tokenize(self, text: str) -> List[str]:
        """Stop-word filtering tokenizer for BM25."""
        # Remove special chars and lower case
        clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
        tokens = clean_text.split()
        return [t for t in tokens if t not in STOP_WORDS]
    
    async def _get_domain_embeddings(self):
        """Prepare domain embeddings for re-ranking."""
        if not self.vector_store:
            return
            
        if not self._domain_embeddings:
            for domain, text in DOMAIN_CORPUS.items():
                self._domain_embeddings[domain] = self.vector_store.embed_text(text)
                
    async def classify(self, query: str) -> Tuple[str, float, Dict[str, float]]:
        """
        Classify query domain using BM25 and Re-ranking.
        Returns: (predicted_domain, confidence_score, all_scores)
        """
        tokenized_query = self._tokenize(query)
        
        # 1. BM25 Scores
        bm25_scores = self.bm25.get_scores(tokenized_query)
        
        # Normalize BM25 scores to 0-1
        if max(bm25_scores) > 0:
            bm25_scores = bm25_scores / max(bm25_scores)
        
        # 2. Semantic Re-ranking (If vector store available)
        semantic_scores = np.zeros(len(self.domains))
        if self.vector_store:
            await self._get_domain_embeddings()
            query_embedding = self.vector_store.embed_text(query)
            
            for i, domain in enumerate(self.domains):
                domain_emb = self._domain_embeddings.get(domain)
                if domain_emb:
                    # Cosine similarity
                    sim = np.dot(query_embedding, domain_emb) / (np.linalg.norm(query_embedding) * np.linalg.norm(domain_emb))
                    semantic_scores[i] = sim

        # 3. Hybrid Score (Weighted avg of BM25 and Semantic)
        # BM25 is good for keywords, Semantic is good for intent.
        hybrid_scores = {}
        for i, domain in enumerate(self.domains):
            # If query is very short, rely more on BM25
            if len(tokenized_query) <= 3:
                score = (0.7 * bm25_scores[i]) + (0.3 * semantic_scores[i])
            else:
                score = (0.5 * bm25_scores[i]) + (0.5 * semantic_scores[i])
            hybrid_scores[domain] = float(score)
            
        # 4. Final Decision
        best_domain = max(hybrid_scores, key=hybrid_scores.get)
        confidence = hybrid_scores[best_domain]
        
        logger.info(f"Hybrid classification for query '{query}': {best_domain} (conf: {confidence:.2f})")
        return best_domain, confidence, hybrid_scores

# Singleton
_classifier: Optional[BM25DomainClassifier] = None

async def get_domain_classifier() -> BM25DomainClassifier:
    """Get or create singleton."""
    global _classifier
    if _classifier is None:
        from app.services.vector_store import get_vector_store
        vs = await get_vector_store()
        _classifier = BM25DomainClassifier(vector_store=vs)
    return _classifier
