import os
import io
import csv
import datetime
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models import AnalysisRun, Project, ClaimResult, AtomicClaim, EvidenceRecord

def generate_csv_report(analysis_run_id: int, db: Session) -> str:
    run = db.query(AnalysisRun).filter(AnalysisRun.analysis_run_id == analysis_run_id).first()
    if not run:
        raise ValueError("Analysis run not found")

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "Claim ID", "Requirement ID", "Claim Statement", "Expected Behavior",
        "Verification Status", "Sufficiency", "Reason Codes", "Explanation", "Evidence Locations"
    ])

    results = db.query(ClaimResult).filter(ClaimResult.analysis_run_id == analysis_run_id).all()
    for res in results:
        claim = res.claim
        # Fetch evidence locations
        ev_records = db.query(EvidenceRecord).filter(
            EvidenceRecord.analysis_run_id == analysis_run_id,
            EvidenceRecord.claim_id == claim.claim_id
        ).all()
        locations = "; ".join([e.location_reference or e.evidence_type for e in ev_records if e.location_reference])

        writer.writerow([
            claim.claim_id,
            claim.requirement_id,
            claim.claim_text,
            claim.expected_behavior or "",
            res.status,
            res.sufficiency_state,
            res.reason_codes or "",
            res.explanation,
            locations
        ])

    return output.getvalue()


def generate_pdf_report(analysis_run_id: int, db: Session) -> bytes:
    run = db.query(AnalysisRun).filter(AnalysisRun.analysis_run_id == analysis_run_id).first()
    if not run:
        raise ValueError("Analysis run not found")

    project = run.project
    results = db.query(ClaimResult).filter(ClaimResult.analysis_run_id == analysis_run_id).all()

    # Calculate statistics
    total = len(results)
    counts = {
        "Fully Satisfied": len([r for r in results if r.status == "Fully Satisfied"]),
        "Partially Satisfied": len([r for r in results if r.status == "Partially Satisfied"]),
        "Missing": len([r for r in results if r.status == "Missing"]),
        "Contradictory": len([r for r in results if r.status == "Contradictory"]),
        "Unverifiable": len([r for r in results if r.status == "Unverifiable"]),
    }

    # Attempt to use ReportLab if available
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            name="TitleStyle",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#1e293b")
        )
        story.append(Paragraph("ReqProof: Multi-Artifact Verification Report", title_style))
        story.append(Spacer(1, 10))

        # Project Metadata
        meta_text = (
            f"<b>Project:</b> {project.project_name} | "
            f"<b>Source Version:</b> {run.source_version or 'v1.0.0'} | "
            f"<b>Analysis Run:</b> #{run.analysis_run_id} | "
            f"<b>Generated:</b> {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"
        )
        story.append(Paragraph(meta_text, styles["Normal"]))
        story.append(Spacer(1, 15))

        # Status Summary Table
        summary_data = [
            ["Status Category", "Count", "Percentage"],
            ["Fully Satisfied", str(counts["Fully Satisfied"]), f"{(counts['Fully Satisfied']/total*100) if total else 0:.1f}%"],
            ["Partially Satisfied", str(counts["Partially Satisfied"]), f"{(counts['Partially Satisfied']/total*100) if total else 0:.1f}%"],
            ["Missing", str(counts["Missing"]), f"{(counts['Missing']/total*100) if total else 0:.1f}%"],
            ["Contradictory", str(counts["Contradictory"]), f"{(counts['Contradictory']/total*100) if total else 0:.1f}%"],
            ["Unverifiable", str(counts["Unverifiable"]), f"{(counts['Unverifiable']/total*100) if total else 0:.1f}%"],
            ["Total Evaluated Claims", str(total), "100.0%"]
        ]
        t = Table(summary_data, colWidths=[200, 100, 100])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#0f172a")),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ]))
        story.append(t)
        story.append(Spacer(1, 20))

        # Claim Details
        story.append(Paragraph("<b>Detailed Claim Evaluations & Traceability</b>", styles["Heading2"]))
        story.append(Spacer(1, 10))

        for res in results:
            c = res.claim
            status_color = "#10b981" if res.status == "Fully Satisfied" else "#ef4444" if res.status in ["Contradictory", "Missing"] else "#f59e0b"
            item_html = (
                f"<b>Claim #{c.claim_id}:</b> {c.claim_text}<br/>"
                f"<font color='{status_color}'><b>Status: {res.status}</b></font> ({res.sufficiency_state})<br/>"
                f"<b>Explanation:</b> {res.explanation}"
            )
            story.append(Paragraph(item_html, styles["Normal"]))
            story.append(Spacer(1, 10))

        doc.build(story)
        return buffer.getvalue()

    except ImportError:
        # Fallback formatted plain text report if ReportLab binary is absent in runtime environment
        buffer = io.BytesIO()
        text = f"============================================================\n"
        text += f"REQPROOF MULTI-ARTIFACT REQUIREMENT VERIFICATION REPORT\n"
        text += f"============================================================\n\n"
        text += f"Project: {project.project_name}\n"
        text += f"Source Version: {run.source_version or 'v1.0.0'}\n"
        text += f"Run ID: #{run.analysis_run_id}\n"
        text += f"Generated: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n"
        text += f"--- SUMMARY METRICS ---\n"
        text += f"Total Claims: {total}\n"
        for k, v in counts.items():
            pct = (v / total * 100) if total else 0
            text += f"- {k}: {v} ({pct:.1f}%)\n"
        text += f"\n--- DETAILED CLAIM RESULTS ---\n\n"
        for res in results:
            text += f"Claim #{res.claim_id}: {res.claim.claim_text}\n"
            text += f"Status: {res.status} (Sufficiency: {res.sufficiency_state})\n"
            text += f"Explanation: {res.explanation}\n"
            text += f"-" * 60 + "\n"

        buffer.write(text.encode('utf-8'))
        return buffer.getvalue()
