"""
NyayaShastra - Statutes API Routes
Handles statute search and IPC-BNS comparisons using PostgreSQL database.
NO MOCK DATA - Uses real database.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import Statute, IPCBNSMapping
from app.schemas import (
    StatuteResponse,
    StatuteSearchRequest,
    StatuteSearchResponse,
    IPCBNSComparisonRequest,
    IPCBNSComparisonResponse,
    IPCBNSComparisonItem,
    LegalDomain
)
from sqlalchemy.orm import joinedload, aliased

router = APIRouter(prefix="/api/statutes", tags=["statutes"])


def statute_to_dict(statute: Statute) -> dict:
    """Convert SQLAlchemy Statute to dictionary."""
    return {
        "id": statute.id,
        "section_number": statute.section_number,
        "act_code": statute.act_code,
        "act_name": statute.act_name,
        "title_en": statute.title_en,
        "title_hi": statute.title_hi,
        "content_en": statute.content_en,
        "content_hi": statute.content_hi,
        "domain": statute.domain,
        "chapter": statute.chapter,
        "year_enacted": statute.year_enacted,
        "punishment_description": statute.punishment_description,
        "is_bailable": statute.is_bailable,
        "is_cognizable": statute.is_cognizable
    }


def mapping_to_dict(mapping: IPCBNSMapping) -> dict:
    """Convert SQLAlchemy IPCBNSMapping to dictionary."""
    ipc = mapping.ipc_section
    bns = mapping.bns_section
    
    return {
        "id": str(mapping.id),
        "ipc_section": ipc.section_number if ipc else "",
        "ipc_title": ipc.title_en if ipc else "",
        "ipc_content": ipc.content_en if ipc else "",
        "bns_section": bns.section_number if bns else "",
        "bns_title": bns.title_en if bns else "",
        "bns_content": bns.content_en if bns else "",
        "changes": mapping.changes or [],
        "punishment_change": {
            "old": mapping.old_punishment or "",
            "new": mapping.new_punishment or "",
            "increased": mapping.punishment_increased or False
        } if mapping.punishment_changed else None,
        "mapping_type": mapping.mapping_type or "exact"
    }


@router.get("/", response_model=List[dict])
def get_statutes(
    act_code: Optional[str] = Query(None, description="Filter by act code (IPC, BNS)"),
    domain: Optional[str] = Query(None, description="Filter by domain (criminal, civil)"),
    limit: int = Query(20, le=100, description="Maximum results"),
    db: Session = Depends(get_db)
):
    """Get all statutes with optional filtering from database."""
    query = db.query(Statute)
    
    if act_code:
        query = query.filter(Statute.act_code.ilike(act_code))
    
    if domain:
        query = query.filter(Statute.domain == domain)
    
    statutes = query.limit(limit).all()
    
    if not statutes:
        return []
    
    return [statute_to_dict(s) for s in statutes]


@router.get("/search")
def search_statutes(
    query: str = Query(..., description="Search query"),
    act_codes: Optional[str] = Query(None, description="Comma-separated act codes"),
    domain: Optional[str] = Query(None, description="Legal domain"),
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db)
):
    """Search statutes by text query in database."""
    search_query = db.query(Statute)
    
    # Text search in title and content
    search_pattern = f"%{query}%"
    search_query = search_query.filter(
        (Statute.title_en.ilike(search_pattern)) |
        (Statute.content_en.ilike(search_pattern)) |
        (Statute.section_number.ilike(search_pattern)) |
        (Statute.title_hi.ilike(search_pattern)) |
        (Statute.content_hi.ilike(search_pattern))
    )
    
    # Filter by act codes if provided
    if act_codes:
        codes = [c.strip().upper() for c in act_codes.split(",")]
        search_query = search_query.filter(Statute.act_code.in_(codes))
    
    # Filter by domain
    if domain:
        search_query = search_query.filter(Statute.domain == domain)
    
    # Get total count
    total = search_query.count()
    
    # Get results
    statutes = search_query.limit(limit).all()
    
    return {
        "results": [statute_to_dict(s) for s in statutes],
        "total": total,
        "query": query
    }


@router.get("/section/{section_number}")
def get_section(
    section_number: str,
    act_code: str = Query("IPC", description="Act code"),
    db: Session = Depends(get_db)
):
    """Get a specific section by number from database."""
    statute = db.query(Statute).filter(
        Statute.section_number.ilike(section_number),
        Statute.act_code.ilike(act_code)
    ).first()
    
    if not statute:
        raise HTTPException(
            status_code=404, 
            detail=f"Section {section_number} not found in {act_code}"
        )
    
    return statute_to_dict(statute)


# In-memory cache for full comparison list
_comparison_cache = None

@router.get("/comparison")
def get_ipc_bns_comparison(
    ipc_section: Optional[str] = Query(None, description="IPC section number"),
    bns_section: Optional[str] = Query(None, description="BNS section number"),
    search_query: Optional[str] = Query(None, description="Search in comparisons"),
    db: Session = Depends(get_db)
):
    """Get IPC to BNS section comparisons from database."""
    global _comparison_cache
    
    # Return cached result for full list request
    if not ipc_section and not bns_section and not search_query and _comparison_cache:
        return _comparison_cache

    try:
        query = db.query(IPCBNSMapping).options(
            joinedload(IPCBNSMapping.ipc_section),
            joinedload(IPCBNSMapping.bns_section)
        )
        
        # Use aliases if we need to join the same table twice
        if ipc_section:
            statute_ipc = aliased(Statute)
            query = query.join(
                statute_ipc, IPCBNSMapping.ipc_section_id == statute_ipc.id
            ).filter(statute_ipc.section_number.ilike(f"%{ipc_section}%"))
        
        if bns_section:
            statute_bns = aliased(Statute)
            query = query.join(
                statute_bns, IPCBNSMapping.bns_section_id == statute_bns.id
            ).filter(statute_bns.section_number.ilike(f"%{bns_section}%"))
        
        mappings = query.all()
        
        # Filter by search query if provided
        if search_query:
            query_lower = search_query.lower()
            filtered_mappings = []
            for m in mappings:
                ipc = m.ipc_section
                bns = m.bns_section
                if not ipc or not bns:
                    continue
                    
                if (query_lower in (ipc.title_en or "").lower() or
                    query_lower in (bns.title_en or "").lower() or
                    query_lower in (ipc.section_number or "").lower() or
                    query_lower in (bns.section_number or "").lower()):
                    filtered_mappings.append(m)
            mappings = filtered_mappings
        
        result = {
            "comparisons": [mapping_to_dict(m) for m in mappings if m.ipc_section and m.bns_section],
            "total": len(mappings)
        }
        
        # Update cache if this was a full list request
        if not ipc_section and not bns_section and not search_query:
            _comparison_cache = result
            
        return result
    except Exception as e:
        # Return empty data instead of error
        import logging
        logging.error(f"Error fetching comparisons: {e}")
        return {
            "comparisons": [],
            "total": 0
        }


@router.get("/comparison/{ipc_section}")
def get_specific_comparison(
    ipc_section: str,
    db: Session = Depends(get_db)
):
    """Get comparison for a specific IPC section from database."""
    # Find the IPC statute
    ipc_statute = db.query(Statute).filter(
        Statute.section_number.ilike(ipc_section),
        Statute.act_code == "IPC"
    ).first()
    
    if not ipc_statute:
        raise HTTPException(
            status_code=404, 
            detail=f"IPC Section {ipc_section} not found"
        )
    
    # Find the mapping
    mapping = db.query(IPCBNSMapping).filter(
        IPCBNSMapping.ipc_section_id == ipc_statute.id
    ).first()
    
    if not mapping:
        raise HTTPException(
            status_code=404, 
            detail=f"No BNS mapping found for IPC Section {ipc_section}"
        )
    
    return mapping_to_dict(mapping)
