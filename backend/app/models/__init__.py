import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SQLEnum, Float, JSON
from sqlalchemy.orm import relationship
from app.database import Base

def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=utcnow)

    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    project_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    project_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    source_version = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=utcnow)

    owner = relationship("User", back_populates="projects")
    requirements = relationship("Requirement", back_populates="project", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="project", cascade="all, delete-orphan")
    analysis_runs = relationship("AnalysisRun", back_populates="project", cascade="all, delete-orphan")


class Requirement(Base):
    __tablename__ = "requirements"

    requirement_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
    requirement_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=datetime.datetime.utcnow)

    project = relationship("Project", back_populates="requirements")
    claims = relationship("AtomicClaim", back_populates="requirement", cascade="all, delete-orphan")


class AtomicClaim(Base):
    __tablename__ = "atomic_claims"

    claim_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    requirement_id = Column(Integer, ForeignKey("requirements.requirement_id"), nullable=False)
    claim_text = Column(Text, nullable=False)
    expected_behavior = Column(Text, nullable=True)
    verification_criteria = Column(Text, nullable=True)  # JSON or text description of required criteria
    relevant_artifact_types = Column(String(255), default="source,api,test")
    review_status = Column(String(50), default="reviewed")  # draft, reviewed, approved
    created_at = Column(DateTime, default=utcnow)

    requirement = relationship("Requirement", back_populates="claims")
    evidence_records = relationship("EvidenceRecord", back_populates="claim")
    results = relationship("ClaimResult", back_populates="claim")


class RequirementEdge(Base):
    __tablename__ = "requirement_edges"

    edge_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    source_claim_id = Column(Integer, ForeignKey("atomic_claims.claim_id"), nullable=False)
    target_claim_id = Column(Integer, ForeignKey("atomic_claims.claim_id"), nullable=False)
    relationship_type = Column(String(100), default="depends_on")  # depends_on, parent_child, conflicts_with


class Artifact(Base):
    __tablename__ = "artifacts"

    artifact_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
    artifact_path = Column(String(500), nullable=False)
    artifact_type = Column(String(100), nullable=False)  # source, ui, api, test_report, config
    language = Column(String(50), nullable=True)          # java, typescript, javascript, python, xml
    content_hash = Column(String(128), nullable=True)
    analysis_status = Column(String(50), default="processed")  # pending, processed, failed, skipped

    project = relationship("Project", back_populates="artifacts")
    evidence_records = relationship("EvidenceRecord", back_populates="artifact")


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    analysis_run_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=False)
    source_version = Column(String(100), nullable=True)
    status = Column(String(50), default="queued")  # queued, running, completed, partially_completed, failed
    started_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime, nullable=True)
    configuration = Column(Text, nullable=True)

    project = relationship("Project", back_populates="analysis_runs")
    evidence_records = relationship("EvidenceRecord", back_populates="analysis_run", cascade="all, delete-orphan")
    claim_results = relationship("ClaimResult", back_populates="analysis_run", cascade="all, delete-orphan")
    test_executions = relationship("TestExecution", back_populates="analysis_run", cascade="all, delete-orphan")


class EvidenceRecord(Base):
    __tablename__ = "evidence_records"

    evidence_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    analysis_run_id = Column(Integer, ForeignKey("analysis_runs.analysis_run_id"), nullable=False)
    claim_id = Column(Integer, ForeignKey("atomic_claims.claim_id"), nullable=False)
    artifact_id = Column(Integer, ForeignKey("artifacts.artifact_id"), nullable=True)
    evidence_type = Column(String(50), nullable=False)  # static, ui, api, runtime, test
    polarity = Column(String(50), nullable=False)       # supporting, contradicting, inconclusive
    observation = Column(Text, nullable=False)
    location_reference = Column(String(500), nullable=True) # e.g. src/auth/AuthController.java#L45-L62
    provenance = Column(String(255), nullable=True)         # analyzer name, timestamp, runner
    meta_info = Column(Text, nullable=True)                 # JSON details
    created_at = Column(DateTime, default=utcnow)

    analysis_run = relationship("AnalysisRun", back_populates="evidence_records")
    claim = relationship("AtomicClaim", back_populates="evidence_records")
    artifact = relationship("Artifact", back_populates="evidence_records")


class ClaimResult(Base):
    __tablename__ = "claim_results"

    result_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    analysis_run_id = Column(Integer, ForeignKey("analysis_runs.analysis_run_id"), nullable=False)
    claim_id = Column(Integer, ForeignKey("atomic_claims.claim_id"), nullable=False)
    status = Column(String(50), nullable=False)  # Fully Satisfied, Partially Satisfied, Missing, Contradictory, Unverifiable
    reason_codes = Column(Text, nullable=True)   # JSON array of reasons
    explanation = Column(Text, nullable=False)
    sufficiency_state = Column(String(50), default="sufficient")  # sufficient, insufficient
    created_at = Column(DateTime, default=utcnow)

    analysis_run = relationship("AnalysisRun", back_populates="claim_results")
    claim = relationship("AtomicClaim", back_populates="results")


class TestExecution(Base):
    __tablename__ = "test_executions"

    test_execution_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    analysis_run_id = Column(Integer, ForeignKey("analysis_runs.analysis_run_id"), nullable=False)
    test_name = Column(String(255), nullable=False)
    execution_source = Column(String(100), default="junit_report") # junit_report, reqproof_runner
    outcome = Column(String(50), nullable=False) # passed, failed, skipped, timed_out, errored
    duration_ms = Column(Float, default=0.0)
    log_reference = Column(Text, nullable=True)

    analysis_run = relationship("AnalysisRun", back_populates="test_executions")
