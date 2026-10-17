from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import datetime

# --- Auth Schemas ---
class UserRegister(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    user_id: int
    name: str
    email: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# --- Project Schemas ---
class ProjectCreate(BaseModel):
    project_name: str
    description: Optional[str] = None
    source_version: Optional[str] = "v1.0.0"

class ProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    description: Optional[str] = None
    source_version: Optional[str] = None

class ArtifactResponse(BaseModel):
    artifact_id: int
    project_id: int
    artifact_path: str
    artifact_type: str
    language: Optional[str] = None
    content_hash: Optional[str] = None
    analysis_status: str

    class Config:
        from_attributes = True

class ProjectResponse(BaseModel):
    project_id: int
    user_id: int
    project_name: str
    description: Optional[str] = None
    source_version: Optional[str] = None
    created_at: datetime.datetime
    artifacts_count: Optional[int] = 0
    requirements_count: Optional[int] = 0

    class Config:
        from_attributes = True


# --- Requirement & Claim Schemas ---
class AtomicClaimCreate(BaseModel):
    claim_text: str
    expected_behavior: str
    verification_criteria: Optional[str] = ""
    relevant_artifact_types: Optional[str] = "source,api,test"
    review_status: Optional[str] = "reviewed"

class AtomicClaimUpdate(BaseModel):
    claim_text: Optional[str] = None
    expected_behavior: Optional[str] = None
    verification_criteria: Optional[str] = None
    relevant_artifact_types: Optional[str] = None
    review_status: Optional[str] = None

class AtomicClaimResponse(BaseModel):
    claim_id: int
    requirement_id: int
    claim_text: str
    expected_behavior: Optional[str] = None
    verification_criteria: Optional[str] = None
    relevant_artifact_types: str
    review_status: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class RequirementCreate(BaseModel):
    requirement_text: str

class RequirementResponse(BaseModel):
    requirement_id: int
    project_id: int
    requirement_text: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    claims: List[AtomicClaimResponse] = []

    class Config:
        from_attributes = True


# --- Graph Schemas ---
class GraphNode(BaseModel):
    id: str
    type: str  # requirement or claim
    label: str
    data: Dict[str, Any]
    position: Optional[Dict[str, float]] = None

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    relationship_type: str = "decomposed_into" # decomposed_into, depends_on, conflicts_with

class RequirementGraphResponse(BaseModel):
    project_id: int
    nodes: List[GraphNode]
    edges: List[GraphEdge]


# --- Evidence & Result Schemas ---
class EvidenceRecordCreate(BaseModel):
    claim_id: int
    artifact_id: Optional[int] = None
    evidence_type: str  # static, ui, api, runtime, test
    polarity: str       # supporting, contradicting, inconclusive
    observation: str
    location_reference: Optional[str] = None
    provenance: Optional[str] = None
    meta_info: Optional[str] = None

class EvidenceRecordResponse(BaseModel):
    evidence_id: int
    analysis_run_id: int
    claim_id: int
    artifact_id: Optional[int] = None
    evidence_type: str
    polarity: str
    observation: str
    location_reference: Optional[str] = None
    provenance: Optional[str] = None
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class ClaimResultResponse(BaseModel):
    result_id: int
    analysis_run_id: int
    claim_id: int
    claim_text: Optional[str] = None
    status: str  # Fully Satisfied, Partially Satisfied, Missing, Contradictory, Unverifiable
    reason_codes: Optional[str] = None
    explanation: str
    sufficiency_state: str
    evidence_records: List[EvidenceRecordResponse] = []
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class AnalysisRunCreate(BaseModel):
    configuration: Optional[Dict[str, Any]] = None

class AnalysisRunResponse(BaseModel):
    analysis_run_id: int
    project_id: int
    source_version: Optional[str] = None
    status: str
    started_at: datetime.datetime
    completed_at: Optional[datetime.datetime] = None
    total_claims: int = 0
    fully_satisfied: int = 0
    partially_satisfied: int = 0
    missing: int = 0
    contradictory: int = 0
    unverifiable: int = 0

    class Config:
        from_attributes = True


# --- Report Schemas ---
class VerificationSummaryReport(BaseModel):
    project_name: str
    project_id: int
    source_version: str
    analysis_run_id: int
    generated_at: str
    metrics: Dict[str, Any]
    results: List[ClaimResultResponse]
    limitations: List[str]
