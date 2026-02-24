"""Generate downloadable report (JSON and text)."""
import json
from pathlib import Path
from datetime import datetime

from app.schemas.comparison import ComparisonResult, Contradiction
from app.schemas.document import ExtractedDocument
from app.schemas.report import ReportSummary


def generate_report(
    documents: list[ExtractedDocument],
    comparison: ComparisonResult,
    output_dir: Path,
    job_id: str,
) -> tuple[Path, Path]:
    """
    Write report as JSON and TXT. Returns (path_to_json, path_to_txt).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = ReportSummary(
        summary=comparison.summary or "",
        total_docs=comparison.total_documents,
        consistent_count=comparison.documents_consistent,
        contradiction_count=len(comparison.contradictions),
        contradictions=comparison.contradictions,
        comparison_result=comparison,
    )
    # Serialize for JSON (Pydantic model)
    report_json = summary.model_dump(mode="json")
    report_json["documents"] = [d.model_dump(mode="json") for d in documents]
    report_json["generated_at"] = datetime.utcnow().isoformat() + "Z"
    report_json["job_id"] = job_id

    json_path = output_dir / f"report_{job_id}.json"
    txt_path = output_dir / f"report_{job_id}.txt"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report_json, f, indent=2, ensure_ascii=False)

    lines = [
        "DOCUMENT VERIFICATION REPORT",
        "=" * 50,
        f"Generated: {report_json['generated_at']}",
        f"Job ID: {job_id}",
        "",
        comparison.summary or "",
        "",
        f"Documents processed: {comparison.total_documents}",
        f"Contradictions found: {len(comparison.contradictions)}",
        "",
        "CONTRADICTIONS",
        "-" * 30,
    ]
    for i, c in enumerate(comparison.contradictions, 1):
        lines.append(f"{i}. [{c.contradiction_type.value}] {c.title}")
        lines.append(f"   {c.description}")
        lines.append(f"   Sources: {', '.join(c.sources)}")
        lines.append("")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return json_path, txt_path
