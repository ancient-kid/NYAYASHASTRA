"""
NyayaShastra - Statute Service
Handles statute data access and IPC-BNS mappings.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
import logging

from app.models import Statute, IPCBNSMapping
from app.database import get_db_context

logger = logging.getLogger(__name__)


class StatuteService:
    """Service for statute data access."""
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
    
    async def get_section(self, section_number: str, act_code: str) -> Optional[Dict[str, Any]]:
        """Get a specific section by number and act code."""
        try:
            with get_db_context() as db:
                statute = db.query(Statute).filter(
                    Statute.section_number == section_number,
                    Statute.act_code == act_code
                ).first()
                
                if statute:
                    return self._statute_to_dict(statute)
        except Exception as e:
            logger.error(f"Error getting section: {e}")
        
        return None
    
    async def search_statutes(self, query: str, act_codes: Optional[List[str]] = None,
                             domain: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search statutes by text query."""
        try:
            with get_db_context() as db:
                q = db.query(Statute)
                
                if act_codes:
                    q = q.filter(Statute.act_code.in_(act_codes))
                
                if domain:
                    q = q.filter(Statute.domain == domain)
                
                # Text search on title and content
                q = q.filter(
                    (Statute.title_en.ilike(f"%{query}%")) |
                    (Statute.content_en.ilike(f"%{query}%"))
                )
                
                statutes = q.limit(limit).all()
                return [self._statute_to_dict(s) for s in statutes]
        except Exception as e:
            logger.error(f"Error searching statutes: {e}")
        
        return []
    
    async def get_ipc_bns_mapping(self, ipc_section: str) -> Optional[Dict[str, Any]]:
        """Get IPC to BNS mapping for a section."""
        try:
            with get_db_context() as db:
                # Find IPC statute
                ipc_statute = db.query(Statute).filter(
                    Statute.section_number == ipc_section,
                    Statute.act_code == "IPC"
                ).first()
                
                if not ipc_statute:
                    return None
                
                # Find mapping
                mapping = db.query(IPCBNSMapping).filter(
                    IPCBNSMapping.ipc_section_id == ipc_statute.id
                ).first()
                
                if mapping:
                    return self._mapping_to_dict(mapping)
        except Exception as e:
            logger.error(f"Error getting mapping: {e}")
        
        return None
    
    async def get_all_mappings(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all IPC-BNS mappings."""
        try:
            with get_db_context() as db:
                mappings = db.query(IPCBNSMapping).limit(limit).all()
                return [self._mapping_to_dict(m) for m in mappings]
        except Exception as e:
            logger.error(f"Error getting all mappings: {e}")
        
        return []
    
    async def create_statute(self, statute_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a new statute."""
        try:
            with get_db_context() as db:
                statute = Statute(**statute_data)
                db.add(statute)
                db.commit()
                db.refresh(statute)
                return self._statute_to_dict(statute)
        except Exception as e:
            logger.error(f"Error creating statute: {e}")
        
        return None
    
    async def bulk_create_statutes(self, statutes_data: List[Dict[str, Any]]) -> int:
        """Bulk create statutes."""
        try:
            with get_db_context() as db:
                statutes = [Statute(**data) for data in statutes_data]
                db.bulk_save_objects(statutes)
                db.commit()
                return len(statutes)
        except Exception as e:
            logger.error(f"Error bulk creating statutes: {e}")
        
        return 0
    
    def _statute_to_dict(self, statute: Statute) -> Dict[str, Any]:
        """Convert statute model to dictionary."""
        return {
            "id": statute.id,
            "section_number": statute.section_number,
            "act_code": statute.act_code,
            "act_name": statute.act_name,
            "title_en": statute.title_en,
            "title_hi": statute.title_hi,
            "content_en": statute.content_en,
            "content_hi": statute.content_hi,
            "chapter": statute.chapter,
            "year_enacted": statute.year_enacted,
            "domain": statute.domain,
            "punishment_description": statute.punishment_description,
            "min_punishment": statute.min_punishment,
            "max_punishment": statute.max_punishment,
            "is_bailable": statute.is_bailable,
            "is_cognizable": statute.is_cognizable
        }
    
    def _mapping_to_dict(self, mapping: IPCBNSMapping) -> Dict[str, Any]:
        """Convert mapping model to dictionary."""
        return {
            "id": mapping.id,
            "ipc_section": mapping.ipc_section.section_number if mapping.ipc_section else "",
            "ipc_title": mapping.ipc_section.title_en if mapping.ipc_section else "",
            "ipc_content": mapping.ipc_section.content_en if mapping.ipc_section else "",
            "bns_section": mapping.bns_section.section_number if mapping.bns_section else "",
            "bns_title": mapping.bns_section.title_en if mapping.bns_section else "",
            "bns_content": mapping.bns_section.content_en if mapping.bns_section else "",
            "mapping_type": mapping.mapping_type,
            "changes": mapping.changes or [],
            "punishment_changed": mapping.punishment_changed,
            "old_punishment": mapping.old_punishment,
            "new_punishment": mapping.new_punishment,
            "punishment_increased": mapping.punishment_increased,
            "notes": mapping.notes_en
        }


# Singleton
_statute_service: Optional[StatuteService] = None


def get_statute_service() -> StatuteService:
    """Get or create statute service singleton."""
    global _statute_service
    if _statute_service is None:
        _statute_service = StatuteService()
    return _statute_service
