"""Document Verification Engine - FastAPI application."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routes import documents_router, compare_router, report_router

app = FastAPI(title=settings.app_name, debug=settings.debug)


def _clear_dir(d: Path) -> None:
    """Remove all files (and files in subdirs) inside d. Keeps d itself."""
    if not d.exists() or not d.is_dir():
        return
    for f in d.iterdir():
        try:
            if f.is_file():
                f.unlink()
            elif f.is_dir():
                for sub in f.rglob("*"):
                    if sub.is_file():
                        sub.unlink()
                f.rmdir()
        except OSError:
            pass


def _clear_upload_and_report_dirs():
    """Remove old files from upload, report, and extracted dirs on server start (clean slate)."""
    # Clear configured dirs (temp or local)
    for d in (settings.upload_dir, settings.report_dir, settings.extracted_dir):
        _clear_dir(d)
    # Also clear legacy project folders in case they exist (backend/uploads, backend/reports)
    backend_root = Path(__file__).resolve().parent.parent
    for name in ("uploads", "reports", "extracted"):
        _clear_dir(backend_root / name)


@app.on_event("startup")
def startup():
    _clear_upload_and_report_dirs()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(documents_router)
app.include_router(compare_router)
app.include_router(report_router)


@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "docs": "/docs",
        "api": {
            "upload": "POST /api/documents/upload",
            "list": "GET /api/documents/list",
            "compare": "GET /api/compare",
            "report": "POST /api/report/generate",
            "download_json": "GET /api/report/download/{job_id}/json",
            "download_txt": "GET /api/report/download/{job_id}/txt",
        },
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
