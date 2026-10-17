from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Requirement, AtomicClaim, Project, User, RequirementEdge
from app.schemas import (
    RequirementCreate, RequirementResponse, AtomicClaimCreate,
    AtomicClaimUpdate, AtomicClaimResponse, RequirementGraphResponse
)
from app.services.auth_service import get_current_user
from app.services.gemini_service import decompose_requirement_with_gemini
from app.services.graph_service import get_project_requirement_graph

router = APIRouter(tags=["Requirements & Claims"])

def get_authorized_project(project_id: int, user: User, db: Session) -> Project:
    project = db.query(Project).filter(Project.project_id == project_id, Project.user_id == user.user_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or unauthorized.")
    return project

@router.post("/projects/{project_id}/requirements", response_model=RequirementResponse)
def create_requirement(
    project_id: int,
    req_in: RequirementCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = get_authorized_project(project_id, current_user, db)

    req = Requirement(
        project_id=project.project_id,
        requirement_text=req_in.requirement_text
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    # Automatically trigger decomposition proposal
    decomposed = decompose_requirement_with_gemini(req.requirement_text)
    claim_objects = []
    for item in decomposed:
        claim = AtomicClaim(
            requirement_id=req.requirement_id,
            claim_text=item.get("claim_text", req.requirement_text),
            expected_behavior=item.get("expected_behavior", ""),
            verification_criteria=item.get("verification_criteria", ""),
            relevant_artifact_types=item.get("relevant_artifact_types", "source,api,test"),
            review_status="reviewed"
        )
        db.add(claim)
        claim_objects.append(claim)

    db.commit()
    db.refresh(req)
    return req

@router.get("/projects/{project_id}/requirements", response_model=List[RequirementResponse])
def list_requirements(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = get_authorized_project(project_id, current_user, db)
    return db.query(Requirement).filter(Requirement.project_id == project.project_id).all()

@router.post("/requirements/{requirement_id}/decompose", response_model=List[AtomicClaimResponse])
def trigger_decomposition(
    requirement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    req = db.query(Requirement).filter(Requirement.requirement_id == requirement_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found.")
    get_authorized_project(req.project_id, current_user, db)

    # Clear previous claims and re-run decomposition
    db.query(AtomicClaim).filter(AtomicClaim.requirement_id == requirement_id).delete()

    decomposed = decompose_requirement_with_gemini(req.requirement_text)
    claims = []
    for item in decomposed:
        claim = AtomicClaim(
            requirement_id=req.requirement_id,
            claim_text=item.get("claim_text", req.requirement_text),
            expected_behavior=item.get("expected_behavior", ""),
            verification_criteria=item.get("verification_criteria", ""),
            relevant_artifact_types=item.get("relevant_artifact_types", "source,api,test"),
            review_status="reviewed"
        )
        db.add(claim)
        claims.append(claim)

    db.commit()
    for c in claims:
        db.refresh(c)
    return claims

@router.get("/requirements/{requirement_id}/claims", response_model=List[AtomicClaimResponse])
def get_claims(
    requirement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    req = db.query(Requirement).filter(Requirement.requirement_id == requirement_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found.")
    get_authorized_project(req.project_id, current_user, db)
    return db.query(AtomicClaim).filter(AtomicClaim.requirement_id == requirement_id).all()

@router.patch("/claims/{claim_id}", response_model=AtomicClaimResponse)
def update_claim(
    claim_id: int,
    claim_in: AtomicClaimUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    claim = db.query(AtomicClaim).filter(AtomicClaim.claim_id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found.")
    get_authorized_project(claim.requirement.project_id, current_user, db)

    if claim_in.claim_text is not None:
        claim.claim_text = claim_in.claim_text
    if claim_in.expected_behavior is not None:
        claim.expected_behavior = claim_in.expected_behavior
    if claim_in.verification_criteria is not None:
        claim.verification_criteria = claim_in.verification_criteria
    if claim_in.relevant_artifact_types is not None:
        claim.relevant_artifact_types = claim_in.relevant_artifact_types
    if claim_in.review_status is not None:
        claim.review_status = claim_in.review_status

    db.commit()
    db.refresh(claim)
    return claim

@router.get("/projects/{project_id}/graph", response_model=RequirementGraphResponse)
def get_graph(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = get_authorized_project(project_id, current_user, db)
    return get_project_requirement_graph(project.project_id, db)
