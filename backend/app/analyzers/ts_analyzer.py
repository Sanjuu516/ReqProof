import os
import re
from typing import List, Dict, Any
from app.analyzers.base import BaseAnalyzer

class TypeScriptFrontendAnalyzer(BaseAnalyzer):
    def __init__(self):
        self.name = "TSFrontendAnalyzer-v1.0"

    def analyze(self, project_dir: str, claims: List[Any], artifacts: List[Any]) -> List[Dict[str, Any]]:
        """
        Inspects React/TypeScript/JavaScript frontend files to discover routes,
        forms, input validation, and user interface components.
        """
        observations = []
        ui_artifacts = [a for a in artifacts if a.artifact_type in {"ui", "source"} and (a.language in {"typescript", "javascript"} or a.artifact_path.endswith((".tsx", ".jsx", ".ts", ".js")))]

        for art in ui_artifacts:
            full_path = os.path.join(project_dir, art.artifact_path)
            if not os.path.isfile(full_path):
                continue

            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
            except Exception:
                continue

            content = "".join(lines)

            for claim in claims:
                claim_text = (claim.claim_text + " " + (claim.expected_behavior or "")).lower()
                tokens = [w for w in re.findall(r'\b[a-zA-Z]{3,}\b', claim_text) if w not in {
                    "the", "and", "should", "must", "shall", "with", "for", "that", "this", "from", "system"
                }]

                # 1. Route declarations
                route_matches = re.finditer(r'<Route\s+[^>]*path=["\']([^"\']+)["\']|path:\s*["\']([^"\']+)["\']', content)
                for rm in route_matches:
                    p1, p2 = rm.groups()
                    route = p1 or p2
                    line_no = content[:rm.start()].count('\n') + 1
                    if any(t in route.lower() for t in tokens):
                        observations.append({
                            "claim_id": claim.claim_id,
                            "artifact_id": art.artifact_id,
                            "evidence_type": "ui",
                            "polarity": "supporting",
                            "observation": f"Found frontend route definition: {route}",
                            "location_reference": f"{art.artifact_path}#L{line_no}",
                            "provenance": self.name,
                            "meta_info": {"route": route, "line": line_no}
                        })

                # 2. Form & Input Validation checks
                for idx, line in enumerate(lines, 1):
                    line_lower = line.lower()
                    
                    # Form submissions
                    if "onsubmit" in line_lower or "handlesubmit" in line_lower:
                        if any(t in line_lower for t in tokens) or any(t in ["form", "submit", "save", "input"] for t in tokens):
                            observations.append({
                                "claim_id": claim.claim_id,
                                "artifact_id": art.artifact_id,
                                "evidence_type": "ui",
                                "polarity": "supporting",
                                "observation": f"Found form submission handler: {line.strip()[:90]}",
                                "location_reference": f"{art.artifact_path}#L{idx}",
                                "provenance": self.name,
                                "meta_info": {"rule": "form_handler", "line": idx}
                            })

                    # Input validation rules (e.g. zod, yup, HTML5 validation)
                    if any(v in line_lower for v in ["z.string()", "yup.string()", "required", "minlength", "maxlength", "validation"]):
                        if any(t in line_lower for t in tokens) or any(t in ["validation", "input", "field", "error"] for t in tokens):
                            observations.append({
                                "claim_id": claim.claim_id,
                                "artifact_id": art.artifact_id,
                                "evidence_type": "ui",
                                "polarity": "supporting",
                                "observation": f"Found UI input validation rule: {line.strip()[:90]}",
                                "location_reference": f"{art.artifact_path}#L{idx}",
                                "provenance": self.name,
                                "meta_info": {"rule": "ui_validation", "line": idx}
                            })

                    # Buttons / Action elements
                    if "<button" in line_lower and any(t in line_lower for t in tokens if len(t) > 3):
                        observations.append({
                            "claim_id": claim.claim_id,
                            "artifact_id": art.artifact_id,
                            "evidence_type": "ui",
                            "polarity": "supporting",
                            "observation": f"Found UI interactive button: {line.strip()[:90]}",
                            "location_reference": f"{art.artifact_path}#L{idx}",
                            "provenance": self.name,
                            "meta_info": {"rule": "ui_button", "line": idx}
                        })

        return observations
