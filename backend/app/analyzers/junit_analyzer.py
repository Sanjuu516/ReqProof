import os
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Tuple
from app.analyzers.base import BaseAnalyzer

class JUnitReportAnalyzer(BaseAnalyzer):
    def __init__(self):
        self.name = "JUnitReportAnalyzer-v1.0"

    def analyze(self, project_dir: str, claims: List[Any], artifacts: List[Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Parses JUnit XML reports to extract test execution records and map them
        as supporting, contradicting, or inconclusive evidence to claims.
        """
        observations = []
        test_executions = []

        report_artifacts = [a for a in artifacts if a.artifact_type == "test_report" or (a.artifact_path.endswith(".xml") and ("test" in a.artifact_path.lower() or "surefire" in a.artifact_path.lower()))]

        for art in report_artifacts:
            full_path = os.path.join(project_dir, art.artifact_path)
            if not os.path.isfile(full_path):
                continue

            try:
                tree = ET.parse(full_path)
                root = tree.getroot()
            except Exception:
                continue

            # Handle both <testsuite> and <testsuites>
            suites = [root] if root.tag == "testsuite" else root.findall(".//testsuite")
            if not suites and root.tag == "testsuites":
                suites = list(root)

            for suite in suites:
                for testcase in suite.findall("testcase"):
                    test_name = testcase.get("name", "unknown_test")
                    classname = testcase.get("classname", "")
                    duration = float(testcase.get("time", 0.0)) * 1000 # ms

                    failure = testcase.find("failure")
                    error = testcase.find("error")
                    skipped = testcase.find("skipped")

                    if failure is not None:
                        outcome = "failed"
                        detail = failure.get("message") or (failure.text or "").strip()[:200]
                    elif error is not None:
                        outcome = "errored"
                        detail = error.get("message") or (error.text or "").strip()[:200]
                    elif skipped is not None:
                        outcome = "skipped"
                        detail = skipped.get("message") or "Test skipped"
                    else:
                        outcome = "passed"
                        detail = "Test executed successfully"

                    test_executions.append({
                        "test_name": f"{classname}.{test_name}" if classname else test_name,
                        "outcome": outcome,
                        "duration_ms": duration,
                        "log_reference": f"{art.artifact_path} ({detail})",
                        "execution_source": "junit_report"
                    })

                    # Map test outcomes to claims
                    test_identifier = f"{classname} {test_name}".lower()
                    for claim in claims:
                        claim_tokens = [w for w in (claim.claim_text + " " + (claim.expected_behavior or "")).lower().split() if len(w) > 3]
                        if any(t in test_identifier for t in claim_tokens):
                            if outcome in {"failed", "errored"}:
                                observations.append({
                                    "claim_id": claim.claim_id,
                                    "artifact_id": art.artifact_id,
                                    "evidence_type": "test",
                                    "polarity": "contradicting",
                                    "observation": f"Automated test {test_name} FAILED: {detail}",
                                    "location_reference": f"{art.artifact_path}::{test_name}",
                                    "provenance": self.name,
                                    "meta_info": {"outcome": outcome, "duration_ms": duration}
                                })
                            elif outcome == "passed":
                                observations.append({
                                    "claim_id": claim.claim_id,
                                    "artifact_id": art.artifact_id,
                                    "evidence_type": "test",
                                    "polarity": "supporting",
                                    "observation": f"Automated test {test_name} PASSED ({duration:.1f}ms).",
                                    "location_reference": f"{art.artifact_path}::{test_name}",
                                    "provenance": self.name,
                                    "meta_info": {"outcome": outcome, "duration_ms": duration}
                                })
                            elif outcome == "skipped":
                                observations.append({
                                    "claim_id": claim.claim_id,
                                    "artifact_id": art.artifact_id,
                                    "evidence_type": "test",
                                    "polarity": "inconclusive",
                                    "observation": f"Automated test {test_name} was SKIPPED.",
                                    "location_reference": f"{art.artifact_path}::{test_name}",
                                    "provenance": self.name,
                                    "meta_info": {"outcome": outcome}
                                })

        return observations, test_executions
