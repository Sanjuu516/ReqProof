import os
import re
from typing import List, Dict, Any, Optional
from app.analyzers.base import BaseAnalyzer, RawObservation

class JavaStaticAnalyzer(BaseAnalyzer):
    def __init__(self):
        self.name = "JavaStaticAnalyzer-v1.0"

    def analyze(self, project_dir: str, claims: List[Any], artifacts: List[Any]) -> List[Dict[str, Any]]:
        """
        Inspects Java source code to collect evidence about controllers, routes,
        validation methods, conditions, and annotations.
        """
        observations = []
        java_artifacts = [a for a in artifacts if a.artifact_type == "source" and (a.language == "java" or a.artifact_path.endswith(".java"))]

        for art in java_artifacts:
            full_path = os.path.join(project_dir, art.artifact_path)
            if not os.path.isfile(full_path):
                continue

            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
            except Exception:
                continue

            content = "".join(lines)

            # Analyze Java content
            for claim in claims:
                claim_text = (claim.claim_text + " " + (claim.expected_behavior or "")).lower()
                tokens = [w for w in re.findall(r'\b[a-zA-Z]{3,}\b', claim_text) if w not in {
                    "the", "and", "should", "must", "shall", "with", "for", "that", "this", "from", "system"
                }]

                # Check 1: Route/Controller presence
                route_matches = re.finditer(r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|RequestMapping)\s*\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\']', content)
                for rm in route_matches:
                    method_ann, route_path = rm.groups()
                    line_no = content[:rm.start()].count('\n') + 1
                    if any(t in route_path.lower() for t in tokens):
                        observations.append({
                            "claim_id": claim.claim_id,
                            "artifact_id": art.artifact_id,
                            "evidence_type": "static",
                            "polarity": "supporting",
                            "observation": f"Found Java REST route @{method_ann}('{route_path}') matching requirement keywords.",
                            "location_reference": f"{art.artifact_path}#L{line_no}",
                            "provenance": self.name,
                            "meta_info": {"route": route_path, "annotation": method_ann, "line": line_no}
                        })

                # Check 2: Validation / Security logic
                for idx, line in enumerate(lines, 1):
                    line_lower = line.lower()
                    
                    # Security checks
                    if any(k in line_lower for k in ["@preauthorize", "@secured", "@rolesallowed"]):
                        if any(t in line_lower or t in ["auth", "role", "permission", "security"] for t in tokens):
                            observations.append({
                                "claim_id": claim.claim_id,
                                "artifact_id": art.artifact_id,
                                "evidence_type": "static",
                                "polarity": "supporting",
                                "observation": f"Found security authorization annotation: {line.strip()}",
                                "location_reference": f"{art.artifact_path}#L{idx}",
                                "provenance": self.name,
                                "meta_info": {"rule": "security_annotation", "line": idx}
                            })

                    # Token expiration / validation logic
                    if any(k in line_lower for k in ["isexpired", "validate", "expiration", "validatetoken", "checktoken"]):
                        if any(t in line_lower for t in tokens) or any(t in ["token", "expired", "expire", "auth"] for t in tokens):
                            # Check whether it actively rejects or throws
                            if "throw" in line_lower or "return false" in line_lower or "unauthorized" in line_lower:
                                observations.append({
                                    "claim_id": claim.claim_id,
                                    "artifact_id": art.artifact_id,
                                    "evidence_type": "static",
                                    "polarity": "supporting",
                                    "observation": f"Found token validation rejection logic: {line.strip()}",
                                    "location_reference": f"{art.artifact_path}#L{idx}",
                                    "provenance": self.name,
                                    "meta_info": {"rule": "validation_rejection", "line": idx}
                                })
                            else:
                                observations.append({
                                    "claim_id": claim.claim_id,
                                    "artifact_id": art.artifact_id,
                                    "evidence_type": "static",
                                    "polarity": "supporting",
                                    "observation": f"Found token validation structure: {line.strip()}",
                                    "location_reference": f"{art.artifact_path}#L{idx}",
                                    "provenance": self.name,
                                    "meta_info": {"rule": "validation_structure", "line": idx}
                                })

                    # Generic method / condition matching
                    if any(t in line_lower for t in tokens if len(t) > 4) and any(kw in line_lower for kw in ["public", "private", "if (", "return"]):
                        # Avoid duplicates
                        if not any(o["location_reference"] == f"{art.artifact_path}#L{idx}" for o in observations):
                            observations.append({
                                "claim_id": claim.claim_id,
                                "artifact_id": art.artifact_id,
                                "evidence_type": "static",
                                "polarity": "supporting",
                                "observation": f"Detected matching implementation structure: {line.strip()[:100]}",
                                "location_reference": f"{art.artifact_path}#L{idx}",
                                "provenance": self.name,
                                "meta_info": {"rule": "keyword_match", "line": idx}
                            })

        return observations
