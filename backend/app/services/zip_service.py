import os
import zipfile
import hashlib
from typing import List, Dict, Any, Tuple
from app.config import settings
from app.models import Artifact, Project
from sqlalchemy.orm import Session

IGNORED_DIRS = {
    ".git", "__pycache__", "node_modules", "target", "build", ".gradle",
    ".idea", ".vscode", "dist", ".next", ".turbo", "coverage"
}

LANGUAGE_EXTENSIONS = {
    ".java": "java",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".js": "javascript",
    ".jsx": "javascript",
    ".py": "python",
    ".xml": "xml",
    ".json": "json",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".sql": "sql",
}

def is_safe_path(base_dir: str, path: str, follow_symlinks: bool = True) -> bool:
    if follow_symlinks:
        matchpath = os.path.realpath(path)
    else:
        matchpath = os.path.abspath(path)
    return base_dir == os.path.commonpath((base_dir, matchpath))

def calculate_file_hash(filepath: str) -> str:
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def extract_and_scan_zip(zip_path: str, project_id: int, db: Session) -> Tuple[str, List[Artifact], Dict[str, Any]]:
    extract_dir = os.path.join(settings.UPLOAD_DIR, f"project_{project_id}")
    os.makedirs(extract_dir, exist_ok=True)
    real_base = os.path.realpath(extract_dir)

    file_count = 0
    max_files = 1000

    # Extract safely
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.infolist():
            file_count += 1
            if file_count > max_files:
                raise ValueError("ZIP archive contains too many files (limit: 1000)")

            # Prevent directory traversal attacks
            destination = os.path.join(extract_dir, member.filename)
            if not is_safe_path(real_base, destination):
                raise ValueError(f"Unsafe ZIP archive path detected: {member.filename}")

            if member.is_dir():
                os.makedirs(destination, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(destination), exist_ok=True)
                with zf.open(member) as source, open(destination, 'wb') as target:
                    target.write(source.read())

    # Scan extracted directory
    artifacts = []
    manifests = []
    languages_detected = set()

    # Clear previous artifacts for this project
    db.query(Artifact).filter(Artifact.project_id == project_id).delete()

    for root, dirs, files in os.walk(extract_dir):
        # Prune ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS and not d.startswith('.')]
        
        for file in files:
            if file.startswith('.'):
                continue
            
            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, extract_dir)
            _, ext = os.path.splitext(file)
            ext = ext.lower()
            
            # Determine artifact type
            artifact_type = "other"
            language = LANGUAGE_EXTENSIONS.get(ext)
            
            if language:
                languages_detected.add(language)

            if file in {"pom.xml", "package.json", "build.gradle", "application.properties", "application.yml"}:
                artifact_type = "config"
                manifests.append(rel_path)
            elif "test" in rel_path.lower() or file.endswith("Test.java") or file.endswith(".test.ts") or file.endswith(".spec.ts"):
                artifact_type = "test"
            elif ext in {".tsx", ".jsx", ".html", ".vue", ".css"}:
                artifact_type = "ui"
            elif ext in {".java", ".ts", ".js", ".py"}:
                artifact_type = "source"
            elif ext == ".xml" and ("test" in rel_path.lower() or "surefire" in rel_path.lower()):
                artifact_type = "test_report"

            file_hash = calculate_file_hash(full_path)
            
            art = Artifact(
                project_id=project_id,
                artifact_path=rel_path,
                artifact_type=artifact_type,
                language=language,
                content_hash=file_hash,
                analysis_status="processed"
            )
            db.add(art)
            artifacts.append(art)

    db.commit()

    summary = {
        "total_files": len(artifacts),
        "languages": list(languages_detected),
        "manifests": manifests,
        "artifact_types": {
            "source": len([a for a in artifacts if a.artifact_type == "source"]),
            "ui": len([a for a in artifacts if a.artifact_type == "ui"]),
            "config": len([a for a in artifacts if a.artifact_type == "config"]),
            "test": len([a for a in artifacts if a.artifact_type == "test"]),
            "other": len([a for a in artifacts if a.artifact_type == "other"]),
        }
    }

    return extract_dir, artifacts, summary
