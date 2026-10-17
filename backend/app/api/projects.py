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

@router.post("/{project_id}/load-demo")
def load_demo_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = get_authorized_project(project_id, current_user, db)
    demo_zip = os.path.join(settings.BASE_DIR, "samples/sample-spring-react-app.zip")
    if not os.path.exists(demo_zip):
        raise HTTPException(status_code=404, detail="Demo project archive not found on server.")

    # 1. Extract and scan artifacts
    extract_dir, artifacts, summary = extract_and_scan_zip(demo_zip, project.project_id, db)

    # 2. Automatically seed ground truth requirements if not present
    from app.models import AtomicClaim
    from app.services.gemini_service import decompose_requirement_with_gemini

    sample_reqs = [
        "The system must reject expired authentication tokens and validate JWT signature.",
        "The user login form must validate password length before submission.",
        "The system shall support WebAuthn biometric hardware authentication."
    ]

    for req_text in sample_reqs:
        existing = db.query(Requirement).filter(
            Requirement.project_id == project.project_id,
            Requirement.requirement_text == req_text
        ).first()
        if not existing:
            req = Requirement(project_id=project.project_id, requirement_text=req_text)
            db.add(req)
            db.commit()
            db.refresh(req)

            decomposed = decompose_requirement_with_gemini(req_text)
            for item in decomposed:
                claim = AtomicClaim(
                    requirement_id=req.requirement_id,
                    claim_text=item.get("claim_text", req_text),
                    expected_behavior=item.get("expected_behavior", ""),
                    verification_criteria=item.get("verification_criteria", ""),
                    relevant_artifact_types=item.get("relevant_artifact_types", "source,api,test"),
                    review_status="reviewed"
                )
                db.add(claim)
            db.commit()

    return {
        "message": "Demo benchmark application and sample requirements loaded successfully!",
        "summary": summary,
        "requirements_loaded": len(sample_reqs)
    }

@router.post("/{project_id}/upload-folder")
async def upload_folder_files(
    project_id: int,
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Accepts files selected from a directory via HTML5 webkitdirectory.
    """
    project = get_authorized_project(project_id, current_user, db)
    extract_dir = os.path.join(settings.UPLOAD_DIR, f"project_{project_id}")
    os.makedirs(extract_dir, exist_ok=True)

    for file in files:
        # File filename may contain relative path if transmitted by browser
        filename = file.filename or "file.txt"
        safe_rel_path = filename.replace("\\", "/").lstrip("/")
        dest_path = os.path.join(extract_dir, safe_rel_path)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        content = await file.read()
        with open(dest_path, "wb") as f:
            f.write(content)

    # Re-scan repository
    from app.services.zip_service import calculate_file_hash, IGNORED_DIRS, LANGUAGE_EXTENSIONS
    db.query(Artifact).filter(Artifact.project_id == project_id).delete()

    artifacts = []
    manifests = []
    languages_detected = set()

    for root, dirs, f_list in os.walk(extract_dir):
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith('.')]
        for fname in f_list:
            if fname.startswith('.'):
                continue
            full_path = os.path.join(root, fname)
            rel_path = os.path.relpath(full_path, extract_dir)
            _, ext = os.path.splitext(fname)
            ext = ext.lower()

            artifact_type = "other"
            language = LANGUAGE_EXTENSIONS.get(ext)
            if language:
                languages_detected.add(language)

            if fname in {"pom.xml", "package.json", "build.gradle", "application.properties"}:
                artifact_type = "config"
                manifests.append(rel_path)
            elif "test" in rel_path.lower() or fname.endswith("Test.java") or fname.endswith(".test.ts"):
                artifact_type = "test"
            elif ext in {".tsx", ".jsx", ".html", ".css"}:
                artifact_type = "ui"
            elif ext in {".java", ".ts", ".js", ".py"}:
                artifact_type = "source"
            elif ext == ".xml" and ("test" in rel_path.lower() or "surefire" in rel_path.lower()):
                artifact_type = "test_report"

            art = Artifact(
                project_id=project_id,
                artifact_path=rel_path,
                artifact_type=artifact_type,
                language=language,
                content_hash=calculate_file_hash(full_path),
                analysis_status="processed"
            )
            db.add(art)
            artifacts.append(art)

    db.commit()
    return {
        "message": f"Successfully uploaded and scanned {len(artifacts)} files from folder.",
        "summary": {
            "total_files": len(artifacts),
            "languages": list(languages_detected),
            "manifests": manifests
        }
    }

@router.get("/{project_id}/artifacts", response_model=List[ArtifactResponse])
def list_project_artifacts(project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = get_authorized_project(project_id, current_user, db)
    artifacts = db.query(Artifact).filter(Artifact.project_id == project.project_id).all()
    return [ArtifactResponse.model_validate(a) for a in artifacts]

@router.get("/{project_id}/artifacts/{artifact_id}/content")
def get_artifact_content(
    project_id: int,
    artifact_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = get_authorized_project(project_id, current_user, db)
    artifact = db.query(Artifact).filter(Artifact.artifact_id == artifact_id, Artifact.project_id == project.project_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found.")

    extract_dir = os.path.join(settings.UPLOAD_DIR, f"project_{project_id}")
    full_path = os.path.join(extract_dir, artifact.artifact_path)

    if not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="Artifact file does not exist on disk.")

    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

    return {
        "artifact_id": artifact.artifact_id,
        "artifact_path": artifact.artifact_path,
        "language": artifact.language,
        "artifact_type": artifact.artifact_type,
        "content": content
    }

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
