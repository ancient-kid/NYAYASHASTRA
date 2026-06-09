"""
NyayaShastra - Database Seed Script
Seeds the database with initial legal data.
"""

import asyncio
import logging
from datetime import datetime

from app.database import init_db, get_db_context
from app.models import Statute, IPCBNSMapping, CaseLaw, Court
from app.legal_data.legal_seeds import (
    IPC_SECTIONS, 
    BNS_SECTIONS, 
    IPC_BNS_MAPPINGS, 
    LANDMARK_CASES
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def seed_statutes():
    """Seed statute data."""
    logger.info("Seeding statutes...")
    
    with get_db_context() as db:
        # Check if already seeded
        existing = db.query(Statute).count()
        if existing > 0:
            logger.info(f"Statutes already seeded ({existing} records)")
            return
        
        # Seed IPC sections
        for section_data in IPC_SECTIONS:
            statute = Statute(
                section_number=section_data["section_number"],
                act_code=section_data["act_code"],
                act_name=section_data["act_name"],
                title_en=section_data["title_en"],
                title_hi=section_data.get("title_hi"),
                content_en=section_data["content_en"],
                content_hi=section_data.get("content_hi"),
                chapter=section_data.get("chapter"),
                year_enacted=section_data.get("year_enacted", 1860),
                domain=section_data.get("domain", "criminal"),
                punishment_description=section_data.get("punishment_description"),
                is_cognizable=section_data.get("is_cognizable"),
                is_bailable=section_data.get("is_bailable")
            )
            db.add(statute)
        
        # Seed BNS sections
        for section_data in BNS_SECTIONS:
            statute = Statute(
                section_number=section_data["section_number"],
                act_code=section_data["act_code"],
                act_name=section_data["act_name"],
                title_en=section_data["title_en"],
                title_hi=section_data.get("title_hi"),
                content_en=section_data["content_en"],
                content_hi=section_data.get("content_hi"),
                year_enacted=section_data.get("year_enacted", 2023),
                domain=section_data.get("domain", "criminal"),
                punishment_description=section_data.get("punishment_description"),
                is_cognizable=section_data.get("is_cognizable"),
                is_bailable=section_data.get("is_bailable")
            )
            db.add(statute)
        
        db.commit()
        logger.info(f"Seeded {len(IPC_SECTIONS) + len(BNS_SECTIONS)} statutes")


def seed_mappings():
    """Seed IPC-BNS mappings."""
    logger.info("Seeding IPC-BNS mappings...")
    
    with get_db_context() as db:
        existing = db.query(IPCBNSMapping).count()
        if existing > 0:
            logger.info(f"Mappings already seeded ({existing} records)")
            return
        
        for mapping_data in IPC_BNS_MAPPINGS:
            # Find IPC and BNS sections
            ipc_section = db.query(Statute).filter(
                Statute.section_number == mapping_data["ipc_section"],
                Statute.act_code == "IPC"
            ).first()
            
            bns_section = db.query(Statute).filter(
                Statute.section_number == mapping_data["bns_section"],
                Statute.act_code == "BNS"
            ).first()
            
            if ipc_section and bns_section:
                mapping = IPCBNSMapping(
                    ipc_section_id=ipc_section.id,
                    bns_section_id=bns_section.id,
                    mapping_type=mapping_data.get("mapping_type", "exact"),
                    changes=mapping_data.get("changes"),
                    punishment_changed=mapping_data.get("punishment_changed", False),
                    old_punishment=mapping_data.get("old_punishment"),
                    new_punishment=mapping_data.get("new_punishment"),
                    punishment_increased=mapping_data.get("punishment_increased")
                )
                db.add(mapping)
        
        db.commit()
        logger.info(f"Seeded {len(IPC_BNS_MAPPINGS)} mappings")


def seed_cases():
    """Seed landmark case data."""
    logger.info("Seeding case laws...")
    
    with get_db_context() as db:
        existing = db.query(CaseLaw).count()
        if existing > 0:
            logger.info(f"Cases already seeded ({existing} records)")
            return
        
        for case_data in LANDMARK_CASES:
            # Parse judgment date
            judgment_date = None
            if case_data.get("judgment_date"):
                try:
                    judgment_date = datetime.strptime(
                        case_data["judgment_date"], "%Y-%m-%d"
                    )
                except:
                    pass
            
            # Map court string to enum
            court_map = {
                "supreme_court": Court.SUPREME_COURT,
                "delhi_high_court": Court.HIGH_COURT,
                "bombay_high_court": Court.HIGH_COURT
            }
            court = court_map.get(case_data.get("court"), Court.SUPREME_COURT)
            
            case = CaseLaw(
                case_number=case_data["case_number"],
                case_name=case_data["case_name"],
                case_name_hi=case_data.get("case_name_hi"),
                court=court,
                court_name=case_data.get("court_name"),
                judgment_date=judgment_date,
                reporting_year=case_data.get("reporting_year"),
                summary_en=case_data.get("summary_en"),
                summary_hi=case_data.get("summary_hi"),
                is_landmark=case_data.get("is_landmark", False),
                citation_string=case_data.get("citation_string"),
                source_url=case_data.get("source_url"),
                key_holdings=case_data.get("key_holdings"),
                domain=case_data.get("domain", "criminal"),
                cited_sections=case_data.get("cited_sections")
            )
            db.add(case)
        
        db.commit()
        logger.info(f"Seeded {len(LANDMARK_CASES)} cases")


def seed_all():
    """Seed all data."""
    logger.info("Starting database seeding...")
    
    # Initialize database tables
    init_db()
    
    # Seed data
    seed_statutes()
    seed_mappings()
    seed_cases()
    
    logger.info("Database seeding complete!")


if __name__ == "__main__":
    seed_all()
