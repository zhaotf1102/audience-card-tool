from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from fastapi import HTTPException, UploadFile


def ensure_job_dirs(workspace: Path, job_id: str) -> Dict[str, Path]:
    root = workspace / job_id
    dirs = {
        "root": root,
        "originals": root / "originals",
        "crops": root / "crops",
        "templates": root / "templates",
        "outputs": root / "outputs",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return dirs


class JobStore:
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace
        self.workspace.mkdir(parents=True, exist_ok=True)

    def state_path(self, job_id: str) -> Path:
        return self.workspace / job_id / "job.json"

    def load(self, job_id: str) -> Optional[Dict[str, Any]]:
        path = self.state_path(job_id)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def must_load(self, job_id: str) -> Dict[str, Any]:
        state = self.load(job_id)
        if not state:
            raise HTTPException(status_code=404, detail="job not found")
        return state

    def save(self, job_id: str, state: Dict[str, Any]) -> None:
        path = self.state_path(job_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


async def save_upload_file(upload: UploadFile, directory: Path, target_name: str | None = None) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    original_name = upload.filename or f"upload_{uuid4().hex}"
    filename = target_name or safe_filename(original_name)
    target = directory / filename
    content = await upload.read()
    target.write_bytes(content)
    return target


def safe_filename(filename: str) -> str:
    path = Path(filename)
    stem = re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", path.stem, flags=re.UNICODE).strip("._")
    suffix = path.suffix.lower()
    if not stem:
        stem = uuid4().hex[:10]
    return f"{stem}_{uuid4().hex[:6]}{suffix}"
