import json
import re
from typing import List, Dict, Any, Optional
from app.config import settings

def _heuristic_decomposition(requirement_text: str) -> List[Dict[str, Any]]:
    """
    Deterministic rule-based requirement decomposer used as a resilient fallback
    when Gemini API key is not configured or during offline execution.
    """
    sentences = [s.strip() for s in re.split(r'[.\n;]+', requirement_text) if len(s.strip()) > 8]
    if not sentences:
        sentences = [requirement_text.strip()]

    claims = []
    for i, sentence in enumerate(sentences):
        lower = sentence.lower()
        
        # Infer relevant artifact types based on keywords
        artifacts = []
        if any(w in lower for w in ["api", "endpoint", "request", "response", "token", "status", "http", "jwt", "header"]):
            artifacts.append("api")
        if any(w in lower for w in ["ui", "button", "screen", "page", "form", "display", "input", "modal", "view"]):
            artifacts.append("ui")
        if any(w in lower for w in ["validate", "check", "function", "service", "class", "method", "logic", "database", "store"]):
            artifacts.append("source")
        if any(w in lower for w in ["test", "verify", "assert", "coverage"]):
            artifacts.append("test")
            
        if not artifacts:
            artifacts = ["source", "api", "test"]

        # Expected behavior extraction
        if "should" in lower:
            expected = sentence[lower.find("should"):]
        elif "must" in lower:
            expected = sentence[lower.find("must"):]
        elif "shall" in lower:
            expected = sentence[lower.find("shall"):]
        else:
            expected = f"System satisfies: {sentence}"

        claims.append({
            "claim_text": sentence,
            "expected_behavior": expected.strip(),
            "verification_criteria": f"Verify via {', '.join(artifacts)} artifacts that: {sentence}",
            "relevant_artifact_types": ",".join(artifacts),
            "review_status": "reviewed",
            "dependencies": []
        })

    # Add default dependency from subsequent claims to the first claim if multiple
    if len(claims) > 1:
        for idx in range(1, len(claims)):
            claims[idx]["dependencies"] = [0] # depends on claim 0

    return claims


def decompose_requirement_with_gemini(requirement_text: str, project_context: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Decomposes natural-language requirements into atomic, independently verifiable claims
    using Google Gemini API with fallback to deterministic heuristic parser.
    """
    if not settings.GEMINI_API_KEY:
        return _heuristic_decomposition(requirement_text)

    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        
        prompt = f"""
You are an expert software requirement verification assistant for ReqProof.
Decompose the following software requirement into smaller, atomic, independently verifiable claims.

Requirement:
"{requirement_text}"

Project Context:
"{project_context or 'Web application with Java backend and TypeScript frontend'}"

For each atomic claim, produce:
- claim_text: A concise, single verifiable claim statement.
- expected_behavior: Clear description of expected behavior.
- relevant_artifact_types: Comma-separated list containing any of: source, ui, api, runtime, test.
- verification_criteria: Concrete conditions under which this claim is verified or refuted.
- dependencies: Array of integer indices of preceding claims this claim depends on (e.g. [0]).

Respond ONLY with a valid JSON array of objects with the keys:
["claim_text", "expected_behavior", "relevant_artifact_types", "verification_criteria", "dependencies"]
"""

        model = genai.GenerativeModel(settings.GEMINI_MODEL)
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean markdown codeblocks if present
        if text.startswith("```"):
            text = re.sub(r"^```[a-zA-Z]*\n", "", text)
            text = re.sub(r"\n```$", "", text)
            
        data = json.loads(text)
        if isinstance(data, list) and len(data) > 0:
            return data
    except Exception as e:
        # Fallback on any network/API exception
        pass

    return _heuristic_decomposition(requirement_text)
