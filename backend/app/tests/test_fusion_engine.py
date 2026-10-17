import unittest
import json
from app.engine.fusion_engine import EvidenceFusionEngine
from app.models import AtomicClaim, EvidenceRecord

class TestEvidenceFusionEngine(unittest.TestCase):
    def setUp(self):
        self.engine = EvidenceFusionEngine()

    def test_contradiction_detection(self):
        claim = AtomicClaim(
            claim_id=1,
            requirement_id=1,
            claim_text="The system must reject expired authentication tokens.",
            expected_behavior="Return 401 Unauthorized for expired JWT.",
            relevant_artifact_types="source,api,test"
        )

        ev1 = EvidenceRecord(
            evidence_id=1,
            analysis_run_id=1,
            claim_id=1,
            evidence_type="static",
            polarity="supporting",
            observation="Found token validation rejection logic: if (token.isExpired()) throw Unauthorized",
            location_reference="src/auth/JwtValidator.java#L45",
            provenance="JavaStaticAnalyzer-v1.0"
        )
        ev2 = EvidenceRecord(
            evidence_id=2,
            analysis_run_id=1,
            claim_id=1,
            evidence_type="api",
            polarity="contradicting",
            observation="API security configuration permits requests without enforcing token validation (permitAll found).",
            location_reference="src/config/SecurityConfig.java#L22",
            provenance="ApiRuntimeAnalyzer-v1.0"
        )

        result = self.engine.evaluate_claim(claim, [ev1, ev2], [])
        self.assertEqual(result["status"], "Contradictory")
        self.assertIn("Contradiction detected", result["explanation"])
        self.assertIn("MATERIAL_ARTIFACT_CONFLICT", json.loads(result["reason_codes"]))

    def test_fully_satisfied(self):
        claim = AtomicClaim(
            claim_id=2,
            requirement_id=1,
            claim_text="User registration must validate password length.",
            expected_behavior="Reject passwords shorter than 8 characters.",
            relevant_artifact_types="source,ui"
        )

        ev1 = EvidenceRecord(
            evidence_id=3,
            analysis_run_id=1,
            claim_id=2,
            evidence_type="source",
            polarity="supporting",
            observation="Backend validates password length >= 8.",
            location_reference="src/service/UserService.java#L60",
            provenance="JavaStaticAnalyzer-v1.0"
        )
        ev2 = EvidenceRecord(
            evidence_id=4,
            analysis_run_id=1,
            claim_id=2,
            evidence_type="ui",
            polarity="supporting",
            observation="UI form enforces minLength=8 on password input.",
            location_reference="frontend/src/Register.tsx#L35",
            provenance="TSFrontendAnalyzer-v1.0"
        )

        result = self.engine.evaluate_claim(claim, [ev1, ev2], [])
        self.assertEqual(result["status"], "Fully Satisfied")

    def test_unverifiable_on_no_evidence(self):
        claim = AtomicClaim(
            claim_id=3,
            requirement_id=1,
            claim_text="System must support OAuth2 single sign-on with GitHub.",
            expected_behavior="Authenticate via GitHub OAuth.",
            relevant_artifact_types="source,api"
        )

        result = self.engine.evaluate_claim(claim, [], [])
        self.assertEqual(result["status"], "Unverifiable")
        self.assertEqual(result["sufficiency_state"], "insufficient")

if __name__ == "__main__":
    unittest.main()
