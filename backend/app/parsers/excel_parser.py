"""Excel parsing: SOV / budget → structured SOVData."""
import re
import uuid
from pathlib import Path
from typing import Optional

import pandas as pd

from app.schemas.document import (
    DocumentType,
    ExtractedDocument,
    SOVData,
    SOVLineItem,
)


def _normalize_cost(s: object) -> Optional[str]:
    """Turn cell value into cost string like $45,000."""
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    if isinstance(s, (int, float)):
        if s >= 1_000_000:
            return f"${s/1_000_000:.1f}M"
        return f"${s:,.0f}"
    text = str(s).strip()
    if not text:
        return None
    if re.match(r"^\$?[\d,.]+\s*M?$", text, re.I):
        return text if text.startswith("$") else f"${text}"
    return text


def _find_column(df: pd.DataFrame, *names: str) -> Optional[str]:
    """Return first column name that matches any of the given names (case-insensitive)."""
    lower = {n.lower() for n in names}
    for col in df.columns:
        if str(col).strip().lower() in lower:
            return str(col)
    for col in df.columns:
        if any(n in str(col).lower() for n in lower):
            return str(col)
    return None


def parse_excel(
    path: Path,
    file_id: Optional[str] = None,
    filename: Optional[str] = None,
) -> ExtractedDocument:
    """Parse Excel (xlsx/xls) and return ExtractedDocument with SOV data."""
    file_id = file_id or str(uuid.uuid4())
    filename = filename or path.name
    line_items: list[SOVLineItem] = []
    total_budget: Optional[str] = None
    loan_amount: Optional[str] = None
    extra: dict = {}

    try:
        if path.suffix.lower() == ".xls":
            df = pd.read_excel(path, engine="xlrd")
        else:
            df = pd.read_excel(path, engine="openpyxl")
    except Exception as e:
        return ExtractedDocument(
            file_id=file_id,
            filename=filename,
            doc_type=DocumentType.EXCEL_SOV,
            sov=SOVData(line_items=[], extra={"error": str(e)}),
        )

    if df.empty or len(df.columns) == 0:
        return ExtractedDocument(
            file_id=file_id,
            filename=filename,
            doc_type=DocumentType.EXCEL_SOV,
            sov=SOVData(line_items=[]),
        )

    # Find columns: line item / description, qty, cost
    col_item = _find_column(df, "line item", "line_item", "description", "item", "scope")
    col_qty = _find_column(df, "qty", "quantity", "budgeted_qty", "budgeted qty")
    col_cost = _find_column(df, "cost", "budgeted_cost", "budgeted cost", "amount", "price")
    col_total = _find_column(df, "total", "total budget", "budget total", "loan", "loan amount")

    for _, row in df.iterrows():
        item_name = None
        if col_item:
            item_name = row.get(col_item)
        if item_name is None or (isinstance(item_name, float) and pd.isna(item_name)):
            item_name = " ".join(str(row.get(c, "")) for c in df.columns[:3])
        item_name = str(item_name).strip() if item_name else "Unnamed"
        qty = row.get(col_qty) if col_qty else None
        try:
            qty = float(qty) if qty is not None and not (isinstance(qty, float) and pd.isna(qty)) else None
        except (TypeError, ValueError):
            qty = None
        cost = _normalize_cost(row.get(col_cost)) if col_cost else None
        if item_name and (qty is not None or cost):
            line_items.append(
                SOVLineItem(line_item=item_name, budgeted_qty=qty, budgeted_cost=cost)
            )

    if col_total:
        for _, row in df.iterrows():
            val = row.get(col_total)
            if val is not None and not (isinstance(val, float) and pd.isna(val)):
                total_budget = _normalize_cost(val) or total_budget
                break

    return ExtractedDocument(
        file_id=file_id,
        filename=filename,
        doc_type=DocumentType.EXCEL_SOV,
        sov=SOVData(
            line_items=line_items,
            total_budget=total_budget,
            loan_amount=loan_amount,
            extra=extra,
        ),
    )
