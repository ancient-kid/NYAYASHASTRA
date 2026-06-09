"""
NyayaShastra - Database Seeder
Seeds the PostgreSQL database with IPC, BNS sections, and case laws from CSV data.
Run with: python -m app.seed_database
"""

import logging
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import SessionLocal, init_db
from app.models import Statute, IPCBNSMapping, CaseLaw, CaseStatuteLink
from app.legal_data.legal_seeds import (
    get_ipc_sections,
    get_bns_sections,
    get_mappings,
    get_landmark_cases
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def clear_database(db: Session):
    """Clear existing data from tables."""
    logger.info("Clearing existing data...")
    db.query(CaseStatuteLink).delete()
    db.query(IPCBNSMapping).delete()
    db.query(CaseLaw).delete()
    db.query(Statute).delete()
    db.commit()
    logger.info("Database cleared.")


def seed_statutes(db: Session) -> dict:
    """Seed IPC and BNS sections from CSV data."""
    logger.info("Seeding statutes from CSV data...")
    statute_map = {}  # Maps (act_code, section_number) -> id
    
    # Seed IPC sections
    ipc_sections = get_ipc_sections()
    logger.info(f"Loading {len(ipc_sections)} IPC sections...")
    
    for data in ipc_sections:
        try:
            statute = Statute(
                section_number=data["section_number"],
                act_name=data["act_name"],
                act_code=data["act_code"],
                title_en=data.get("title_en", ""),
                title_hi=data.get("title_hi"),
                content_en=data.get("content_en", ""),
                content_hi=data.get("content_hi"),
                chapter=data.get("chapter"),
                year_enacted=data.get("year_enacted", 1860),
                domain=data.get("domain", "criminal"),
                punishment_description=data.get("punishment_description"),
                is_bailable=data.get("is_bailable"),
                is_cognizable=data.get("is_cognizable")
            )
            db.add(statute)
            db.flush()
            statute_map[(data["act_code"], data["section_number"])] = statute.id
        except Exception as e:
            logger.warning(f"Skipping IPC section {data.get('section_number')}: {e}")
            continue
    
    # Seed BNS sections
    bns_sections = get_bns_sections()
    logger.info(f"Loading {len(bns_sections)} BNS sections...")
    
    for data in bns_sections:
        try:
            statute = Statute(
                section_number=data["section_number"],
                act_name=data["act_name"],
                act_code=data["act_code"],
                title_en=data.get("title_en", ""),
                title_hi=data.get("title_hi"),
                content_en=data.get("content_en", ""),
                content_hi=data.get("content_hi"),
                year_enacted=data.get("year_enacted", 2023),
                domain=data.get("domain", "criminal"),
                punishment_description=data.get("punishment_description"),
                is_bailable=data.get("is_bailable"),
                is_cognizable=data.get("is_cognizable")
            )
            db.add(statute)
            db.flush()
            statute_map[(data["act_code"], data["section_number"])] = statute.id
        except Exception as e:
            logger.warning(f"Skipping BNS section {data.get('section_number')}: {e}")
            continue
    
    db.commit()
    logger.info(f"Seeded {len(statute_map)} statutes total.")
    return statute_map


def seed_mappings(db: Session, statute_map: dict):
    """Seed IPC-BNS mappings from CSV data."""
    logger.info("Seeding IPC-BNS mappings from CSV...")
    
    mappings_data = get_mappings()
    count = 0
    skipped = 0
    
    for data in mappings_data:
        ipc_key = ("IPC", data["ipc_section"])
        bns_key = ("BNS", data["bns_section"])
        
        if ipc_key not in statute_map or bns_key not in statute_map:
            skipped += 1
            continue
        
        try:
            mapping = IPCBNSMapping(
                ipc_section_id=statute_map[ipc_key],
                bns_section_id=statute_map[bns_key],
                mapping_type=data.get("mapping_type", "exact"),
                changes=data.get("changes", []),
                punishment_changed=data.get("punishment_changed", False),
                old_punishment=data.get("old_punishment"),
                new_punishment=data.get("new_punishment"),
                punishment_increased=data.get("punishment_increased")
            )
            db.add(mapping)
            count += 1
        except Exception as e:
            logger.warning(f"Skipping mapping {data['ipc_section']} -> {data['bns_section']}: {e}")
            skipped += 1
    
    db.commit()
    logger.info(f"Seeded {count} mappings, skipped {skipped}.")


def seed_case_laws(db: Session, statute_map: dict):
    """Seed landmark case laws."""
    logger.info("Seeding case laws...")
    
    cases_data = get_landmark_cases()
    count = 0
    
    for data in cases_data:
        # Parse judgment date
        judgment_date = None
        if data.get("judgment_date"):
            try:
                judgment_date = datetime.strptime(data["judgment_date"], "%Y-%m-%d")
            except:
                pass
        
        try:
            case = CaseLaw(
                case_number=data["case_number"],
                case_name=data["case_name"],
                case_name_hi=data.get("case_name_hi"),
                court=data.get("court", "supreme_court"),
                court_name=data.get("court_name"),
                judgment_date=judgment_date,
                reporting_year=data.get("reporting_year"),
                summary_en=data.get("summary_en"),
                summary_hi=data.get("summary_hi"),
                is_landmark=data.get("is_landmark", False),
                domain=data.get("domain", "criminal"),
                key_holdings=data.get("key_holdings", []),
                citation_string=data.get("citation_string"),
                source_url=data.get("source_url")
            )
            db.add(case)
            db.flush()
            
            # Link cited sections
            cited_sections = data.get("cited_sections", [])
            for section_num in cited_sections:
                # Try IPC first, then BNS
                ipc_key = ("IPC", section_num)
                bns_key = ("BNS", section_num)
                
                statute_id = statute_map.get(ipc_key) or statute_map.get(bns_key)
                if statute_id:
                    link = CaseStatuteLink(
                        case_id=case.id,
                        statute_id=statute_id,
                        relevance_score=1.0
                    )
                    db.add(link)
            
            count += 1
        except Exception as e:
            logger.warning(f"Skipping case {data.get('case_name')}: {e}")
    
    db.commit()
    logger.info(f"Seeded {count} case laws.")


def seed_database():
    """Main seeding function."""
    logger.info("=" * 60)
    logger.info("NyayaShastra - Database Seeding from CSV Data")
    logger.info("=" * 60)
    
    # Initialize database tables
    logger.info("Initializing database tables...")
    init_db()
    
    # Create session
    db = SessionLocal()
    
    try:
        # Clear existing data
        clear_database(db)
        
        # Seed statutes from CSV
        statute_map = seed_statutes(db)
        
        # Seed mappings from CSV
        seed_mappings(db, statute_map)
        
        # Seed case laws
        seed_case_laws(db, statute_map)
        
        logger.info("=" * 60)
        logger.info("Database seeding completed successfully!")
        logger.info("=" * 60)
        
        # Print summary
        statute_count = db.query(Statute).count()
        ipc_count = db.query(Statute).filter(Statute.act_code == "IPC").count()
        bns_count = db.query(Statute).filter(Statute.act_code == "BNS").count()
        mapping_count = db.query(IPCBNSMapping).count()
        case_count = db.query(CaseLaw).count()
        
        logger.info(f"\n📊 Summary:")
        logger.info(f"  - Total Statutes: {statute_count}")
        logger.info(f"    • IPC Sections: {ipc_count}")
        logger.info(f"    • BNS Sections: {bns_count}")
        logger.info(f"  - IPC-BNS Mappings: {mapping_count}")
        logger.info(f"  - Case Laws: {case_count}")
        
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
