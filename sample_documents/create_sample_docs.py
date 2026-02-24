"""Create two sample documents with hardcoded comparison fields (different values) to show contradictions."""
from pathlib import Path

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
except ImportError:
    print("Install reportlab: pip install reportlab")
    raise

import openpyxl
from openpyxl.styles import Font

OUTPUT_DIR = Path(__file__).resolve().parent


def create_drawing_pdf():
    """PDF classified as drawing: fire_dampers=22, total_doors=150, floors=5."""
    path = OUTPUT_DIR / "drawing_floor_plan.pdf"
    c = canvas.Canvas(str(path), pagesize=letter)
    c.setFont("Helvetica", 12)
    c.drawString(100, 700, "Floor Plan Drawing")
    c.drawString(100, 670, "Fire dampers: 22")
    c.drawString(100, 640, "Total doors: 150")
    c.drawString(100, 610, "Floors: 5")
    c.save()
    print(f"Created {path}")
    return path


def create_sov_excel():
    """Excel SOV: fire dampers qty=15 (mismatch with drawing 22), door line with aluminum."""
    path = OUTPUT_DIR / "schedule_of_values.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "SOV"
    # Headers the parser looks for
    ws.append(["Line Item", "Qty", "Budgeted Cost"])
    ws.append(["Fire Dampers", 15, 45000])
    ws.append(["Doors - Aluminum", 150, 120000])
    ws.append(["HVAC Units", 8, 95000])
    # Totals row
    ws.append(["Total Budget", None, "$10.2M"])
    for row in ws.iter_rows(min_row=1, max_row=1):
        for cell in row:
            cell.font = Font(bold=True)
    wb.save(path)
    print(f"Created {path}")
    return path


if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    create_drawing_pdf()
    create_sov_excel()
    print("\nDone. Upload drawing_floor_plan.pdf and schedule_of_values.xlsx to see:")
    print("  - Fire dampers: Drawing (22) vs SOV (15) -> quantity mismatch")
