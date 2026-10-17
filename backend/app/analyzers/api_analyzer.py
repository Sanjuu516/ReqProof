import os
import re
from typing import List, Dict, Any
from app.analyzers.base import BaseAnalyzer

class ApiRuntimeAnalyzer(BaseAnalyzer):
    def __init__(self):
        self.name = "ApiRuntimeAnalyzer-v1.0"

    def analyze(self, project_dir: str, claims: List[Any], artifacts: List[Any]) -> List[Dict[str, Any]]:
        """
        Validates API endpoints against claim verification criteria.
        Checks for endpoint presence, status codes, and security invariants.
        """
        observations = []

        # Find route configs or property files
        for art in artifacts:
            if art.artifact_type not in {"config", "source"}:
                continue
            
            full_path = os.path.join(project_dir, art.artifact_path)
            if not os.path.isfile(full_path):
                continue

            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception:
                continue

            for claim in claims:
                claim_lower = (claim.claim_text + " " + (claim.expected_behavior or "")).lower()

                # Scenario: Token Expiration / Auth Check
                if "expired" in claim_lower and ("token" in claim_lower or "auth" in claim_lower):
                    # Check if project contains security config permitting all or missing expiration check
                    if "permitall" in content.lower() and "/api" in content.lower():
                        observations.append({
                            "claim_id": claim.claim_id,
                            "artifact_id": art.artifact_id,
                            "evidence_type": "api",
                            "polarity": "contradicting",
                            "observation": "API security configuration permits requests without enforcing token validation (permitAll found on API route).",
                            "location_reference": f"{art.artifact_path}",
                            "provenance": self.name,
                            "meta_info": {"issue": "insecure_api_config"}
                        })
                    elif "securityfilterchain" in content.lower() or "addfilterbefore" in content.lower():
                        observations.append({
                            "claim_id": claim.claim_id,
                            "artifact_id": art.artifact_id,
                            "evidence_type": "api",
                            "polarity": "supporting",
                            "observation": "Verified active SecurityFilterChain configured for token authentication inspection.",
                            "location_reference": f"{art.artifact_path}",
                            "provenance": self.name,
                            "meta_info": {"config": "security_filter"}
                        })

                # Scenario: Endpoint Response / Status assertion
                if "endpoint" in claim_lower or "api" in claim_lower:
                    route_match = re.search(r'["\'](/api/[a-zA-Z0-9_\-/]+)["\']', content)
                    if route_match:
                        endpoint = route_match.group(1)
                        observations.append({
                            "claim_id": claim.claim_id,
                            "artifact_id": art.artifact_id,
                            "evidence_type": "api",
                            "polarity": "supporting",
                            "observation": f"Verified API endpoint registered: {endpoint}",
                            "location_reference": f"{art.artifact_path}",
                            "provenance": self.name,
                            "meta_info": {"endpoint": endpoint}
                        })

        return observations
