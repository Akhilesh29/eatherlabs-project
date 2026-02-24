"""Generate and download report."""
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import settings
from app.routes.documents import get_parsed_documents
from app.services.comparison import compare_documents
from app.services.report import generate_report

router = APIRouter(prefix="/api/report", tags=["report"])


@router.post("/generate")
async def generate():
    """
    Generate report (JSON + TXT) from current parsed documents and comparison.
    Returns job_id and paths for download.
    """
    documents = get_parsed_documents()
    if not documents:
        return {"error": "No documents parsed. Upload and parse documents first.", "job_id": None}
    comparison = compare_documents(documents)
    job_id = str(uuid.uuid4())[:8]
    json_path, txt_path = generate_report(
        documents, comparison, settings.report_dir, job_id
    )
    return {
        "job_id": job_id,
        "json_url": f"/api/report/download/{job_id}/json",
        "txt_url": f"/api/report/download/{job_id}/txt",
        "summary": comparison.summary,
        "contradiction_count": len(comparison.contradictions),
    }


@router.get("/download/{job_id}/json")
async def download_json(job_id: str):
    """Download report as JSON."""
    path = settings.report_dir / f"report_{job_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report not found. Generate report first.")
    return FileResponse(
        path,
        media_type="application/json",
        filename=f"verification_report_{job_id}.json",
    )


@router.get("/download/{job_id}/txt")
async def download_txt(job_id: str):
    """Download report as TXT."""
    path = settings.report_dir / f"report_{job_id}.txt"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Report not found. Generate report first.")
    return FileResponse(
        path,
        media_type="text/plain",
        filename=f"verification_report_{job_id}.txt",
    )
