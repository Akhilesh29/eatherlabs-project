"""PDF parsing: extract text and produce structured data (drawing or specs)."""
import re
import uuid
from pathlib import Path
from typing import Optional

import pdfplumber
from pdfplumber.page import Page

from app.schemas.document import (
    DocumentType,
    DrawingData,
    ExtractedDocument,
    SpecsData,
)


def _extract_text_from_pdf(path: Path, max_chars: int = 5000) -> str:
    """Extract raw text from PDF using pdfplumber."""
    text_parts = []
    total = 0
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            if total >= max_chars:
                break
            t = page.extract_text()
            if t:
                text_parts.append(t)
                total += len(t)
    return "\n".join(text_parts)[:max_chars]


def _infer_doc_type(text: str, filename: str) -> DocumentType:
    """Heuristic: drawing vs specs from keywords."""
    lower = (text + " " + filename).lower()
    if "sov" in lower or "schedule of values" in lower:
        return DocumentType.PDF_OTHER  # SOV usually Excel
    if any(k in lower for k in ("drawing", "plan", "floor plan", "dwg")):
        return DocumentType.PDF_DRAWING
    if any(k in lower for k in ("spec", "specification", "requirement", "material")):
        return DocumentType.PDF_SPECS
    # Default: try to extract numbers (drawing-like) vs requirements (spec-like)
    if re.search(r"\b(fire.?damper|damper|door)s?\s*[=:]?\s*\d+", lower, re.I):
        return DocumentType.PDF_DRAWING
    return DocumentType.PDF_SPECS


def _extract_drawing_data(text: str) -> DrawingData:
    """Parse numbers from text for drawing/plan style."""
    numbers: dict[str, Optional[int]] = {
        "fire_dampers": None,
        "total_doors": None,
        "floors": None,
    }
    lower = text.lower()
    # Fire dampers: "fire dampers: 22" or "fire dampers 22"
    m = re.search(r"fire\s*dampers?\s*[=:]\s*(\d+)", lower, re.I)
    if m:
        numbers["fire_dampers"] = int(m.group(1))
    m = re.search(r"(\d+)\s*fire\s*dampers?", lower, re.I)
    if m and numbers["fire_dampers"] is None:
        numbers["fire_dampers"] = int(m.group(1))
    # Doors
    m = re.search(r"(?:total\s*)?doors?\s*[=:]\s*(\d+)", lower, re.I)
    if m:
        numbers["total_doors"] = int(m.group(1))
    m = re.search(r"(\d+)\s*(?:total\s*)?doors?", lower, re.I)
    if m and numbers["total_doors"] is None:
        numbers["total_doors"] = int(m.group(1))
    # Floors
    m = re.search(r"floors?\s*[=:]\s*(\d+)", lower, re.I)
    if m:
        numbers["floors"] = int(m.group(1))
    m = re.search(r"(\d+)\s*floors?", lower, re.I)
    if m and numbers["floors"] is None:
        numbers["floors"] = int(m.group(1))
    return DrawingData(
        fire_dampers=numbers["fire_dampers"],
        total_doors=numbers["total_doors"],
        floors=numbers["floors"],
    )


def _extract_specs_data(text: str) -> SpecsData:
    """Parse requirements from text for spec style."""
    data: dict[str, Optional[int | str]] = {
        "fire_dampers_required": None,
        "door_specs": None,
    }
    lower = text.lower()
    m = re.search(r"fire\s*dampers?\s*(?:required)?\s*[=:]\s*(\d+)", lower, re.I)
    if m:
        data["fire_dampers_required"] = int(m.group(1))
    m = re.search(r"(\d+)\s*fire\s*dampers?\s*(?:required)?", lower, re.I)
    if m and data["fire_dampers_required"] is None:
        data["fire_dampers_required"] = int(m.group(1))
    # Door specs: look for "steel", "fire-rated", "aluminum"
    for pattern in [
        r"door\s*specs?\s*[=:]\s*([^\n.]+)",
        r"doors?\s*(?:shall be|are)\s*([^\n.]+)",
        r"(steel|aluminum|fire-rated[^\n.]*)",
    ]:
        m = re.search(pattern, lower, re.I)
        if m:
            data["door_specs"] = m.group(1).strip()[:200]
            break
    return SpecsData(
        fire_dampers_required=data["fire_dampers_required"],
        door_specs=data["door_specs"],
    )


def parse_pdf(
    path: Path,
    file_id: Optional[str] = None,
    filename: Optional[str] = None,
) -> ExtractedDocument:
    """Parse a PDF and return structured ExtractedDocument."""
    file_id = file_id or str(uuid.uuid4())
    filename = filename or path.name
    text = _extract_text_from_pdf(path)
    doc_type = _infer_doc_type(text, filename)
    drawing = None
    specs = None
    if doc_type == DocumentType.PDF_DRAWING:
        drawing = _extract_drawing_data(text)
    else:
        specs = _extract_specs_data(text)
    return ExtractedDocument(
        file_id=file_id,
        filename=filename,
        doc_type=doc_type,
        drawing=drawing,
        specs=specs,
        raw_text_preview=text[:500] if text else None,
    )
