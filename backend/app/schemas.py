"""
NyayaShastra - Pydantic Schemas
Request/Response models for API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# ============== Enums ==============

class Language(str, Enum):
    ENGLISH = "en"
    HINDI = "hi"


class AgentType(str, Enum):
    QUERY = "query"
    STATUTE = "statute"
    CASE = "case"
    REGULATORY = "regulatory"
    CITATION = "citation"
    SUMMARY = "summary"
    RESPONSE = "response"


class AgentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class LegalDomain(str, Enum):
    CRIMINAL = "criminal"
    CIVIL_FAMILY = "civil_family"
    CORPORATE = "corporate"
    IT_CYBER = "it_cyber"
    ENVIRONMENT = "environment"
    CONSTITUTIONAL = "constitutional"
    PROPERTY = "property"
    TRAFFIC = "traffic"
    OTHER = "other"
    ALL = "all"


# ============== Chat Schemas ==============

class Citation(BaseModel):
    """Citation reference."""
    id: str
    title: str
    source: str  # gazette, supreme_court, high_court, law_commission
    url: str
    excerpt: Optional[str] = None
    year: Optional[int] = None
    court: Optional[str] = None


class StatuteReference(BaseModel):
    """Referenced statute."""
    id: str
    section: str
    act: str
    act_code: str
    title: str
    content: str
    content_hi: Optional[str] = None


class AgentProcessingStep(BaseModel):
    """Agent processing step status."""
    agent: AgentType
    status: AgentStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result_summary: Optional[str] = None


class ChatMessageRequest(BaseModel):
    """Chat message request from client."""
    content: str = Field(..., min_length=1, max_length=5000)
    language: Language = Language.ENGLISH
    session_id: Optional[str] = None
    domain: Optional[str] = None


class ChatMessageResponse(BaseModel):
    """Chat message response to client."""
    id: str
    role: str
    content: str
    content_hi: Optional[str] = None
    citations: List[Citation] = []
    statutes: List[StatuteReference] = []
    agent_pipeline: List[AgentProcessingStep] = []
    timestamp: datetime
    session_id: str


class ChatStreamChunk(BaseModel):
    """Streaming chunk for real-time updates."""
    type: str  # agent_status, content_chunk, citation, statute, complete
    data: Dict[str, Any]


# ============== Statute Schemas ==============

class StatuteBase(BaseModel):
    """Base statute schema."""
    section_number: str
    act_name: str
    act_code: str
    title_en: str
    title_hi: Optional[str] = None
    content_en: str
    content_hi: Optional[str] = None
    domain: Optional[str] = None


class StatuteCreate(StatuteBase):
    """Create statute schema."""
    chapter: Optional[str] = None
    year_enacted: Optional[int] = None
    punishment_description: Optional[str] = None
    min_punishment: Optional[str] = None
    max_punishment: Optional[str] = None
    is_bailable: Optional[bool] = None
    is_cognizable: Optional[bool] = None


class StatuteResponse(StatuteBase):
    """Statute response schema."""
    id: int
    chapter: Optional[str] = None
    year_enacted: Optional[int] = None
    punishment_description: Optional[str] = None
    is_bailable: Optional[bool] = None
    is_cognizable: Optional[bool] = None
    
    class Config:
        from_attributes = True


class StatuteSearchRequest(BaseModel):
    """Search request for statutes."""
    query: str
    act_codes: Optional[List[str]] = None  # Filter by act
    domain: Optional[LegalDomain] = None
    language: Language = Language.ENGLISH
    limit: int = Field(default=10, le=50)


class StatuteSearchResponse(BaseModel):
    """Search response with statutes."""
    results: List[StatuteResponse]
    total: int
    query: str


# ============== IPC-BNS Comparison Schemas ==============

class ChangeDetail(BaseModel):
    """Change detail in IPC to BNS mapping."""
    type: str  # added, removed, modified
    description: str
    description_hi: Optional[str] = None


class PunishmentChange(BaseModel):
    """Punishment change details."""
    old: str
    new: str
    increased: bool


class IPCBNSComparisonItem(BaseModel):
    """IPC to BNS comparison item."""
    id: str
    ipc_section: str
    ipc_title: str
    ipc_content: str
    bns_section: str
    bns_title: str
    bns_content: str
    changes: List[ChangeDetail] = []
    punishment_change: Optional[PunishmentChange] = None
    mapping_type: Optional[str] = None
    notes: Optional[str] = None


class IPCBNSComparisonRequest(BaseModel):
    """Request for IPC-BNS comparison."""
    ipc_section: Optional[str] = None
    bns_section: Optional[str] = None
    search_query: Optional[str] = None
    language: Language = Language.ENGLISH


class IPCBNSComparisonResponse(BaseModel):
    """Response with comparisons."""
    comparisons: List[IPCBNSComparisonItem]
    total: int


# ============== Case Law Schemas ==============

class CaseLawBase(BaseModel):
    """Base case law schema."""
    case_number: str
    case_name: str
    case_name_hi: Optional[str] = None
    court: str
    court_name: Optional[str] = None
    judgment_date: Optional[datetime] = None
    summary_en: Optional[str] = None
    summary_hi: Optional[str] = None


class CaseLawResponse(CaseLawBase):
    """Case law response schema."""
    id: int
    is_landmark: bool = False
    citation_string: Optional[str] = None
    source_url: Optional[str] = None
    key_holdings: Optional[List[str]] = None
    domain: Optional[str] = None
    tags: Optional[List[str]] = None
    
    class Config:
        from_attributes = True


class CaseLawSearchRequest(BaseModel):
    """Case law search request."""
    query: str
    court: Optional[str] = None
    domain: Optional[LegalDomain] = None
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    landmark_only: bool = False
    language: Language = Language.ENGLISH
    limit: int = Field(default=10, le=50)


class CaseLawSearchResponse(BaseModel):
    """Case law search response."""
    results: List[CaseLawResponse]
    total: int
    query: str


# ============== Document Upload Schemas ==============

class DocumentSummary(BaseModel):
    """Document summary after processing."""
    key_arguments: List[str] = []
    verdict: Optional[str] = None
    cited_sections: List[Dict[str, str]] = []  # [{act, section}]
    parties: Optional[str] = None
    court_name: Optional[str] = None
    date: Optional[str] = None


class DocumentUploadResponse(BaseModel):
    """Response after document upload."""
    document_id: str
    filename: str
    status: str
    message: str


class DocumentStatusResponse(BaseModel):
    """Document processing status."""
    document_id: str
    filename: str
    status: str  # pending, processing, completed, error
    progress: int  # 0-100
    summary: Optional[DocumentSummary] = None
    error_message: Optional[str] = None


# ============== Agent Status Schemas ==============

class AgentInfo(BaseModel):
    """Agent information."""
    id: AgentType
    name: str
    name_hi: str
    description: str
    description_hi: str
    color: str


class AgentPipelineStatus(BaseModel):
    """Current status of all agents in pipeline."""
    session_id: str
    agents: List[AgentProcessingStep]
    current_agent: Optional[AgentType] = None
    is_complete: bool = False
    

# ============== Health Check ==============

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    database: str
    vector_db: str
    llm: str
