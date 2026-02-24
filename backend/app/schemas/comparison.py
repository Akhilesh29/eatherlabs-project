"""Schemas for comparison results and contradictions."""
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ContradictionType(str, Enum):
    """Kind of contradiction."""

    QUANTITY_MISMATCH = "quantity_mismatch"
    MATERIAL_MISMATCH = "material_mismatch"
    BUDGET_OVERRUN = "budget_overrun"
    MISSING_ITEM = "missing_item"
    OTHER = "other"


class Contradiction(BaseModel):
    """A single flagged contradiction between documents."""

    contradiction_type: ContradictionType
    title: str
    description: str
    sources: list[str] = Field(default_factory=list)  # file names or IDs
    details: dict[str, Any] = Field(default_factory=dict)
    severity: str = "high"  # high, medium, low


class ComparisonResult(BaseModel):
    """Result of comparing all extracted documents."""

    total_documents: int
    documents_consistent: int
    contradictions: list[Contradiction] = Field(default_factory=list)
    summary: Optional[str] = None
