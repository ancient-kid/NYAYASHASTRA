"""
NyayaShastra - Database Models
SQLAlchemy ORM models for legal data storage.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON, Enum
from sqlalchemy.orm import relationship, declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()


class LegalDomain(enum.Enum):
    """Legal domain categories."""
    CRIMINAL = "criminal"
    CIVIL_FAMILY = "civil_family"
    CORPORATE = "corporate"
    IT_CYBER = "it_cyber"
    ENVIRONMENT = "environment"
    CONSTITUTIONAL = "constitutional"
    PROPERTY = "property"
    TRAFFIC = "traffic"
    OTHER = "other"


class Court(enum.Enum):
    """Court types."""
    SUPREME_COURT = "supreme_court"
    HIGH_COURT = "high_court"
    DISTRICT_COURT = "district_court"
    TRIBUNAL = "tribunal"
    OTHER = "other"


class Statute(Base):
    """Legal statute/section model."""
    __tablename__ = "statutes"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Section identification
    section_number = Column(String(50), nullable=False, index=True)
    act_name = Column(String(200), nullable=False, index=True)
    act_code = Column(String(20), nullable=False, index=True)  # IPC, BNS, IT, etc.
    
    # Content
    title_en = Column(String(500), nullable=False)
    title_hi = Column(String(500))
    content_en = Column(Text, nullable=False)
    content_hi = Column(Text)
    
    # Metadata
    chapter = Column(String(100))
    year_enacted = Column(Integer)
    domain = Column(String(50), default="criminal")
    
    # Punishment details
    punishment_description = Column(Text)
    min_punishment = Column(String(200))
    max_punishment = Column(String(200))
    is_bailable = Column(Boolean)
    is_cognizable = Column(Boolean)
    
    # Embeddings
    embedding_id = Column(String(100))  # Reference to vector DB
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    mappings_old = relationship("IPCBNSMapping", back_populates="ipc_section", foreign_keys="IPCBNSMapping.ipc_section_id")
    mappings_new = relationship("IPCBNSMapping", back_populates="bns_section", foreign_keys="IPCBNSMapping.bns_section_id")
    citations = relationship("CaseLaw", secondary="case_statute_links", back_populates="cited_statutes")


class IPCBNSMapping(Base):
    """Mapping between old IPC sections and new BNS sections."""
    __tablename__ = "ipc_bns_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign keys
    ipc_section_id = Column(Integer, ForeignKey("statutes.id"), nullable=False)
    bns_section_id = Column(Integer, ForeignKey("statutes.id"), nullable=False)
    
    # Mapping details
    mapping_type = Column(String(50))  # exact, modified, merged, split, new, removed
    
    # Change details
    changes = Column(JSON)  # List of changes: {type, description}
    punishment_changed = Column(Boolean, default=False)
    old_punishment = Column(String(500))
    new_punishment = Column(String(500))
    punishment_increased = Column(Boolean)
    
    # Notes
    notes_en = Column(Text)
    notes_hi = Column(Text)
    
    # Relationships
    ipc_section = relationship("Statute", back_populates="mappings_old", foreign_keys=[ipc_section_id])
    bns_section = relationship("Statute", back_populates="mappings_new", foreign_keys=[bns_section_id])


class CaseLaw(Base):
    """Case law/judgment model."""
    __tablename__ = "case_laws"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Case identification
    case_number = Column(String(200), nullable=False, index=True)
    case_name = Column(String(500), nullable=False)
    case_name_hi = Column(String(500))
    
    # Court details
    court = Column(String(50), default="supreme_court")
    court_name = Column(String(200))
    bench = Column(String(500))
    
    # Dates
    judgment_date = Column(DateTime)
    reporting_year = Column(Integer, index=True)
    
    # Content
    summary_en = Column(Text)
    summary_hi = Column(Text)
    full_text = Column(Text)
    key_holdings = Column(JSON)  # List of key holdings
    
    # Classification
    is_landmark = Column(Boolean, default=False)
    domain = Column(String(50))
    tags = Column(JSON)  # List of tags
    
    # Citations
    citation_string = Column(String(500))  # e.g., "AIR 2023 SC 1234"
    neutral_citation = Column(String(200))
    source_url = Column(String(500))
    
    # Embeddings
    embedding_id = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Relationships
    cited_statutes = relationship("Statute", secondary="case_statute_links", back_populates="citations")


class CaseStatuteLink(Base):
    """Link table between cases and statutes."""
    __tablename__ = "case_statute_links"
    
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey("case_laws.id"), nullable=False)
    statute_id = Column(Integer, ForeignKey("statutes.id"), nullable=False)
    relevance_score = Column(Float)


class ChatSession(Base):
    """Chat session model."""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # User info (optional)
    user_id = Column(String(100))
    
    # Session metadata
    language = Column(String(10), default="en")
    domain = Column(String(50), default="all")
    started_at = Column(DateTime, server_default=func.now())
    last_activity = Column(DateTime, onupdate=func.now())
    
    # Relationships
    messages = relationship("ChatMessage", back_populates="session")


class ChatMessage(Base):
    """Chat message model."""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    
    # Message content
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    content_hi = Column(Text)
    
    # Metadata
    agent_path = Column(JSON)  # Which agents processed this
    citations = Column(JSON)  # List of citations used
    statutes_referenced = Column(JSON)  # List of statute IDs
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    
    # Token usage
    prompt_tokens = Column(Integer)
    completion_tokens = Column(Integer)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")


class DocumentUpload(Base):
    """Uploaded document model."""
    __tablename__ = "document_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(100), unique=True, nullable=False, index=True)
    
    # File info
    filename = Column(String(500), nullable=False)
    file_size = Column(Integer)
    file_type = Column(String(50))
    storage_path = Column(String(500))
    
    # Processing status
    status = Column(String(50), default="pending")  # pending, processing, completed, error
    error_message = Column(Text)
    
    # Extracted content
    extracted_text = Column(Text)
    page_count = Column(Integer)
    
    # Summary
    summary = Column(JSON)  # Structured summary
    key_arguments = Column(JSON)
    verdict = Column(Text)
    cited_sections = Column(JSON)
    parties = Column(String(500))
    court_name = Column(String(200))
    judgment_date = Column(DateTime)
    
    # Timestamps
    uploaded_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime)
    
    # Session link
    session_id = Column(String(100))


