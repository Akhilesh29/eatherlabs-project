"""Report output schema."""
from pydantic import BaseModel

from .comparison import ComparisonResult, Contradiction


class ReportSummary(BaseModel):
    """Full report for download (JSON)."""

    summary: str
    total_docs: int
    consistent_count: int
    contradiction_count: int
    contradictions: list[Contradiction]
    comparison_result: ComparisonResult
