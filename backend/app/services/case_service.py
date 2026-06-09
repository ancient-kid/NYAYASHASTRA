"""
NyayaShastra - Case Law Service
Handles case law data access and search.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import logging

from app.models import CaseLaw
from app.database import get_db_context

logger = logging.getLogger(__name__)


class CaseService:
    """Service for case law data access."""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
    
    async def get_case(self, case_id: int) -> Optional[Dict[str, Any]]:
        """Get a case by ID."""
        try:
            with get_db_context() as db:
                case = db.query(CaseLaw).filter(CaseLaw.id == case_id).first()
                if case:
                    return self._case_to_dict(case)
        except Exception as e:
            logger.error(f"Error getting case: {e}")
        return None
    
    async def get_cases_by_section(self, section_number: str, 
                                   limit: int = 5) -> List[Dict[str, Any]]:
        """Get cases that cite a specific section."""
        try:
            with get_db_context() as db:
                from app.models import CaseStatuteLink, Statute
                cases = db.query(CaseLaw).join(
                    CaseStatuteLink, CaseLaw.id == CaseStatuteLink.case_id
                ).join(
                    Statute, CaseStatuteLink.statute_id == Statute.id
                ).filter(
                    Statute.section_number == section_number
                ).limit(limit).all()
                return [self._case_to_dict(c) for c in cases]
        except Exception as e:
            logger.error(f"Error getting cases by section: {e}")
        return []
    
    async def search_cases(self, query: str, court: Optional[str] = None,
                          domain: Optional[str] = None,
                          limit: int = 10) -> List[Dict[str, Any]]:
        """Search cases by text query."""
        try:
            with get_db_context() as db:
                q = db.query(CaseLaw)
                
                if court:
                    q = q.filter(CaseLaw.court == court)
                
                if domain:
                    domain_val = domain.value if hasattr(domain, "value") else domain
                    if isinstance(domain_val, str):
                        domain_val = self._normalize_domain(domain_val)
                    q = q.filter(CaseLaw.domain == domain_val)
                
                # Text search
                q = q.filter(
                    (CaseLaw.case_name.ilike(f"%{query}%")) |
                    (CaseLaw.summary_en.ilike(f"%{query}%"))
                )
                
                cases = q.limit(limit).all()
                return [self._case_to_dict(c) for c in cases]
        except Exception as e:
            logger.error(f"Error searching cases: {e}")
        return []
    
    async def get_landmark_cases(self, domain: Optional[str] = None,
                                 limit: int = 10) -> List[Dict[str, Any]]:
        """Get landmark cases."""
        try:
            with get_db_context() as db:
                q = db.query(CaseLaw).filter(CaseLaw.is_landmark == True)
                
                if domain:
                    domain_val = domain.value if hasattr(domain, "value") else domain
                    if isinstance(domain_val, str):
                        domain_val = self._normalize_domain(domain_val)
                    q = q.filter(CaseLaw.domain == domain_val)
                
                cases = q.order_by(CaseLaw.reporting_year.desc()).limit(limit).all()
                return [self._case_to_dict(c) for c in cases]
        except Exception as e:
            logger.error(f"Error getting landmark cases: {e}")
        return []
    
    async def create_case(self, case_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new case."""
        try:
            with get_db_context() as db:
                case = CaseLaw(**case_data)
                db.add(case)
                db.commit()
                db.refresh(case)
                return self._case_to_dict(case)
        except Exception as e:
            logger.error(f"Error creating case: {e}")
        return None

    def _normalize_domain(self, domain: str) -> str:
        norm = domain.lower().strip()
        if norm in ("civil", "family", "civil_family"):
            return "civil_family"
        if norm in ("it_cyber", "cyber", "it"):
            return "it_cyber"
        if norm in ("environmental", "environment"):
            return "environment"
        if norm in ("constitutional", "consitutional"):
            return "constitutional"
        if norm in ("criminal", "corporate", "property", "traffic"):
            return norm
        return norm
    
    def _case_to_dict(self, case: CaseLaw) -> Dict[str, Any]:
        """Convert case model to dictionary."""
        court_val = case.court.value if hasattr(case.court, "value") else case.court
        return {
            "id": case.id,
            "case_number": case.case_number,
            "case_name": case.case_name,
            "case_name_hi": case.case_name_hi,
            "court": court_val,
            "court_name": case.court_name,
            "judgment_date": case.judgment_date.isoformat() if case.judgment_date else None,
            "reporting_year": case.reporting_year,
            "summary_en": case.summary_en,
            "summary_hi": case.summary_hi,
            "is_landmark": case.is_landmark,
            "citation_string": case.citation_string,
            "source_url": case.source_url,
            "key_holdings": case.key_holdings,
            "domain": case.domain,
            "cited_sections": [
                {"act": s.act_code, "section": s.section_number}
                for s in case.cited_statutes
            ]
        }


# Singleton
_case_service: Optional[CaseService] = None


def get_case_service() -> CaseService:
    """Get or create case service singleton."""
    global _case_service
    if _case_service is None:
        _case_service = CaseService()
    return _case_service
