from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models import Requirement, AtomicClaim, RequirementEdge
from app.schemas import RequirementGraphResponse, GraphNode, GraphEdge

def get_project_requirement_graph(project_id: int, db: Session) -> RequirementGraphResponse:
    requirements = db.query(Requirement).filter(Requirement.project_id == project_id).all()
    nodes: List[GraphNode] = []
    edges: List[GraphEdge] = []

    y_offset = 50

    for r_idx, req in enumerate(requirements):
        req_node_id = f"req-{req.requirement_id}"
        nodes.append(GraphNode(
            id=req_node_id,
            type="requirement",
            label=f"REQ-{req.requirement_id}: {req.requirement_text[:40]}...",
            data={
                "id": req.requirement_id,
                "text": req.requirement_text,
                "created_at": str(req.created_at)
            },
            position={"x": 50.0, "y": float(y_offset)}
        ))

        claim_y = y_offset
        for c_idx, claim in enumerate(req.claims):
            claim_node_id = f"claim-{claim.claim_id}"
            
            # Fetch latest result if available
            latest_status = "unverified"
            if claim.results:
                latest_status = claim.results[-1].status

            nodes.append(GraphNode(
                id=claim_node_id,
                type="claim",
                label=f"CLAIM-{claim.claim_id}: {claim.claim_text[:40]}...",
                data={
                    "id": claim.claim_id,
                    "requirement_id": req.requirement_id,
                    "text": claim.claim_text,
                    "expected_behavior": claim.expected_behavior,
                    "status": latest_status,
                    "artifact_types": claim.relevant_artifact_types
                },
                position={"x": 380.0, "y": float(claim_y)}
            ))

            # Edge: Requirement -> Atomic Claim
            edges.append(GraphEdge(
                id=f"edge-req-{req.requirement_id}-claim-{claim.claim_id}",
                source=req_node_id,
                target=claim_node_id,
                relationship_type="decomposed_into"
            ))

            claim_y += 110

        y_offset = max(y_offset + 140, claim_y + 40)

    # Fetch explicit claim-to-claim dependencies
    claim_ids = [c.claim_id for req in requirements for c in req.claims]
    if claim_ids:
        custom_edges = db.query(RequirementEdge).filter(RequirementEdge.source_claim_id.in_(claim_ids)).all()
        for e in custom_edges:
            edges.append(GraphEdge(
                id=f"edge-custom-{e.edge_id}",
                source=f"claim-{e.source_claim_id}",
                target=f"claim-{e.target_claim_id}",
                relationship_type=e.relationship_type
            ))

    return RequirementGraphResponse(
        project_id=project_id,
        nodes=nodes,
        edges=edges
    )
