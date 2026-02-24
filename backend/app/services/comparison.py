"""Cross-compare extracted documents and flag contradictions."""
import re
from typing import Optional

from app.schemas.comparison import Contradiction, ContradictionType, ComparisonResult
from app.schemas.document import DocumentType, ExtractedDocument


def _parse_money(s: Optional[str]) -> Optional[float]:
    """Parse $10.2M or $45,000 to float."""
    if not s or not str(s).strip():
        return None
    s = str(s).replace(",", "").replace("$", "").strip().upper()
    if s.endswith("M"):
        try:
            return float(s[:-1]) * 1_000_000
        except ValueError:
            return None
    try:
        return float(s)
    except ValueError:
        return None


def _find_sov_line(items: list, keyword: str) -> Optional[dict]:
    """Find a line item that contains keyword (e.g. 'fire damper')."""
    key = keyword.lower()
    for item in items:
        if key in (item.get("line_item") or "").lower():
            return item
    return None


def compare_documents(documents: list[ExtractedDocument]) -> ComparisonResult:
    """Compare all extracted docs and return contradictions."""
    contradictions: list[Contradiction] = []
    drawings = [d for d in documents if d.doc_type == DocumentType.PDF_DRAWING and d.drawing]
    specs = [d for d in documents if d.doc_type == DocumentType.PDF_SPECS and d.specs]
    sov_docs = [d for d in documents if d.doc_type == DocumentType.EXCEL_SOV and d.sov]

    # --- Fire dampers: drawing vs SOV vs specs ---
    drawing_dampers: Optional[int] = None
    for d in drawings:
        if d.drawing and d.drawing.fire_dampers is not None:
            drawing_dampers = d.drawing.fire_dampers
            break
    spec_dampers: Optional[int] = None
    for d in specs:
        if d.specs and d.specs.fire_dampers_required is not None:
            spec_dampers = d.specs.fire_dampers_required
            break
    sov_dampers: Optional[int] = None
    sov_filenames: list[str] = []
    for d in sov_docs:
        if not d.sov:
            continue
        for li in d.sov.line_items:
            if "fire damper" in (li.line_item or "").lower():
                q = li.budgeted_qty
                if q is not None:
                    sov_dampers = int(q) if sov_dampers is None else sov_dampers
                    sov_filenames.append(d.filename)
                break

    if drawing_dampers is not None and sov_dampers is not None and drawing_dampers != sov_dampers:
        diff = drawing_dampers - sov_dampers
        contradictions.append(
            Contradiction(
                contradiction_type=ContradictionType.QUANTITY_MISMATCH,
                title="Fire dampers: Drawing vs SOV",
                description=f"Drawing shows {drawing_dampers} fire dampers, SOV budgets {sov_dampers}. "
                + (f"Missing {diff} in SOV." if diff > 0 else f"SOV has {-diff} extra."),
                sources=[d.filename for d in drawings if d.drawing] + sov_filenames,
                details={"drawing": drawing_dampers, "sov": sov_dampers, "diff": diff},
            )
        )
    if (
        drawing_dampers is not None
        and spec_dampers is not None
        and drawing_dampers != spec_dampers
    ):
        contradictions.append(
            Contradiction(
                contradiction_type=ContradictionType.QUANTITY_MISMATCH,
                title="Fire dampers: Drawing vs Specs",
                description=f"Drawing shows {drawing_dampers}, Specs require {spec_dampers}.",
                sources=[d.filename for d in drawings] + [d.filename for d in specs],
                details={"drawing": drawing_dampers, "specs": spec_dampers},
            )
        )

    # --- Door material: specs vs SOV line item ---
    spec_door: Optional[str] = None
    for d in specs:
        if d.specs and d.specs.door_specs:
            spec_door = d.specs.door_specs.strip().lower()
            break
    sov_door: Optional[str] = None
    for d in sov_docs:
        if not d.sov:
            continue
        for li in d.sov.line_items:
            if "door" in (li.line_item or "").lower():
                # Could parse material from line_item or extra; simple check
                text = (li.line_item or "").lower()
                if "steel" in text:
                    sov_door = "steel"
                elif "aluminum" in text:
                    sov_door = "aluminum"
                if sov_door:
                    break
        if sov_door:
            break
    if spec_door and sov_door:
        if "steel" in spec_door and "aluminum" in sov_door:
            contradictions.append(
                Contradiction(
                    contradiction_type=ContradictionType.MATERIAL_MISMATCH,
                    title="Door material: Specs vs SOV",
                    description="Specs say steel doors, SOV references aluminum doors.",
                    sources=[d.filename for d in specs] + [d.filename for d in sov_docs],
                    details={"specs": spec_door, "sov": sov_door},
                )
            )
        elif "aluminum" in spec_door and "steel" in sov_door:
            contradictions.append(
                Contradiction(
                    contradiction_type=ContradictionType.MATERIAL_MISMATCH,
                    title="Door material: Specs vs SOV",
                    description="Specs say aluminum doors, SOV references steel doors.",
                    sources=[d.filename for d in specs] + [d.filename for d in sov_docs],
                    details={"specs": spec_door, "sov": sov_door},
                )
            )

    # --- Budget total vs loan amount ---
    total_budget: Optional[float] = None
    loan_amount: Optional[float] = None
    for d in sov_docs:
        if d.sov:
            if d.sov.total_budget:
                total_budget = _parse_money(d.sov.total_budget)
            if d.sov.loan_amount:
                loan_amount = _parse_money(d.sov.loan_amount)
    if total_budget is not None and loan_amount is not None and loan_amount > 0:
        if total_budget > loan_amount:
            pct = ((total_budget - loan_amount) / loan_amount) * 100
            contradictions.append(
                Contradiction(
                    contradiction_type=ContradictionType.BUDGET_OVERRUN,
                    title="Budget vs Loan overrun",
                    description=f"Total budget {total_budget:,.0f} exceeds loan {loan_amount:,.0f} by {pct:.1f}%.",
                    sources=[d.filename for d in sov_docs],
                    details={"total_budget": total_budget, "loan_amount": loan_amount, "pct_overrun": pct},
                )
            )

    total = len(documents)
    consistent = total - min(len(contradictions), total)  # simplified: docs "consistent" if no contradictions
    if total > 0:
        consistent = max(0, total - len(contradictions))
    summary = f"{consistent}/{total} docs consistent. {len(contradictions)} contradictions found."
    return ComparisonResult(
        total_documents=total,
        documents_consistent=consistent,
        contradictions=contradictions,
        summary=summary,
    )
