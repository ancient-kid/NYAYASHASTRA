"""
NyayaShastra - Case Laws API Routes
Handles case law search and retrieval from PostgreSQL database.
NO MOCK DATA - Uses real database.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import CaseLaw, CaseStatuteLink, Statute
from app.schemas import CaseLawResponse

router = APIRouter(prefix="/api/cases", tags=["cases"])


def caselaw_to_dict(case: CaseLaw) -> dict:
    """Convert SQLAlchemy CaseLaw to dictionary."""
    # Get cited sections
    cited_sections = []
    for statute in case.cited_statutes:
        cited_sections.append(statute.section_number)
    
    return {
        "id": str(case.id),
        "case_number": case.case_number,
        "case_name": case.case_name,
        "case_name_hi": case.case_name_hi,
        "court": case.court,
        "court_name": case.court_name,
        "judgment_date": case.judgment_date.strftime("%Y-%m-%d") if case.judgment_date else None,
        "reporting_year": case.reporting_year,
        "summary_en": case.summary_en,
        "summary_hi": case.summary_hi,
        "is_landmark": case.is_landmark,
        "citation_string": case.citation_string,
        "source_url": case.source_url,
        "key_holdings": case.key_holdings or [],
        "domain": case.domain,
        "cited_sections": cited_sections
    }


@router.get("/", response_model=List[dict])
def get_cases(
    court: Optional[str] = Query(None, description="Filter by court"),
    domain: Optional[str] = Query(None, description="Filter by domain"),
    landmark_only: bool = Query(False, description="Only landmark cases"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    """Get all case laws with optional filtering from database."""
    query = db.query(CaseLaw)
    
    if court:
        query = query.filter(CaseLaw.court == court)
    
    if domain:
        query = query.filter(CaseLaw.domain == domain)
    
    if landmark_only:
        query = query.filter(CaseLaw.is_landmark == True)
    
    cases = query.limit(limit).all()
    
    return [caselaw_to_dict(c) for c in cases]


@router.get("/search")
def search_cases(
    query: str = Query(..., description="Search query"),
    court: Optional[str] = Query(None),
    domain: Optional[str] = Query(None),
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db)
):
    """Search case laws by text query in database."""
    search_query = db.query(CaseLaw)
    
    # Text search in case name and summary
    search_pattern = f"%{query}%"
    search_query = search_query.filter(
        (CaseLaw.case_name.ilike(search_pattern)) |
        (CaseLaw.summary_en.ilike(search_pattern)) |
        (CaseLaw.case_name_hi.ilike(search_pattern)) |
        (CaseLaw.summary_hi.ilike(search_pattern)) |
        (CaseLaw.citation_string.ilike(search_pattern))
    )
    
    if court:
        search_query = search_query.filter(CaseLaw.court == court)
    
    if domain:
        search_query = search_query.filter(CaseLaw.domain == domain)
    
    total = search_query.count()
    cases = search_query.limit(limit).all()
    
    return {
        "results": [caselaw_to_dict(c) for c in cases],
        "total": total,
        "query": query
    }


@router.get("/landmark")
def get_landmark_cases(
    domain: Optional[str] = Query(None),
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db)
):
    """Get landmark cases from database."""
    query = db.query(CaseLaw).filter(CaseLaw.is_landmark == True)
    
    if domain:
        query = query.filter(CaseLaw.domain == domain)
    
    total = query.count()
    cases = query.limit(limit).all()
    
    return {
        "cases": [caselaw_to_dict(c) for c in cases],
        "total": total
    }


@router.get("/by-section/{section_number}")
def get_cases_by_section(
    section_number: str,
    db: Session = Depends(get_db)
):
    """Get cases that cite a specific section from database."""
    # Find statutes matching the section number
    statutes = db.query(Statute).filter(
        Statute.section_number.ilike(section_number)
    ).all()
    
    if not statutes:
        return {
            "section": section_number,
            "cases": [],
            "total": 0
        }
    
    # Get all cases that cite these statutes
    statute_ids = [s.id for s in statutes]
    cases = db.query(CaseLaw).join(
        CaseStatuteLink, CaseLaw.id == CaseStatuteLink.case_id
    ).filter(
        CaseStatuteLink.statute_id.in_(statute_ids)
    ).all()
    
    return {
        "section": section_number,
        "cases": [caselaw_to_dict(c) for c in cases],
        "total": len(cases)
    }


@router.get("/{case_id}")
def get_case(
    case_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific case by ID from database."""
    try:
        case_id_int = int(case_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid case ID")
    
    case = db.query(CaseLaw).filter(CaseLaw.id == case_id_int).first()
    
    if not case:
        raise HTTPException(status_code=404, detail=f"Case {case_id} not found")
    
    return caselaw_to_dict(case)
