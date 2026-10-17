import unittest
from app.database import SessionLocal, Base, engine
from app.models import User
from app.schemas import UserRegister, ProjectCreate, RequirementCreate
from app.api.auth import register, get_me
from app.api.projects import create_project, list_projects
from app.api.requirements import create_requirement, get_graph
from app.api.analysis import trigger_analysis_run, get_analysis_results, download_report

class TestDirectAPI(unittest.TestCase):
    def setUp(self):
        Base.metadata.create_all(bind=engine)
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_full_pipeline_flow(self):
        # 1. Register user
        user_in = UserRegister(
            name="Alice Auditor",
            email=f"alice_{id(self)}@reqproof.org",
            password="SecurePassword2026!"
        )
        auth_resp = register(user_in, self.db)
        self.assertIsNotNone(auth_resp.access_token)
        user = self.db.query(User).filter(User.user_id == auth_resp.user.user_id).first()

        # 2. Verify me
        me = get_me(user)
        self.assertEqual(me.email, user_in.email)

        # 3. Create Project
        proj_in = ProjectCreate(
            project_name="ReqProof Spring Auth Benchmark",
            description="Benchmark testing multi-artifact contradiction detection",
            source_version="v2.1"
        )
        proj = create_project(proj_in, user, self.db)
        self.assertEqual(proj.project_name, proj_in.project_name)

        # 4. Create Requirement with Decomposition
        req_in = RequirementCreate(
            requirement_text="The system must reject expired tokens. The user interface shall display an unauthorized banner."
        )
        req = create_requirement(proj.project_id, req_in, user, self.db)
        self.assertEqual(len(req.claims), 2)
        self.assertTrue("reject expired tokens" in req.claims[0].claim_text.lower())

        # 5. Requirement Graph
        graph = get_graph(proj.project_id, user, self.db)
        self.assertGreater(len(graph.nodes), 0)
        self.assertGreater(len(graph.edges), 0)

        # 6. Trigger Analysis Run
        run = trigger_analysis_run(proj.project_id, user, self.db)
        self.assertEqual(run.status, "completed")
        self.assertEqual(run.total_claims, 2)

        # 7. Results
        results = get_analysis_results(run.analysis_run_id, user, self.db)
        self.assertEqual(len(results), 2)
        for r in results:
            self.assertIn(r.status, ["Fully Satisfied", "Partially Satisfied", "Missing", "Contradictory", "Unverifiable"])
            self.assertTrue(len(r.explanation) > 0)

        # 8. Report Generation
        csv_resp = download_report(run.analysis_run_id, format="csv", current_user=user, db=self.db)
        self.assertIn(b"Claim ID", csv_resp.body)

        pdf_resp = download_report(run.analysis_run_id, format="pdf", current_user=user, db=self.db)
        self.assertGreater(len(pdf_resp.body), 50)

        # 9. Database & System Transparency Test
        from app.api.system import get_database_overview, get_gemini_status
        db_overview = get_database_overview(current_user=user, db=self.db)
        self.assertEqual(db_overview["tables"]["users"] >= 1, True)
        self.assertIn("registered_users", db_overview)

        gemini_status = get_gemini_status(current_user=user)
        self.assertIn("configured", gemini_status)

        # 10. Load Demo Benchmark Project Test
        from app.api.projects import load_demo_project
        demo_resp = load_demo_project(proj.project_id, current_user=user, db=self.db)
        self.assertIn("summary", demo_resp)
        self.assertGreater(demo_resp["summary"]["total_files"], 0)

if __name__ == "__main__":
    unittest.main()
