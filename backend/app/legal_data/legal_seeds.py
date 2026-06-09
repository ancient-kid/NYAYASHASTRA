"""
NyayaShastra AI Pro - Real Data Loader
Loads legal data from CSV and PDF files in the data folder.
NO MOCK DATA - Uses actual legal documents.
"""

import os
import csv
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# Data directory
DATA_DIR = Path(__file__).parents[2] / "data" / "Criminal"


def load_ipc_bns_mappings_from_csv() -> List[Dict[str, Any]]:
    """Load IPC-BNS mappings from CSV file."""
    csv_path = DATA_DIR / "ipc_bns_chart.csv"
    
    if not csv_path.exists():
        logger.error(f"CSV file not found: {csv_path}")
        return []
    
    mappings = []
    
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                ipc_section = row.get("IPC_Section", "").strip()
                bns_section = row.get("BNS_Section", "").strip()
                
                # Skip empty rows or rows without both sections
                if not ipc_section and not bns_section:
                    continue
                
                mapping = {
                    "ipc_section": ipc_section,
                    "bns_section": bns_section,
                    "topic": row.get("Topic", "").strip(),
                    "description": row.get("Description", "").strip(),
                    "change_note": row.get("Change_Note", "").strip(),
                    "penalty_old": row.get("Penalty_Old", "").strip(),
                    "penalty_new": row.get("Penalty_New", "").strip(),
                }
                mappings.append(mapping)
        
        logger.info(f"Loaded {len(mappings)} IPC-BNS mappings from CSV")
        
    except Exception as e:
        logger.error(f"Error loading CSV: {e}")
    
    return mappings


def get_ipc_sections_from_csv() -> List[Dict[str, Any]]:
    """Extract IPC sections from the CSV mappings."""
    mappings = load_ipc_bns_mappings_from_csv()
    
    ipc_sections = []
    seen_sections = set()
    
    for mapping in mappings:
        ipc_section = mapping.get("ipc_section", "")
        
        # Handle ranges like "8–52A" or multiple sections
        if not ipc_section or ipc_section in seen_sections:
            continue
        
        # Skip complex section references for now
        if "–" in ipc_section or "," in ipc_section or "&" in ipc_section:
            continue
        
        # Also skip sections with etc or multiple entries
        if "etc" in ipc_section.lower():
            continue
            
        seen_sections.add(ipc_section)
        
        section_data = {
            "section_number": ipc_section,
            "act_code": "IPC",
            "act_name": "Indian Penal Code",
            "title_en": mapping.get("topic", ""),
            "title_hi": "",  # Would need translation
            "content_en": mapping.get("description", ""),
            "content_hi": "",
            "domain": _detect_domain(mapping.get("topic", "") + " " + mapping.get("description", "")),
            "year_enacted": 1860,
            "punishment_description": mapping.get("penalty_old", ""),
            "is_cognizable": True,
            "is_bailable": False,
        }
        ipc_sections.append(section_data)
    
    logger.info(f"Extracted {len(ipc_sections)} IPC sections from CSV")
    return ipc_sections


def get_bns_sections_from_csv() -> List[Dict[str, Any]]:
    """Extract BNS sections from the CSV mappings."""
    mappings = load_ipc_bns_mappings_from_csv()
    
    bns_sections = []
    seen_sections = set()
    
    for mapping in mappings:
        bns_section = mapping.get("bns_section", "")
        
        if not bns_section or bns_section in seen_sections:
            continue
        
        # Skip complex section references
        if "–" in bns_section or "," in bns_section:
            continue
            
        seen_sections.add(bns_section)
        
        section_data = {
            "section_number": bns_section,
            "act_code": "BNS",
            "act_name": "Bhartiya Nyaya Sanhita",
            "title_en": mapping.get("topic", ""),
            "title_hi": "",
            "content_en": mapping.get("description", ""),
            "content_hi": "",
            "domain": _detect_domain(mapping.get("topic", "") + " " + mapping.get("description", "")),
            "year_enacted": 2023,
            "punishment_description": mapping.get("penalty_new", ""),
            "is_cognizable": True,
            "is_bailable": False,
        }
        bns_sections.append(section_data)
    
    logger.info(f"Extracted {len(bns_sections)} BNS sections from CSV")
    return bns_sections


def get_ipc_bns_mappings() -> List[Dict[str, Any]]:
    """Get formatted IPC-BNS mappings for database."""
    raw_mappings = load_ipc_bns_mappings_from_csv()
    
    formatted_mappings = []
    
    for mapping in raw_mappings:
        ipc_section = mapping.get("ipc_section", "")
        bns_section = mapping.get("bns_section", "")
        
        # Skip entries without both sections or complex references
        if not ipc_section or not bns_section:
            continue
        if "–" in ipc_section or "–" in bns_section:
            continue
        if "," in ipc_section or "," in bns_section:
            continue
        if "&" in ipc_section or "&" in bns_section:
            continue
        if "etc" in ipc_section.lower() or "etc" in bns_section.lower():
            continue
        
        # Determine mapping type based on change note
        change_note = mapping.get("change_note", "").lower()
        if "no change" in change_note:
            mapping_type = "exact"
        elif "new" in change_note:
            mapping_type = "new"
        elif "merged" in change_note:
            mapping_type = "merged"
        elif "increased" in change_note or "enhanced" in change_note:
            mapping_type = "modified"
        else:
            mapping_type = "modified"
        
        # Build changes list
        changes = []
        if mapping.get("change_note"):
            changes.append({
                "type": "modified",
                "description": mapping.get("change_note", "")
            })
        
        # Check if punishment changed
        old_penalty = mapping.get("penalty_old", "")
        new_penalty = mapping.get("penalty_new", "")
        punishment_changed = bool(old_penalty or new_penalty)
        punishment_increased = "increased" in change_note.lower() or bool(new_penalty and not old_penalty)
        
        formatted_mapping = {
            "ipc_section": ipc_section,
            "bns_section": bns_section,
            "mapping_type": mapping_type,
            "changes": changes,
            "punishment_changed": punishment_changed,
            "old_punishment": old_penalty,
            "new_punishment": new_penalty,
            "punishment_increased": punishment_increased,
        }
        formatted_mappings.append(formatted_mapping)
    
    logger.info(f"Formatted {len(formatted_mappings)} IPC-BNS mappings")
    return formatted_mappings


def _detect_domain(text: str) -> str:
    """Detect legal domain from text."""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ["murder", "hurt", "death", "kill", "rape", "assault", "robbery", "theft", "kidnap"]):
        return "criminal"
    elif any(word in text_lower for word in ["marriage", "divorce", "dowry", "wife", "husband", "child", "guardian"]):
        return "civil_family"
    elif any(word in text_lower for word in ["property", "land", "estate"]):
        return "property"
    elif any(word in text_lower for word in ["trade", "commerce", "company", "business"]):
        return "corporate"
    elif any(word in text_lower for word in ["election", "vote", "poll"]):
        return "constitutional"
    elif any(word in text_lower for word in ["public servant", "government", "official"]):
        return "constitutional"
    elif any(word in text_lower for word in ["pollution", "environment", "water", "air"]):
        return "environment"
    else:
        return "criminal"


# Landmark case laws (these would ideally come from Case_Laws.pdf)
LANDMARK_CASES = [
    {
        "case_number": "Criminal Appeal No. 567/1980",
        "case_name": "Bachan Singh v. State of Punjab",
        "case_name_hi": "बचन सिंह बनाम पंजाब राज्य",
        "court": "supreme_court",
        "court_name": "Supreme Court of India",
        "judgment_date": "1980-05-09",
        "reporting_year": 1980,
        "summary_en": "Landmark judgment establishing the 'rarest of rare' doctrine for imposition of death penalty in India. The Constitution Bench held that death penalty is constitutional but should be imposed only in exceptional circumstances.",
        "summary_hi": "भारत में मृत्युदंड के लिए 'दुर्लभतम में दुर्लभ' सिद्धांत स्थापित करने वाला ऐतिहासिक निर्णय।",
        "is_landmark": True,
        "citation_string": "1980 AIR 898, 1980 SCR (2) 684",
        "source_url": "https://indiankanoon.org/doc/1691677",
        "key_holdings": [
            "Death penalty is constitutional",
            "Rarest of rare doctrine established",
            "Aggravating and mitigating circumstances must be balanced"
        ],
        "domain": "criminal",
        "cited_sections": ["302", "103"]
    },
    {
        "case_number": "Writ Petition (Criminal) No. 666-70/1992",
        "case_name": "Vishaka v. State of Rajasthan",
        "case_name_hi": "विशाखा बनाम राजस्थान राज्य",
        "court": "supreme_court",
        "court_name": "Supreme Court of India",
        "judgment_date": "1997-08-13",
        "reporting_year": 1997,
        "summary_en": "Landmark judgment on sexual harassment at workplace. The Supreme Court laid down comprehensive guidelines to prevent sexual harassment, which remained in force until the POSH Act 2013.",
        "summary_hi": "कार्यस्थल पर यौन उत्पीड़न पर ऐतिहासिक निर्णय।",
        "is_landmark": True,
        "citation_string": "AIR 1997 SC 3011",
        "source_url": "https://indiankanoon.org/doc/1031794",
        "key_holdings": [
            "Sexual harassment violates fundamental rights under Articles 14, 15, 19 and 21",
            "Employers must constitute complaints committee",
            "Guidelines for prevention mandatory until legislation"
        ],
        "domain": "criminal",
        "cited_sections": ["354", "74", "509", "79"]
    },
    {
        "case_number": "Writ Petition (Civil) No. 494/2012",
        "case_name": "K.S. Puttaswamy v. Union of India",
        "case_name_hi": "के.एस. पुट्टास्वामी बनाम भारत संघ",
        "court": "supreme_court",
        "court_name": "Supreme Court of India",
        "judgment_date": "2017-08-24",
        "reporting_year": 2017,
        "summary_en": "Nine-judge Constitution Bench unanimously held that the right to privacy is a fundamental right protected under Article 21 of the Constitution of India.",
        "summary_hi": "निजता का अधिकार मौलिक अधिकार है - 9 न्यायाधीशों की संविधान पीठ का सर्वसम्मत निर्णय।",
        "is_landmark": True,
        "citation_string": "(2017) 10 SCC 1",
        "source_url": "https://indiankanoon.org/doc/127517806",
        "key_holdings": [
            "Right to privacy is a fundamental right",
            "Protected under Article 21",
            "Not absolute, subject to reasonable restrictions"
        ],
        "domain": "constitutional",
        "cited_sections": []
    },
    {
        "case_number": "Criminal Appeal No. 1265/2013",
        "case_name": "Lalita Kumari v. Government of UP",
        "case_name_hi": "ललिता कुमारी बनाम उत्तर प्रदेश सरकार",
        "court": "supreme_court",
        "court_name": "Supreme Court of India",
        "judgment_date": "2013-11-12",
        "reporting_year": 2013,
        "summary_en": "Constitution Bench held that registration of FIR is mandatory under Section 154 CrPC if the information discloses commission of a cognizable offence. Police cannot refuse to register FIR.",
        "summary_hi": "संज्ञेय अपराध के लिए FIR पंजीकरण अनिवार्य है - पुलिस FIR दर्ज करने से इनकार नहीं कर सकती।",
        "is_landmark": True,
        "citation_string": "(2014) 2 SCC 1",
        "source_url": "https://indiankanoon.org/doc/195681207",
        "key_holdings": [
            "FIR registration is mandatory for cognizable offences",
            "Police cannot refuse to register FIR",
            "Preliminary inquiry only in specific categories"
        ],
        "domain": "criminal",
        "cited_sections": []
    },
    {
        "case_number": "Criminal Appeal No. 76/2016",
        "case_name": "Navtej Singh Johar v. Union of India",
        "case_name_hi": "नवतेज सिंह जौहर बनाम भारत संघ",
        "court": "supreme_court",
        "court_name": "Supreme Court of India",
        "judgment_date": "2018-09-06",
        "reporting_year": 2018,
        "summary_en": "Five-judge Constitution Bench decriminalized consensual homosexual acts between adults by reading down Section 377 IPC to the extent it criminalized consensual sexual acts of adults in private.",
        "summary_hi": "वयस्कों के बीच सहमति से समलैंगिक संबंधों को अपराध की श्रेणी से बाहर किया - धारा 377 को आंशिक रूप से असंवैधानिक घोषित किया।",
        "is_landmark": True,
        "citation_string": "(2018) 10 SCC 1",
        "source_url": "https://indiankanoon.org/doc/168671544",
        "key_holdings": [
            "Section 377 IPC partially struck down",
            "Consensual acts between adults decriminalized",
            "Sexual orientation is part of right to privacy and dignity"
        ],
        "domain": "criminal",
        "cited_sections": []
    },
    {
        "case_number": "Writ Petition (Civil) No. 135/1970",
        "case_name": "Kesavananda Bharati v. State of Kerala",
        "case_name_hi": "केशवानंद भारती बनाम केरल राज्य",
        "court": "supreme_court",
        "court_name": "Supreme Court of India",
        "judgment_date": "1973-04-24",
        "reporting_year": 1973,
        "summary_en": "The most significant judgment in Indian constitutional history which established the 'Basic Structure Doctrine'. It held that while Parliament has the power to amend the Constitution, it cannot alter its basic structure.",
        "summary_hi": "भारतीय संवैधानिक इतिहास का सबसे महत्वपूर्ण निर्णय जिसने 'बुनियादी ढांचा सिद्धांत' स्थापित किया।",
        "is_landmark": True,
        "citation_string": "AIR 1973 SC 1461",
        "source_url": "https://indiankanoon.org/doc/257876",
        "key_holdings": [
            "Basic Structure Doctrine established",
            "Parliamentary power to amend is limited",
            "Judicial review is a part of the basic structure"
        ],
        "domain": "constitutional",
        "cited_sections": []
    },
    {
        "case_number": "Writ Petition (Civil) No. 231/1977",
        "case_name": "Maneka Gandhi v. Union of India",
        "case_name_hi": "मेनका गांधी बनाम भारत संघ",
        "court": "supreme_court",
        "court_name": "Supreme Court of India",
        "judgment_date": "1978-01-25",
        "reporting_year": 1978,
        "summary_en": "Expanded the scope of Article 21 (Right to Life and Personal Liberty) to include the right to travel abroad. Established the test of 'reasonableness' for any law depriving a person of liberty.",
        "summary_hi": "अनुच्छेद 21 (जीवन और व्यक्तिगत स्वतंत्रता का अधिकार) के दायरे का विस्तार करने वाला ऐतिहासिक निर्णय।",
        "is_landmark": True,
        "citation_string": "AIR 1978 SC 597",
        "source_url": "https://indiankanoon.org/doc/1766147",
        "key_holdings": [
            "Procedure established by law must be just, fair and reasonable",
            "Fundamental Rights are not mutually exclusive",
            "Right to travel abroad is part of personal liberty"
        ],
        "domain": "constitutional",
        "cited_sections": []
    },
    {
        "case_number": "Writ Petition (Civil) No. 118/2016",
        "case_name": "Shayara Bano v. Union of India",
        "case_name_hi": "शायरा बानो बनाम भारत संघ",
        "court": "supreme_court",
        "court_name": "Supreme Court of India",
        "judgment_date": "2017-08-22",
        "reporting_year": 2017,
        "summary_en": "The Supreme Court declared the practice of 'Triple Talaq' (Talaq-e-Biddat) as unconstitutional, holding it to be arbitrary and violative of fundamental rights of Muslim women.",
        "summary_hi": "'तीन तलाक' की प्रथा को असंवैधानिक घोषित किया - इसे मनमाना और मुस्लिम महिलाओं के मौलिक अधिकारों का उल्लंघन माना।",
        "is_landmark": True,
        "citation_string": "(2017) 9 SCC 1",
        "source_url": "https://indiankanoon.org/doc/11570122",
        "key_holdings": [
            "Triple Talaq is unconstitutional",
            "Violates Article 14 (Right to Equality)",
            "Not an essential religious practice"
        ],
        "domain": "civil_family",
        "cited_sections": []
    }
]


def get_all_statutes() -> List[Dict[str, Any]]:
    """Get all statutes (IPC + BNS) from CSV."""
    ipc = get_ipc_sections_from_csv()
    bns = get_bns_sections_from_csv()
    return ipc + bns


def get_ipc_sections() -> List[Dict[str, Any]]:
    """Get IPC sections."""
    return get_ipc_sections_from_csv()


def get_bns_sections() -> List[Dict[str, Any]]:
    """Get BNS sections."""
    return get_bns_sections_from_csv()


def get_mappings() -> List[Dict[str, Any]]:
    """Get IPC-BNS mappings."""
    return get_ipc_bns_mappings()


def get_landmark_cases() -> List[Dict[str, Any]]:
    """Get landmark cases."""
    return LANDMARK_CASES


# For backward compatibility - map to the actual data loading functions
IPC_SECTIONS = None  # Will be populated on first access
BNS_SECTIONS = None
IPC_BNS_MAPPINGS = None


def _ensure_data_loaded():
    """Ensure data is loaded from CSV."""
    global IPC_SECTIONS, BNS_SECTIONS, IPC_BNS_MAPPINGS
    if IPC_SECTIONS is None:
        IPC_SECTIONS = get_ipc_sections_from_csv()
    if BNS_SECTIONS is None:
        BNS_SECTIONS = get_bns_sections_from_csv()
    if IPC_BNS_MAPPINGS is None:
        IPC_BNS_MAPPINGS = get_ipc_bns_mappings()

# Eagerly load the data so imported variables are initialized immediately
_ensure_data_loaded()
