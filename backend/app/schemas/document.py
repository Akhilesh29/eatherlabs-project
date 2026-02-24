"""Structured data schemas for extracted documents."""
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class DocumentType(str, Enum):
    """Type of document for parsing and comparison."""

    PDF_DRAWING = "pdf_drawing"
    PDF_SPECS = "pdf_specs"
    EXCEL_SOV = "excel_sov"
    EXCEL_BUDGET = "excel_budget"
    PDF_OTHER = "pdf_other"


# --- Drawing-style extraction (counts, quantities from plans) ---
class DrawingData(BaseModel):
    """Structured data from a PDF drawing/plan."""

    fire_dampers: Optional[int] = None
    total_doors: Optional[int] = None
    floors: Optional[int] = None
    extra: dict[str, Any] = Field(default_factory=dict)


# --- Specs-style extraction (requirements, materials) ---
class SpecsData(BaseModel):
    """Structured data from a PDF spec document."""

    fire_dampers_required: Optional[int] = None
    door_specs: Optional[str] = None  # e.g. "steel, fire-rated"
    extra: dict[str, Any] = Field(default_factory=dict)


# --- SOV / Budget line item ---
class SOVLineItem(BaseModel):
    """Single line from SOV or budget."""

    line_item: str
    budgeted_qty: Optional[float] = None
    budgeted_cost: Optional[str] = None  # e.g. "$45,000"
    extra: dict[str, Any] = Field(default_factory=dict)


class SOVData(BaseModel):
    """Structured data from Excel SOV or budget."""

    line_items: list[SOVLineItem] = Field(default_factory=list)
    total_budget: Optional[str] = None  # e.g. "$10.2M"
    loan_amount: Optional[str] = None
    extra: dict[str, Any] = Field(default_factory=dict)


# --- Generic extracted document (wrapper) ---
class ExtractedDocument(BaseModel):
    """One document's parsed result with metadata."""

    file_id: str
    filename: str
    doc_type: DocumentType
    # One of these is filled based on doc_type
    drawing: Optional[DrawingData] = None
    specs: Optional[SpecsData] = None
    sov: Optional[SOVData] = None
    raw_text_preview: Optional[str] = None  # first N chars for debugging
    extra: dict[str, Any] = Field(default_factory=dict)
