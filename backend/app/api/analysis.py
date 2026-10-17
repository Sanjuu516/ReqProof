import os
import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.config import settings
from app.models import Project, User, Artifact, Requirement, AtomicClaim, AnalysisRun, EvidenceRecord, ClaimResult, TestExecution
from app.schemas import AnalysisRunResponse, ClaimResultResponse, EvidenceRecordResponse
from app.services.auth_service import get_current_user
from app.analyzers.java_analyzer import JavaStaticAnalyzer
from app.analyzers.ts_analyzer import TypeScriptFrontendAnalyzer
from app.analyzers.junit_analyzer import JUnitReportAnalyzer
from app.analyzers.api_analyzer import ApiRuntimeAnalyzer
from app.engine.fusion_engine import EvidenceFusionEngine
from app.services.report_service import generate_csv_report, generate_pdf_report

router = APIRouter(tags=["Analysis & Verification"])

def get_authorized_project(project_id: int, user: User, db: Session) -> Project:
    project = db.query(Project).filter(Project.project_id == project_id, Project.user_id == user.user_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found or unauthorized.")
    return project

@router.post("/projects/{project_id}/analysis-runs", response_model=AnalysisRunResponse)
def trigger_analysis_run(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    project = get_authorized_project(project_id, current_user, db)

    # 1. Initialize Run
    run = AnalysisRun(
        project_id=project.project_id,
        source_version=project.source_version or "v1.0.0",
        status="running",
        started_at=datetime.datetime.now(datetime.timezone.utc),
        configuration='{"analyzers": ["java", "typescript", "junit", "api"], "fusion_mode": "deterministic_v1"}'
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    project_dir = os.path.join(settings.UPLOAD_DIR, f"project_{project_id}")
    artifacts = db.query(Artifact).filter(Artifact.project_id == project_id).all()
    requirements = db.query(Requirement).filter(Requirement.project_id == project_id).all()
    all_claims = [c for r in requirements for c in r.claims]

    raw_evidence: List[Dict[str, Any]] = []

    # 2. Run Analyzers if artifacts exist
    if os.path.exists(project_dir) and artifacts and all_claims:
        java_analyzer = JavaStaticAnalyzer()
        ts_analyzer = TypeScriptFrontendAnalyzer()
        junit_analyzer = JUnitReportAnalyzer()
        api_analyzer = ApiRuntimeAnalyzer()

        # Static Java
        raw_evidence.extend(java_analyzer.analyze(project_dir, all_claims, artifacts))
        # Frontend TS/React
        raw_evidence.extend(ts_analyzer.analyze(project_dir, all_claims, artifacts))
        # JUnit Test Reports
        junit_ev, test_execs = junit_analyzer.analyze(project_dir, all_claims, artifacts)
        raw_evidence.extend(junit_ev)
        for te in test_execs:
            db_te = TestExecution(
                analysis_run_id=run.analysis_run_id,
                test_name=te["test_name"],
                execution_source=te["execution_source"],
                outcome=te["outcome"],
                duration_ms=te["duration_ms"],
                log_reference=te["log_reference"]
            )
            db.add(db_te)

        # API & Runtime
        raw_evidence.extend(api_analyzer.analyze(project_dir, all_claims, artifacts))

    # 3. Normalize & Persist Evidence Records
    stored_evidence = []
    for item in raw_evidence:
        ev = EvidenceRecord(
            analysis_run_id=run.analysis_run_id,
            claim_id=item["claim_id"],
            artifact_id=item.get("artifact_id"),
            evidence_type=item["evidence_type"],
            polarity=item["polarity"],
            observation=item["observation"],
            location_reference=item.get("location_reference"),
            provenance=item.get("provenance"),
            meta_info=str(item.get("meta_info", {}))
        )
        db.add(ev)
        stored_evidence.append(ev)

    db.commit()

    # 4. Run Evidence-Fusion Engine on each Claim
    fusion_engine = EvidenceFusionEngine()
    for claim in all_claims:
        claim_ev = [e for e in stored_evidence if e.claim_id == claim.claim_id]
        verdict = fusion_engine.evaluate_claim(claim, claim_ev, artifacts)

        cr = ClaimResult(
            analysis_run_id=run.analysis_run_id,
            claim_id=claim.claim_id,
            status=verdict["status"],
            reason_codes=verdict.get("reason_codes"),
            explanation=verdict["explanation"],
            sufficiency_state=verdict.get("sufficiency_state", "sufficient")
        )
        db.add(cr)

    run.status = "completed"
    run.completed_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()
    db.refresh(run)

    return AnalysisRunResponse(
        analysis_run_id=run.analysis_run_id,
        project_id=run.project_id,
        source_version=run.source_version,
        status=run.status,
        started_at=run.started_at,
        completed_at=run.completed_at,
        total_claims=len(run.claim_results),
        fully_satisfied=len([cr for cr in run.claim_results if cr.status == "Fully Satisfied"]),
        partially_satisfied=len([cr for cr in run.claim_results if cr.status == "Partially Satisfied"]),
        missing=len([cr for cr in run.claim_results if cr.status == "Missing"]),
        contradictory=len([cr for cr in run.claim_results if cr.status == "Contradictory"]),
        unverifiable=len([cr for cr in run.claim_results if cr.status == "Unverifiable"]),
    )

@router.get("/analysis-runs/{analysis_run_id}", response_model=AnalysisRunResponse)
def get_analysis_run(
    analysis_run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    run = db.query(AnalysisRun).filter(AnalysisRun.analysis_run_id == analysis_run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found.")
    get_authorized_project(run.project_id, current_user, db)

    return AnalysisRunResponse(
        analysis_run_id=run.analysis_run_id,
        project_id=run.project_id,
        source_version=run.source_version,
        status=run.status,
        started_at=run.started_at,
        completed_at=run.completed_at,
        total_claims=len(run.claim_results),
        fully_satisfied=len([cr for cr in run.claim_results if cr.status == "Fully Satisfied"]),
        partially_satisfied=len([cr for cr in run.claim_results if cr.status == "Partially Satisfied"]),
        missing=len([cr for cr in run.claim_results if cr.status == "Missing"]),
        contradictory=len([cr for cr in run.claim_results if cr.status == "Contradictory"]),
        unverifiable=len([cr for cr in run.claim_results if cr.status == "Unverifiable"]),
    )

@router.get("/analysis-runs/{analysis_run_id}/results", response_model=List[ClaimResultResponse])
def get_analysis_results(
    analysis_run_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    run = db.query(AnalysisRun).filter(AnalysisRun.analysis_run_id == analysis_run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found.")
    get_authorized_project(run.project_id, current_user, db)

    results = db.query(ClaimResult).filter(ClaimResult.analysis_run_id == analysis_run_id).all()
    output = []
    for r in results:
        ev_records = db.query(EvidenceRecord).filter(
            EvidenceRecord.analysis_run_id == analysis_run_id,
            EvidenceRecord.claim_id == r.claim_id
        ).all()
        output.append(ClaimResultResponse(
            result_id=r.result_id,
            analysis_run_id=r.analysis_run_id,
            claim_id=r.claim_id,
            claim_text=r.claim.claim_text if r.claim else "",
            status=r.status,
            reason_codes=r.reason_codes,
            explanation=r.explanation,
            sufficiency_state=r.sufficiency_state,
            evidence_records=[EvidenceRecordResponse.model_validate(e) for e in ev_records],
            created_at=r.created_at
        ))
    return output

@router.get("/claims/{claim_id}/evidence", response_model=List[EvidenceRecordResponse])
def get_claim_evidence(
    claim_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    claim = db.query(AtomicClaim).filter(AtomicClaim.claim_id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found.")
    get_authorized_project(claim.requirement.project_id, current_user, db)

    records = db.query(EvidenceRecord).filter(EvidenceRecord.claim_id == claim_id).order_by(EvidenceRecord.created_at.desc()).all()
    return [EvidenceRecordResponse.model_validate(e) for e in records]

@router.get("/reports/{analysis_run_id}/download")
def download_report(
    analysis_run_id: int,
    format: str = "pdf",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    run = db.query(AnalysisRun).filter(AnalysisRun.analysis_run_id == analysis_run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Analysis run not found.")
    get_authorized_project(run.project_id, current_user, db)

    if format.lower() == "csv":
        csv_data = generate_csv_report(analysis_run_id, db)
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=reqproof_run_{analysis_run_id}.csv"}
        )
    else:
        pdf_data = generate_pdf_report(analysis_run_id, db)
        return Response(
            content=pdf_data,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=reqproof_run_{analysis_run_id}.pdf"}
        )
