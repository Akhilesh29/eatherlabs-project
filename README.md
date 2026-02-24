# Document Verification Engine

## Project Description

The system ingests multiple PDF and Excel documents (drawings, specifications, budgets, SOVs), extracts structured data from each, cross-compares them to find contradictions, and generates downloadable reports.

### What It Does

1. **Ingests Documents** - Upload PDFs (drawings, specs) and Excel files (SOV, budgets)
2. **Parses & Understands** - Extracts structured data (quantities, materials, costs) from each document
3. **Cross-Compares** - Automatically flags contradictions between documents:
   - Quantity mismatches (e.g., drawing shows 22 fire dampers, SOV budgets 15)
   - Material mismatches (e.g., specs require steel doors, SOV lists aluminum)
   - Budget overruns (e.g., total budget $10.2M vs loan amount $10M)
4. **Generates Reports** - Creates downloadable JSON and TXT reports with all contradictions


## Tech Stack

### Backend
- **Framework**: FastAPI (Python)
- **PDF Parsing**: pdfplumber
- **Excel Parsing**: pandas, openpyxl, xlrd
- **Validation**: Pydantic
- **Server**: Uvicorn

### Frontend
- **Build Tool**: Vite
- **Language**: TypeScript
- **UI**: Vanilla DOM (no framework)
- **Styling**: CSS

### Storage
- **Current**: In-memory (Python dicts) + file system for uploads
- **Future**: PostgreSQL, Elasticsearch (optional)

---

## Full Setup Process

### Prerequisites

- **Python 3.8+** (check: `python --version`)
- **Node.js 20.19+ or 22.12+** (check: `node --version`)
- **npm** (comes with Node.js)

### Step 1: Clone/Download Project

```bash
cd "c:\Users\HP\Desktop\eatherlabs project"
```

### Step 2: Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Backend will run on:** http://127.0.0.1:8000

**API Documentation:** http://127.0.0.1:8000/docs (Swagger UI)

**Health Check:** http://127.0.0.1:8000/health

### Step 3: Frontend Setup

Open a **new terminal** (keep backend running):

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

**Frontend will run on:** http://localhost:5173

The frontend automatically proxies `/api` requests to the backend at `http://127.0.0.1:8000` (configured in `frontend/vite.config.ts`).

---

## How to Use

1. **Start both servers** (backend on port 8000, frontend on port 5173)
2. **Open browser** → http://localhost:5173
3. **Upload files** → Click "Choose Files", select PDFs/Excel files, click "Upload & Parse"
4. **View parsed files** → See list of parsed documents with extracted data
5. **Compare** → Click "Compare documents" to find contradictions
6. **Generate report** → Click "Generate & download report", then download JSON or TXT

---

## API Endpoints

### Documents
- `POST /api/documents/upload` - Upload and parse PDF/Excel files
- `GET /api/documents/list` - List all parsed documents
- `GET /api/documents/{file_id}` - Get specific document by ID

### Comparison
- `GET /api/compare` - Compare all parsed documents and return contradictions

### Reports
- `POST /api/report/generate` - Generate report (returns job_id and download URLs)
- `GET /api/report/download/{job_id}/json` - Download report as JSON
- `GET /api/report/download/{job_id}/txt` - Download report as TXT

---

## Supported File Types

### PDF
- **Text-based PDFs** - Extracts text using pdfplumber
- **Supported fields**:
  - Drawings: fire_dampers, total_doors, floors
  - Specs: fire_dampers_required, door_specs (materials)
- **Future**: OCR support for scanned PDFs (Tesseract)

### Excel
- **Formats**: `.xlsx`, `.xls`
- **Supported structure**: SOV/Budget style
  - Line items (description)
  - Quantities (budgeted_qty)
  - Costs (budgeted_cost)
  - Totals (total_budget, loan_amount)

---

## Example Workflow

1. **Upload Documents**:
   - `drawing.pdf` → Extracted: `{ fire_dampers: 22, total_doors: 150 }`
   - `specs.pdf` → Extracted: `{ fire_dampers_required: 15, door_specs: "steel" }`
   - `sov.xlsx` → Extracted: `{ line_items: [{ line_item: "Fire Dampers", budgeted_qty: 15 }] }`

2. **Compare** → Finds contradictions:
   - Fire dampers: Drawing=22, SOV=15 → Missing 7 in SOV
   - Door material: Specs=steel, SOV=aluminum → Material mismatch

3. **Download Report** → JSON/TXT with full details

---

## Troubleshooting

### Backend won't start
- Check Python version: `python --version` (need 3.8+)
- Ensure venv is activated: `venv\Scripts\activate` (Windows)
- Reinstall dependencies: `pip install -r requirements.txt`

### Frontend won't start
- Check Node.js version: `node --version` (need 20.19+ or 22.12+)
- Clear node_modules: `rm -rf node_modules` then `npm install`
- Check if port 5173 is already in use

### API calls fail (CORS/proxy)
- Ensure backend is running on port 8000
- Check `frontend/vite.config.ts` proxy settings
- Verify backend CORS allows `localhost:5173` (currently allows all origins)

### Files not parsing correctly
- Check file format (PDF must have extractable text, Excel must have standard columns)
- View API docs at http://127.0.0.1:8000/docs to test upload endpoint directly
- Check backend logs for parsing errors

---



