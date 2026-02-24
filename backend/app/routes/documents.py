"""Upload and parse documents."""
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from app.config import settings
from app.parsers import parse_document
from app.schemas.document import ExtractedDocument

router = APIRouter(prefix="/api/documents", tags=["documents"])

# In-memory store for this session (replace with DB later)
_parsed: dict[str, ExtractedDocument] = {}
_uploaded_paths: dict[str, Path] = {}


def _allowed(filename: str) -> bool:
    ext = Path(filename).suffix.lower()
    return ext in (".pdf", ".xlsx", ".xls")


@router.post("/upload")
async def upload_and_parse(files: list[UploadFile] = File(...)):
    """
    Upload one or more PDF/Excel files. Each is parsed and stored.
    Returns list of parsed file IDs and extracted data.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    results = []
    for f in files:
        if not f.filename or not _allowed(f.filename):
            results.append(
                {"filename": f.filename or "?", "error": "Unsupported file type", "file_id": None}
            )
            continue
        file_id = str(uuid.uuid4())
        dest = settings.upload_dir / f"{file_id}_{f.filename}"
        try:
            with dest.open("wb") as out:
                shutil.copyfileobj(f.file, out)
        except Exception as e:
            results.append({"filename": f.filename, "error": str(e), "file_id": None})
            continue
        _uploaded_paths[file_id] = dest
        try:
            doc = parse_document(dest, file_id=file_id, filename=f.filename)
            _parsed[file_id] = doc
            results.append(
                {
                    "file_id": file_id,
                    "filename": f.filename,
                    "doc_type": doc.doc_type.value,
                    "extracted": doc.model_dump(mode="json"),
                }
            )
        except Exception as e:
            results.append({"filename": f.filename, "file_id": file_id, "error": str(e)})
    return {"parsed": results, "count": len(results)}


@router.get("/list")
async def list_parsed(clear: str = ""):
    """Return all parsed documents. If clear=1 or clear=true, clear all first then return empty list."""
    cleared = 0
    if clear and str(clear).lower() in ("1", "true", "yes"):
        cleared = clear_all_parsed_documents()
    out = [
        {
            "file_id": d.file_id,
            "filename": d.filename,
            "doc_type": d.doc_type.value,
            "extracted": d.model_dump(mode="json"),
        }
        for d in _parsed.values()
    ]
    result = {"documents": out, "total": len(out)}
    if clear and str(clear).lower() in ("1", "true", "yes"):
        result["cleared"] = cleared
    return JSONResponse(
        content=result,
        headers={"Cache-Control": "no-store, no-cache, must-revalidate"},
    )


@router.get("/{file_id}")
async def get_document(file_id: str):
    """Get one parsed document by file_id."""
    if file_id not in _parsed:
        raise HTTPException(status_code=404, detail="Document not found")
    doc = _parsed[file_id]
    return doc.model_dump(mode="json")


def get_parsed_documents() -> list[ExtractedDocument]:
    """Used by compare/report routes to get current parsed docs."""
    return list(_parsed.values())


def clear_all_parsed_documents() -> int:
    """Clear in-memory store and delete uploaded files. Returns number cleared. Used by main app."""
    count = 0
    for file_id in list(_parsed.keys()):
        del _parsed[file_id]
        if file_id in _uploaded_paths:
            path = _uploaded_paths.pop(file_id)
            try:
                if path.exists():
                    path.unlink()
            except OSError:
                pass
        count += 1
    return count
