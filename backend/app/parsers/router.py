"""Route file to appropriate parser and return ExtractedDocument."""
from pathlib import Path
from typing import Optional

from app.parsers.excel_parser import parse_excel
from app.parsers.pdf_parser import parse_pdf
from app.schemas.document import ExtractedDocument


def parse_document(
    path: Path,
    file_id: Optional[str] = None,
    filename: Optional[str] = None,
) -> ExtractedDocument:
    """Dispatch to PDF or Excel parser based on extension."""
    suffix = path.suffix.lower()
    if suffix in (".xlsx", ".xls"):
        return parse_excel(path, file_id=file_id, filename=filename)
    if suffix == ".pdf":
        return parse_pdf(path, file_id=file_id, filename=filename)
    raise ValueError(f"Unsupported file type: {suffix}")
