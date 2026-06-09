"""
Seed IPC-BNS Mappings into the database.
Maps IPC sections to their corresponding BNS sections.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Statute, IPCBNSMapping
from app.config import settings

# IPC to BNS mapping data
IPC_BNS_MAPPINGS = [
    # Murder and related
    {"ipc": "300", "bns": "101", "type": "modified", "changes": [{"type": "modified", "description": "Definition nearly identical with minor language updates"}]},
    {"ipc": "302", "bns": "103", "type": "exact", "changes": [], "punishment_changed": False},
    {"ipc": "304", "bns": "105", "type": "modified", "changes": [{"type": "modified", "description": "Punishment structure maintained"}]},
    {"ipc": "304A", "bns": "106", "type": "modified", "changes": [{"type": "modified", "description": "Causing death by negligence - language updated"}]},
    {"ipc": "304B", "bns": "80", "type": "modified", "changes": [{"type": "modified", "description": "Dowry death provisions strengthened"}], "punishment_changed": True, "old_punishment": "7 years to life", "new_punishment": "7 years to life or death", "punishment_increased": True},
    
    # Hurt and Grievous Hurt
    {"ipc": "319", "bns": "114", "type": "exact", "changes": []},
    {"ipc": "320", "bns": "115", "type": "exact", "changes": []},
    {"ipc": "321", "bns": "116", "type": "exact", "changes": []},
    {"ipc": "322", "bns": "117", "type": "exact", "changes": []},
    {"ipc": "323", "bns": "118", "type": "exact", "changes": []},
    {"ipc": "324", "bns": "119", "type": "modified", "changes": [{"type": "modified", "description": "Voluntarily causing hurt by dangerous weapons"}]},
    {"ipc": "325", "bns": "120", "type": "exact", "changes": []},
    {"ipc": "326", "bns": "121", "type": "modified", "changes": [{"type": "modified", "description": "Grievous hurt by dangerous weapons"}]},
    
    # Sexual Offences
    {"ipc": "375", "bns": "63", "type": "modified", "changes": [{"type": "modified", "description": "Definition of rape updated with modern language"}, {"type": "added", "description": "Explicit consent provisions strengthened"}]},
    {"ipc": "376", "bns": "64", "type": "modified", "changes": [{"type": "modified", "description": "Minimum punishment increased from 7 to 10 years"}], "punishment_changed": True, "old_punishment": "Min 7 years RI to life + fine", "new_punishment": "Min 10 years RI to life + fine", "punishment_increased": True},
    {"ipc": "376A", "bns": "66", "type": "modified", "changes": [{"type": "modified", "description": "Rape causing death or persistent vegetative state"}]},
    {"ipc": "376B", "bns": "67", "type": "modified", "changes": [{"type": "modified", "description": "Sexual intercourse by husband during separation"}]},
    {"ipc": "376D", "bns": "70", "type": "modified", "changes": [{"type": "modified", "description": "Gang rape punishment enhanced"}], "punishment_changed": True, "old_punishment": "Min 20 years RI to life", "new_punishment": "Min 20 years RI to life or death", "punishment_increased": True},
    
    # Kidnapping and Abduction
    {"ipc": "359", "bns": "137", "type": "exact", "changes": []},
    {"ipc": "360", "bns": "138", "type": "exact", "changes": []},
    {"ipc": "361", "bns": "139", "type": "exact", "changes": []},
    {"ipc": "362", "bns": "140", "type": "exact", "changes": []},
    {"ipc": "363", "bns": "141", "type": "exact", "changes": []},
    {"ipc": "363A", "bns": "142", "type": "modified", "changes": [{"type": "modified", "description": "Kidnapping for begging - provisions enhanced"}]},
    {"ipc": "364", "bns": "143", "type": "exact", "changes": []},
    {"ipc": "364A", "bns": "144", "type": "modified", "changes": [{"type": "modified", "description": "Kidnapping for ransom - updated provisions"}]},
    {"ipc": "365", "bns": "145", "type": "exact", "changes": []},
    {"ipc": "366", "bns": "146", "type": "exact", "changes": []},
    
    # Theft and Robbery
    {"ipc": "378", "bns": "302", "type": "modified", "changes": [{"type": "modified", "description": "Definition of theft updated"}]},
    {"ipc": "379", "bns": "303", "type": "exact", "changes": []},
    {"ipc": "380", "bns": "304", "type": "exact", "changes": []},
    {"ipc": "381", "bns": "305", "type": "exact", "changes": []},
    {"ipc": "382", "bns": "306", "type": "modified", "changes": [{"type": "modified", "description": "Theft after preparation for causing death or hurt"}]},
    {"ipc": "390", "bns": "309", "type": "exact", "changes": []},
    {"ipc": "391", "bns": "310", "type": "exact", "changes": []},
    {"ipc": "392", "bns": "311", "type": "exact", "changes": []},
    {"ipc": "393", "bns": "312", "type": "exact", "changes": []},
    {"ipc": "394", "bns": "313", "type": "exact", "changes": []},
    {"ipc": "395", "bns": "314", "type": "exact", "changes": []},
    {"ipc": "396", "bns": "315", "type": "exact", "changes": []},
    {"ipc": "397", "bns": "316", "type": "exact", "changes": []},
    {"ipc": "398", "bns": "317", "type": "exact", "changes": []},
    
    # Cheating
    {"ipc": "415", "bns": "316", "type": "modified", "changes": [{"type": "modified", "description": "Definition of cheating updated"}]},
    {"ipc": "416", "bns": "317", "type": "exact", "changes": []},
    {"ipc": "417", "bns": "318", "type": "exact", "changes": []},
    {"ipc": "418", "bns": "319", "type": "exact", "changes": []},
    {"ipc": "419", "bns": "320", "type": "exact", "changes": []},
    {"ipc": "420", "bns": "318", "type": "modified", "changes": [{"type": "added", "description": "Digital and electronic fraud explicitly covered"}, {"type": "modified", "description": "Enhanced provisions for financial crimes"}]},
    
    # Criminal Intimidation and Defamation
    {"ipc": "499", "bns": "356", "type": "modified", "changes": [{"type": "modified", "description": "Defamation provisions - exceptions updated"}]},
    {"ipc": "500", "bns": "357", "type": "exact", "changes": []},
    {"ipc": "503", "bns": "351", "type": "exact", "changes": []},
    {"ipc": "504", "bns": "352", "type": "exact", "changes": []},
    {"ipc": "506", "bns": "351", "type": "modified", "changes": [{"type": "modified", "description": "Criminal intimidation - merged provisions"}]},
    {"ipc": "507", "bns": "352", "type": "exact", "changes": []},
    
    # Documents and Property
    {"ipc": "463", "bns": "336", "type": "exact", "changes": []},
    {"ipc": "464", "bns": "337", "type": "modified", "changes": [{"type": "modified", "description": "Making a false document - electronic documents included"}]},
    {"ipc": "465", "bns": "338", "type": "exact", "changes": []},
    {"ipc": "466", "bns": "339", "type": "exact", "changes": []},
    {"ipc": "467", "bns": "340", "type": "modified", "changes": [{"type": "modified", "description": "Forgery of valuable security - enhanced punishment"}], "punishment_changed": True, "old_punishment": "Up to life + fine", "new_punishment": "Up to life + fine", "punishment_increased": False},
    {"ipc": "468", "bns": "341", "type": "exact", "changes": []},
    {"ipc": "469", "bns": "342", "type": "exact", "changes": []},
    {"ipc": "470", "bns": "343", "type": "exact", "changes": []},
    {"ipc": "471", "bns": "344", "type": "exact", "changes": []},
    
    # Offences Against Public Tranquility
    {"ipc": "141", "bns": "189", "type": "modified", "changes": [{"type": "modified", "description": "Unlawful assembly definition updated"}]},
    {"ipc": "142", "bns": "190", "type": "exact", "changes": []},
    {"ipc": "143", "bns": "191", "type": "exact", "changes": []},
    {"ipc": "144", "bns": "192", "type": "exact", "changes": []},
    {"ipc": "145", "bns": "192", "type": "exact", "changes": []},
    {"ipc": "146", "bns": "194", "type": "exact", "changes": []},
    {"ipc": "147", "bns": "195", "type": "exact", "changes": []},
    {"ipc": "148", "bns": "196", "type": "exact", "changes": []},
    {"ipc": "149", "bns": "190", "type": "modified", "changes": [{"type": "modified", "description": "Common object doctrine - clearer language"}]},
    {"ipc": "153A", "bns": "196", "type": "modified", "changes": [{"type": "modified", "description": "Promoting enmity - now includes electronic means"}]},
    {"ipc": "153B", "bns": "197", "type": "exact", "changes": []},
    
    # Offences Against State
    {"ipc": "121", "bns": "148", "type": "exact", "changes": []},
    {"ipc": "121A", "bns": "149", "type": "exact", "changes": []},
    {"ipc": "122", "bns": "150", "type": "exact", "changes": []},
    {"ipc": "123", "bns": "151", "type": "exact", "changes": []},
    {"ipc": "124", "bns": "152", "type": "modified", "changes": [{"type": "removed", "description": "Sedition section removed"}, {"type": "added", "description": "New provisions for acts endangering sovereignty"}]},
    {"ipc": "124A", "bns": "152", "type": "modified", "changes": [{"type": "modified", "description": "Sedition replaced with endangering sovereignty of India"}]},
    
    # New Sections in BNS
    {"ipc": "N/A", "bns": "111", "type": "new", "changes": [{"type": "added", "description": "Organized crime - NEW SECTION in BNS"}]},
    {"ipc": "N/A", "bns": "112", "type": "new", "changes": [{"type": "added", "description": "Petty organized crime - NEW SECTION in BNS"}]},
    {"ipc": "N/A", "bns": "113", "type": "new", "changes": [{"type": "added", "description": "Terrorist act - NEW SECTION in BNS"}]},
]


def seed_mappings():
    """Seed IPC-BNS mappings into the database."""
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Get all statutes
        statutes = session.query(Statute).all()
        ipc_statutes = {s.section_number: s for s in statutes if s.act_code == "IPC"}
        bns_statutes = {s.section_number: s for s in statutes if s.act_code == "BNS"}
        
        print(f"Found {len(ipc_statutes)} IPC sections and {len(bns_statutes)} BNS sections")
        
        created_count = 0
        skipped_count = 0
        
        for mapping_data in IPC_BNS_MAPPINGS:
            ipc_num = mapping_data["ipc"]
            bns_num = mapping_data["bns"]
            
            # Skip if IPC is N/A (new BNS sections)
            if ipc_num == "N/A":
                skipped_count += 1
                continue
            
            # Find matching statutes
            ipc_statute = ipc_statutes.get(ipc_num)
            bns_statute = bns_statutes.get(bns_num)
            
            if not ipc_statute:
                print(f"⚠️  IPC Section {ipc_num} not found in database")
                skipped_count += 1
                continue
                
            if not bns_statute:
                print(f"⚠️  BNS Section {bns_num} not found in database")
                skipped_count += 1
                continue
            
            # Check if mapping already exists
            existing = session.query(IPCBNSMapping).filter(
                IPCBNSMapping.ipc_section_id == ipc_statute.id,
                IPCBNSMapping.bns_section_id == bns_statute.id
            ).first()
            
            if existing:
                skipped_count += 1
                continue
            
            # Create mapping
            mapping = IPCBNSMapping(
                ipc_section_id=ipc_statute.id,
                bns_section_id=bns_statute.id,
                mapping_type=mapping_data.get("type", "exact"),
                changes=mapping_data.get("changes", []),
                punishment_changed=mapping_data.get("punishment_changed", False),
                old_punishment=mapping_data.get("old_punishment"),
                new_punishment=mapping_data.get("new_punishment"),
                punishment_increased=mapping_data.get("punishment_increased")
            )
            
            session.add(mapping)
            created_count += 1
            print(f"✅ Created mapping: IPC {ipc_num} → BNS {bns_num}")
        
        session.commit()
        print(f"\n🎉 Seeding complete!")
        print(f"   Created: {created_count} mappings")
        print(f"   Skipped: {skipped_count} (not found or already exists)")
        
    except Exception as e:
        session.rollback()
        print(f"❌ Error seeding mappings: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_mappings()
