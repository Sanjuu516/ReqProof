import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from app.database import get_db
from app.config import settings
from app.models import User, Project, Requirement, AtomicClaim, Artifact, AnalysisRun, EvidenceRecord, ClaimResult
from app.services.auth_service import get_current_user

router = APIRouter(prefix="/system", tags=["System & Database"])

class ApiKeyUpdate(BaseModel):
    api_key: str

@router.get("/database-overview")
def get_database_overview(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns transparency details about where the database is stored,
    all tables, and registered users for debugging and audit purposes.
    """
    db_location = settings.DATABASE_URL
    if db_location.startswith("sqlite:///"):
        relative_path = db_location.replace("sqlite:///", "")
        db_location = os.path.abspath(relative_path)

    users = db.query(User).all()
    user_list = [
        {
            "user_id": u.user_id,
            "name": u.name,
            "email": u.email,
            "created_at": str(u.created_at),
            "password_hash_preview": u.password_hash[:20] + "..." if u.password_hash else "None"
        }
        for u in users
    ]

    stats = {
        "database_type": "SQLite (Default)" if "sqlite" in settings.DATABASE_URL else "MySQL",
        "database_storage_location": db_location,
        "database_file_exists": os.path.exists(db_location) if "sqlite" in settings.DATABASE_URL else True,
        "tables": {
            "users": db.query(func.count(User.user_id)).scalar() or 0,
            "projects": db.query(func.count(Project.project_id)).scalar() or 0,
            "requirements": db.query(func.count(Requirement.requirement_id)).scalar() or 0,
            "atomic_claims": db.query(func.count(AtomicClaim.claim_id)).scalar() or 0,
            "artifacts": db.query(func.count(Artifact.artifact_id)).scalar() or 0,
            "analysis_runs": db.query(func.count(AnalysisRun.analysis_run_id)).scalar() or 0,
            "evidence_records": db.query(func.count(EvidenceRecord.evidence_id)).scalar() or 0,
            "claim_results": db.query(func.count(ClaimResult.result_id)).scalar() or 0,
        },
        "registered_users": user_list,
        "gemini_api_configured": bool(settings.GEMINI_API_KEY),
        "gemini_model": settings.GEMINI_MODEL
    }

    return stats

@router.get("/gemini-status")
def get_gemini_status(current_user: User = Depends(get_current_user)):
    return {
        "configured": bool(settings.GEMINI_API_KEY),
        "masked_key": f"{settings.GEMINI_API_KEY[:6]}...{settings.GEMINI_API_KEY[-4:]}" if settings.GEMINI_API_KEY else "Not configured",
        "model": settings.GEMINI_MODEL,
        "fallback_active": not bool(settings.GEMINI_API_KEY)
    }

@router.post("/gemini-key")
def update_gemini_key(body: ApiKeyUpdate, current_user: User = Depends(get_current_user)):
    settings.GEMINI_API_KEY = body.api_key.strip()
    return {
        "message": "Gemini API key updated successfully in application memory.",
        "configured": bool(settings.GEMINI_API_KEY)
    }
