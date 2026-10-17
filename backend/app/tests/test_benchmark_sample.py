import unittest
import os
from app.database import SessionLocal, Base, engine
from app.models import User
from app.schemas import UserRegister, ProjectCreate, RequirementCreate
from app.api.auth import register
from app.api.projects import create_project
from app.api.requirements import create_requirement
from app.api.analysis import trigger_analysis_run, get_analysis_results
from app.services.zip_service import extract_and_scan_zip

class TestSampleBenchmark(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_sample_benchmark_verification(self):
        # 1. Register
        user_in = UserRegister(
            name="Benchmarker",
            email=f"bench_{id(self)}@reqproof.org",
            password="Password123!"
        )
        auth_resp = register(user_in, self.db)
        user = self.db.query(User).filter(User.user_id == auth_resp.user.user_id).first()

        # 2. Create Project
        proj_in = ProjectCreate(
            project_name="Benchmark Spring & React App",
            description="Testing ground truth multi-artifact evaluation",
            source_version="v1.0"
        )
        proj = create_project(proj_in, user, self.db)

        # 3. Extract and scan the sample zip
        from app.config import settings
        zip_path = os.path.join(settings.BASE_DIR, "samples/sample-spring-react-app.zip")
        self.assertTrue(os.path.exists(zip_path), f"Zip path {zip_path} not found")
        extract_dir, artifacts, summary = extract_and_scan_zip(zip_path, proj.project_id, self.db)
        self.assertGreater(summary["total_files"], 0)

        # 4. Add Requirement 1: Token expiration
        req1 = create_requirement(proj.project_id, RequirementCreate(
            requirement_text="The system must reject expired authentication tokens and validate JWT signature."
        ), user, self.db)

        # 5. Add Requirement 2: Password validation
        req2 = create_requirement(proj.project_id, RequirementCreate(
            requirement_text="The user login form must validate password length before submission."
        ), user, self.db)

        # 6. Add Requirement 3: Biometrics (not implemented)
        req3 = create_requirement(proj.project_id, RequirementCreate(
            requirement_text="The system shall support WebAuthn biometric hardware authentication."
        ), user, self.db)

        # 7. Execute Multi-Artifact Analysis
        run = trigger_analysis_run(proj.project_id, user, self.db)
        self.assertEqual(run.status, "completed")

        # 8. Retrieve results
        results = get_analysis_results(run.analysis_run_id, user, self.db)
        self.assertGreaterEqual(len(results), 3)

        status_by_claim = {r.claim_text.lower(): r.status for r in results}

        # Check that contradiction was caught for expired tokens!
        token_statuses = [r.status for r in results if "expired" in r.claim_text.lower() or "token" in r.claim_text.lower()]
        self.assertTrue(any(s == "Contradictory" for s in token_statuses), f"Expected Contradictory in {token_statuses}")

        # Check that biometrics is Unverifiable or Missing due to no evidence
        bio_statuses = [r.status for r in results if "biometric" in r.claim_text.lower() or "webauthn" in r.claim_text.lower()]
        self.assertTrue(any(s in ["Unverifiable", "Missing"] for s in bio_statuses), f"Expected Unverifiable/Missing in {bio_statuses}")

if __name__ == "__main__":
    unittest.main()
