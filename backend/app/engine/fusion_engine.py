import json
from typing import List, Dict, Any, Tuple
from app.models import AtomicClaim, EvidenceRecord, ClaimResult

class EvidenceFusionEngine:
    def __init__(self):
        self.name = "DeterministicEvidenceFusionEngine-v1.0"

    def evaluate_claim(self, claim: AtomicClaim, evidence_records: List[EvidenceRecord], all_artifacts: List[Any]) -> Dict[str, Any]:
        """
        Applies the 8-step evidence-fusion algorithm described in Section 11 of the proposal:
        1. Evidence Collection
        2. Provenance Validation
        3. Evidence Categorization
        4. Sufficiency Evaluation
        5. Contradiction Analysis
        6. Decision-Rule Application
        7. Explanation Generation
        8. Return persistence-ready structure
        """
        # Step 2: Provenance validation
        valid_evidence = [e for e in evidence_records if e.claim_id == claim.claim_id and e.provenance]

        # If no evidence collected at all
        if not valid_evidence:
            return {
                "status": "Unverifiable",
                "sufficiency_state": "insufficient",
                "reason_codes": json.dumps(["NO_EVIDENCE_FOUND"]),
                "explanation": "No relevant evidence records could be collected across the provided project artifacts. Check whether supported languages or artifacts exist."
            }

        # Step 3: Evidence Categorization
        supporting = [e for e in valid_evidence if e.polarity == "supporting"]
        contradicting = [e for e in valid_evidence if e.polarity == "contradicting"]
        inconclusive = [e for e in valid_evidence if e.polarity == "inconclusive"]

        # Artifact type diversity
        artifact_types_covered = {e.evidence_type for e in valid_evidence}
        required_types = set((claim.relevant_artifact_types or "source,api,test").split(","))
        required_types = {t.strip() for t in required_types if t.strip()}

        # Step 4: Sufficiency Evaluation
        # Evidence sufficiency depends on whether key expected artifact types yielded observations
        overlap = artifact_types_covered.intersection(required_types)
        is_sufficient = len(overlap) >= min(2, len(required_types)) or len(supporting) >= 2 or len(contradicting) >= 1

        # Step 5: Contradiction Analysis
        # Conflict between static code presence and runtime/test failure, or explicit contradicting polarity
        has_static_support = any(e.evidence_type == "static" and e.polarity == "supporting" for e in valid_evidence)
        has_runtime_or_test_failure = any(e.evidence_type in {"api", "test", "runtime"} and e.polarity == "contradicting" for e in valid_evidence)
        
        has_conflict = len(contradicting) > 0 and len(supporting) > 0
        is_material_contradiction = (has_static_support and has_runtime_or_test_failure) or (len(contradicting) > 0 and len(supporting) > 0)

        # Step 6: Decision-Rule Application
        reasons = []

        # Rule 1: Contradictory
        if is_material_contradiction:
            status = "Contradictory"
            sufficiency_state = "sufficient"
            reasons.append("MATERIAL_ARTIFACT_CONFLICT")
            
            support_locs = ", ".join([e.location_reference or e.evidence_type for e in supporting[:2]])
            contra_locs = ", ".join([e.location_reference or e.evidence_type for e in contradicting[:2]])
            
            explanation = (
                f"Contradiction detected: Static source evidence ({support_locs}) suggests implementation is present, "
                f"but runtime or test verification ({contra_locs}) demonstrated non-compliance or failure. "
                f"Observed conflict: {contradicting[0].observation}"
            )
            return {
                "status": status,
                "sufficiency_state": sufficiency_state,
                "reason_codes": json.dumps(reasons),
                "explanation": explanation
            }

        # Rule 2: Explicit failure / missing with sufficient repository inspection
        if len(contradicting) > 0 and len(supporting) == 0:
            status = "Missing"
            sufficiency_state = "sufficient"
            reasons.append("EXPLICIT_BEHAVIORAL_FAILURE")
            explanation = (
                f"Requirement implementation is missing or non-functional. Verification identified: "
                f"{contradicting[0].observation} (Location: {contradicting[0].location_reference or 'Project Config'})."
            )
            return {
                "status": status,
                "sufficiency_state": sufficiency_state,
                "reason_codes": json.dumps(reasons),
                "explanation": explanation
            }

        # Rule 3: Partially Satisfied
        # E.g., UI or source found, but required API or test artifact was absent or only 1 of multiple conditions held
        if len(supporting) > 0 and len(overlap) < len(required_types) and len(required_types) > 1:
            status = "Partially Satisfied"
            sufficiency_state = "sufficient"
            reasons.append("PARTIAL_ARTIFACT_COVERAGE")
            covered_str = ", ".join(artifact_types_covered)
            missing_types_str = ", ".join(required_types - artifact_types_covered)
            explanation = (
                f"Requirement is partially satisfied. Implementation evidence was detected in {covered_str} "
                f"({supporting[0].location_reference or 'artifacts'}), but required verification evidence for "
                f"[{missing_types_str}] was not established or verified."
            )
            return {
                "status": status,
                "sufficiency_state": sufficiency_state,
                "reason_codes": json.dumps(reasons),
                "explanation": explanation
            }

        # Rule 4: Insufficient Evidence -> Unverifiable
        if not is_sufficient:
            status = "Unverifiable"
            sufficiency_state = "insufficient"
            reasons.append("INSUFFICIENT_EVIDENCE")
            explanation = (
                f"Available evidence is insufficient to verify claim. Only inconclusive or sparse observations "
                f"were recorded ({len(inconclusive)} inconclusive items). The system refuses to mark as missing without defensible proof."
            )
            return {
                "status": status,
                "sufficiency_state": sufficiency_state,
                "reason_codes": json.dumps(reasons),
                "explanation": explanation
            }

        # Rule 5: Fully Satisfied
        if len(supporting) > 0 and len(contradicting) == 0:
            status = "Fully Satisfied"
            sufficiency_state = "sufficient"
            reasons.append("SUPPORTED_BY_ALL_EVALUATED_ARTIFACTS")
            evidence_summaries = "; ".join([f"{e.evidence_type.upper()}: {e.observation}" for e in supporting[:3]])
            explanation = (
                f"Sufficient corroborating evidence confirms expected behavior across artifacts ({', '.join(artifact_types_covered)}). "
                f"No material contradictions were identified. Supporting evidence: {evidence_summaries}."
            )
            return {
                "status": status,
                "sufficiency_state": sufficiency_state,
                "reason_codes": json.dumps(reasons),
                "explanation": explanation
            }

        # Default fallback to Unverifiable
        return {
            "status": "Unverifiable",
            "sufficiency_state": "insufficient",
            "reason_codes": json.dumps(["AMBIGUOUS_EVIDENCE_STATE"]),
            "explanation": "Evidence state did not satisfy any explicit decision predicate with high confidence."
        }
