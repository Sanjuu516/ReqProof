import os
import shutil
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models import Project, User, Artifact, AnalysisRun, Requirement
from app.schemas import ProjectCreate, ProjectUpdate, ProjectResponse, ArtifactResponse, AnalysisRunResponse
from app.services.auth_service import get_current_user
from app.services.zip_service import extract_and_scan_zip

router = APIRouter(prefix="/projects", tags=["Projects"])

def get_authorized_project(project_id: int, user: User, db: Session) -> Project:
    project = db.query(Project).filter(Project.project_id == project_id, Project.user_id == user.user_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or unauthorized.")
    return project

@router.post("", response_model=ProjectResponse)
def create_project(project_in: ProjectCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = Project(
        user_id=current_user.user_id,
        project_name=project_in.project_name,
        description=project_in.description,
        source_version=project_in.source_version or "v1.0.0"
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return ProjectResponse(
        project_id=project.project_id,
        user_id=project.user_id,
        project_name=project.project_name,
        description=project.description,
        source_version=project.source_version,
        created_at=project.created_at,
        artifacts_count=0,
        requirements_count=0
    )

@router.get("", response_model=List[ProjectResponse])
def list_projects(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    projects = db.query(Project).filter(Project.user_id == current_user.user_id).order_by(Project.created_at.desc()).all()
    results = []
    for p in projects:
        art_count = db.query(Artifact).filter(Artifact.project_id == p.project_id).count()
        req_count = db.query(Requirement).filter(Requirement.project_id == p.project_id).count()
        results.append(ProjectResponse(
            project_id=p.project_id,
            user_id=p.user_id,
            project_name=p.project_name,
            description=p.description,
            source_version=p.source_version,
            created_at=p.created_at,
            artifacts_count=art_count,
            requirements_count=req_count
        ))
    return results

@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = get_authorized_project(project_id, current_user, db)
    art_count = db.query(Artifact).filter(Artifact.project_id == project.project_id).count()
    req_count = db.query(Requirement).filter(Requirement.project_id == project.project_id).count()
    return ProjectResponse(
        project_id=project.project_id,
        user_id=project.user_id,
        project_name=project.project_name,
        description=project.description,
        source_version=project.source_version,
        created_at=project.created_at,
        artifacts_count=art_count,
        requirements_count=req_count
    )

@router.patch("/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, project_in: ProjectUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = get_authorized_project(project_id, current_user, db)
    if project_in.project_name is not None:
        project.project_name = project_in.project_name
    if project_in.description is not None:
        project.description = project_in.description
    if project_in.source_version is not None:
        project.source_version = project_in.source_version
    db.commit()
    db.refresh(project)
    art_count = db.query(Artifact).filter(Artifact.project_id == project.project_id).count()
    req_count = db.query(Requirement).filter(Requirement.project_id == project.project_id).count()
    return ProjectResponse(
        project_id=project.project_id,
        user_id=project.user_id,
        project_name=project.project_name,
        description=project.description,
        source_version=project.source_version,
        created_at=project.created_at,
        artifacts_count=art_count,
        requirements_count=req_count
    )

@router.delete("/{project_id}")
def delete_project(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = get_authorized_project(project_id, current_user, db)
    project_dir = os.path.join(settings.UPLOAD_DIR, f"project_{project_id}")
    if os.path.exists(project_dir):
        shutil.rmtree(project_dir, ignore_errors=True)
    db.delete(project)
    db.commit()
    return {"message": "Project and all associated artifacts deleted successfully."}

@router.post("/{project_id}/upload")
async def upload_project_zip(
    project_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = get_authorized_project(project_id, current_user, db)

    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip archives are supported.")

    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    temp_zip = os.path.join(settings.UPLOAD_DIR, f"upload_{project_id}_{file.filename}")

    try:
        with open(temp_zip, "wb") as f:
            content = await file.read()
            if len(content) > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
                raise HTTPException(status_code=400, detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB}MB")
            f.write(content)

        extract_dir, artifacts, summary = extract_and_scan_zip(temp_zip, project.project_id, db)
        return {
            "message": "Project uploaded and scanned successfully.",
            "summary": summary
        }
    finally:
        if os.path.exists(temp_zip):
            os.remove(temp_zip)

@router.get("/{project_id}/artifacts", response_model=List[ArtifactResponse])
def list_project_artifacts(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = get_authorized_project(project_id, current_user, db)
    artifacts = db.query(Artifact).filter(Artifact.project_id == project.project_id).all()
    return [ArtifactResponse.model_validate(a) for a in artifacts]

@router.get("/{project_id}/history", response_model=List[AnalysisRunResponse])
def get_project_history(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = get_authorized_project(project_id, current_user, db)
    runs = db.query(AnalysisRun).filter(AnalysisRun.project_id == project.project_id).order_by(AnalysisRun.started_at.desc()).all()
    results = []
    for r in runs:
        results.append(AnalysisRunResponse(
            analysis_run_id=r.analysis_run_id,
            project_id=r.project_id,
            source_version=r.source_version,
            status=r.status,
            started_at=r.started_at,
            completed_at=r.completed_at,
            total_claims=len(r.claim_results),
            fully_satisfied=len([cr for cr in r.claim_results if cr.status == "Fully Satisfied"]),
            partially_satisfied=len([cr for cr in r.claim_results if cr.status == "Partially Satisfied"]),
            missing=len([cr for cr in r.claim_results if cr.status == "Missing"]),
            contradictory=len([cr for cr in r.claim_results if cr.status == "Contradictory"]),
            unverifiable=len([cr for cr in r.claim_results if cr.status == "Unverifiable"]),
        ))
    return results
