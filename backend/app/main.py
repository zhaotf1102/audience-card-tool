from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .image_processing import CARD_CATEGORIES, Category, crop_big_card
from .ppt_builder import build_ppt_from_crops
from .storage import JobStore, ensure_job_dirs, save_upload_file

app = FastAPI(title="Audience Card Tool", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WORKSPACE = Path("workspace")
store = JobStore(WORKSPACE)


class CreateJobResponse(BaseModel):
    job_id: str


class CardRecord(BaseModel):
    id: str
    filename: str
    category: Optional[Category] = None
    image_url: str
    crop_urls: List[str] = []


class JobState(BaseModel):
    job_id: str
    cards: List[CardRecord] = []
    template_uploaded: bool = False
    output_pptx_url: Optional[str] = None


class UpdateCategoryRequest(BaseModel):
    category: Category


@app.get("/api/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/api/categories")
def categories() -> Dict[str, str]:
    return CARD_CATEGORIES


@app.post("/api/jobs", response_model=CreateJobResponse)
def create_job() -> CreateJobResponse:
    job_id = uuid4().hex[:12]
    ensure_job_dirs(WORKSPACE, job_id)
    store.save(job_id, {"job_id": job_id, "cards": [], "template_uploaded": False})
    return CreateJobResponse(job_id=job_id)


@app.get("/api/jobs/{job_id}", response_model=JobState)
def get_job(job_id: str) -> JobState:
    state = store.load(job_id)
    if not state:
        raise HTTPException(status_code=404, detail="job not found")
    return JobState(**state)


@app.post("/api/jobs/{job_id}/images", response_model=JobState)
async def upload_images(job_id: str, files: List[UploadFile] = File(...)) -> JobState:
    state = store.must_load(job_id)
    dirs = ensure_job_dirs(WORKSPACE, job_id)

    cards = state.get("cards", [])
    for upload in files:
        card_id = uuid4().hex[:10]
        saved = await save_upload_file(upload, dirs["originals"])
        category = infer_category_from_filename(saved.name)
        cards.append(
            {
                "id": card_id,
                "filename": saved.name,
                "category": category,
                "image_url": f"/api/jobs/{job_id}/files/originals/{saved.name}",
                "crop_urls": [],
            }
        )

    state["cards"] = cards
    store.save(job_id, state)
    return JobState(**state)


@app.post("/api/jobs/{job_id}/template", response_model=JobState)
async def upload_template(job_id: str, file: UploadFile = File(...)) -> JobState:
    state = store.must_load(job_id)
    dirs = ensure_job_dirs(WORKSPACE, job_id)
    suffix = Path(file.filename or "template.pptx").suffix.lower()
    if suffix != ".pptx":
        raise HTTPException(status_code=400, detail="only .pptx template is supported")
    target = dirs["templates"] / "template.pptx"
    await save_upload_file(file, dirs["templates"], target_name=target.name)
    state["template_uploaded"] = True
    store.save(job_id, state)
    return JobState(**state)


@app.patch("/api/jobs/{job_id}/cards/{card_id}/category", response_model=JobState)
def update_card_category(job_id: str, card_id: str, payload: UpdateCategoryRequest) -> JobState:
    state = store.must_load(job_id)
    updated = False
    for card in state.get("cards", []):
        if card["id"] == card_id:
            card["category"] = payload.category
            updated = True
            break
    if not updated:
        raise HTTPException(status_code=404, detail="card not found")
    store.save(job_id, state)
    return JobState(**state)


@app.post("/api/jobs/{job_id}/crop", response_model=JobState)
def crop_job(job_id: str, margin_ratio: float = Form(0.02)) -> JobState:
    state = store.must_load(job_id)
    dirs = ensure_job_dirs(WORKSPACE, job_id)

    for card in state.get("cards", []):
        source = dirs["originals"] / card["filename"]
        if not source.exists():
            continue
        crop_paths = crop_big_card(source, dirs["crops"], card["id"], margin_ratio=margin_ratio)
        card["crop_urls"] = [f"/api/jobs/{job_id}/files/crops/{p.name}" for p in crop_paths]

    store.save(job_id, state)
    return JobState(**state)


@app.post("/api/jobs/{job_id}/ppt", response_model=JobState)
def generate_ppt(job_id: str) -> JobState:
    state = store.must_load(job_id)
    dirs = ensure_job_dirs(WORKSPACE, job_id)
    template = dirs["templates"] / "template.pptx"
    if not template.exists():
        raise HTTPException(status_code=400, detail="template.pptx has not been uploaded")

    output = dirs["outputs"] / "audience_cards_output.pptx"
    build_ppt_from_crops(template, output, state, dirs["crops"])
    state["output_pptx_url"] = f"/api/jobs/{job_id}/files/outputs/{output.name}"
    store.save(job_id, state)
    return JobState(**state)


@app.get("/api/jobs/{job_id}/files/{kind}/{filename}")
def get_file(job_id: str, kind: str, filename: str):
    dirs = ensure_job_dirs(WORKSPACE, job_id)
    if kind not in dirs:
        raise HTTPException(status_code=404, detail="invalid file kind")
    path = dirs[kind] / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="file not found")
    return FileResponse(path)


def infer_category_from_filename(filename: str) -> Optional[Category]:
    name = filename.lower()
    rules = [
        ("male_tall", ["男高", "男-高", "male_tall"]),
        ("male_rich", ["男富", "男-富", "male_rich"]),
        ("male_handsome", ["男帅", "男-帅", "male_handsome"]),
        ("female_fair", ["女白", "女-白", "female_fair"]),
        ("female_rich", ["女富", "女-富", "female_rich"]),
        ("female_beautiful", ["女美", "女-美", "female_beautiful"]),
    ]
    for category, keywords in rules:
        if any(keyword.lower() in name for keyword in keywords):
            return category  # type: ignore[return-value]
    return None
