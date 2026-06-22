# RepoLens

AI-assisted repository audit platform. Deterministic analyzers discover issues; Groq converts structured findings into a professional audit report.

**Philosophy:** Analysis first, AI second.

## Features (Phase 1 + Phase 2)

- ZIP file upload (Python, JavaScript, TypeScript)
- Tree-sitter AST parsing with shared cache across analyzers
- Large file detection (>500 lines)
- Large function detection (>50 lines)
- Cyclomatic complexity analysis (Python, via Radon)
- Security pattern detection
- Circular import detection
- **Dead code detection:** unused imports, variables, and functions
- Standardized finding schema with categories and evidence
- **Semantic duplicate detection** (local embeddings, cosine similarity)
- Category scoring (Maintainability, Security, Architecture, Dead Code)
- AI-generated audit report (Groq — `llama-3.3-70b-versatile` by default)

## Tech Stack

| Layer    | Technology              |
|----------|-------------------------|
| Frontend | Next.js 16, TypeScript, Tailwind CSS |
| Backend  | FastAPI, Python 3.12    |
| AI       | Groq API (pluggable provider architecture) |

## Project Structure

```
repolens/
├── backend/
│   ├── app/
│   │   ├── analyzers/       # Static analysis modules
│   │   ├── main.py          # FastAPI application
│   │   ├── services/        # Embeddings, report generation
│   │   ├── providers/       # AI provider abstraction (Groq, Gemini)
│   │   ├── pipeline.py      # Analysis orchestration
│   │   ├── scanner.py       # Repository traversal
│   │   └── scoring.py       # Score calculation
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app/                 # Next.js App Router
│   ├── components/          # UI components
│   ├── lib/                 # API client
│   └── Dockerfile
├── docker-compose.yml
└── README.md
```

## Local Development

### Prerequisites

- Python 3.12+
- Node.js 20+
- npm
- (Optional) Groq API key from [Groq Console](https://console.groq.com/keys)

### Backend

**Windows (recommended):**

```powershell
.\scripts\setup-backend.ps1
.\scripts\start-backend.ps1
```

Default port is **8080** because Windows often blocks port 8000 (`WinError 10013`).

**Manual setup:**

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env and set GROQ_API_KEY (optional — fallback report works without it)

uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

API docs: http://127.0.0.1:8080/docs

#### Windows troubleshooting

| Error | Fix |
|-------|-----|
| `Unable to copy venvlauncher.exe` | Delete `backend\venv`, then run `.\scripts\setup-backend.ps1`. Prefer Python from [python.org](https://www.python.org/downloads/) over the Microsoft Store. |
| `[WinError 10013]` on port 8000 | Use port 8080: `.\scripts\start-backend.ps1 -Port 8080` or `-Port 9000` |
| `python` not found | Use `py -3.12` instead of `python` |

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local

npm run dev
```

App: http://localhost:3000

### Environment Variables

**Backend (`backend/.env` or project root `.env`)**

| Variable                   | Description                              | Default |
|----------------------------|------------------------------------------|---------|
| `GROQ_API_KEY`             | Groq API key                             | —       |
| `GROQ_MODEL`               | Groq model for report generation         | `llama-3.3-70b-versatile` |
| `REPORT_PROVIDER`          | AI provider (`groq` or `gemini`)         | `groq`  |
| `REPORT_TOP_FINDINGS_LIMIT`| Max findings sent to AI provider         | `15`    |
| `REPORT_MAX_PAYLOAD_BYTES` | Max JSON payload size for AI requests    | `12000` |
| `REPORT_TIMEOUT_SECONDS`   | AI request timeout in seconds            | `60`    |
| `MAX_UPLOAD_SIZE`          | Max upload size in bytes                 | `26214400` (25 MB) |
| `MAX_EXTRACTED_SIZE`       | Max extracted archive size in bytes      | `104857600` (100 MB) |
| `MAX_EXTRACTED_FILES`      | Max files allowed in archive               | `5000` |
| `UPLOAD_DIRECTORY`         | Temp directory for uploads               | `/tmp/repolens/uploads` |
| `LOG_LEVEL`                | Logging level                            | `INFO` |
| `CORS_ORIGINS`             | Comma-separated allowed origins          | `http://localhost:3000` |
| `DEBUG`                    | Expose internal errors when true           | `false` |

**Legacy Gemini (optional):** set `REPORT_PROVIDER=gemini` and `GEMINI_API_KEY`.

**Frontend (`frontend/.env.local`)**

| Variable              | Description           | Default                 |
|-----------------------|-----------------------|-------------------------|
| `NEXT_PUBLIC_API_URL` | Backend API base URL  | `http://127.0.0.1:8080` |

## Sample Test Projects

Complex sample repositories are included for manual testing:

```
samples/
├── python-sample/          # Python project source
├── python-sample.zip       # Ready to upload
├── js-sample/
├── js-sample.zip
├── typescript-sample/
└── typescript-sample.zip
```

Each sample intentionally includes issues for all analyzers:
- Large files (>500 lines)
- Large functions (>50 lines)
- High cyclomatic complexity (Python)
- Security patterns (hardcoded secrets, eval, innerHTML)
- Circular import chains

**Regenerate samples:**

```bash
python scripts/build_sample_projects.py
```

**Test with the API:**

```powershell
curl -X POST -F "file=@samples/python-sample.zip" http://127.0.0.1:8080/api/analyze
```

## Docker

```bash
# Optional: set Groq API key in .env
export GROQ_API_KEY=your_key_here

docker compose up --build
```

- Frontend: http://localhost:3000
- Backend: http://localhost:8000

## API

### `POST /api/analyze`

Upload a ZIP file containing a source code repository.

**Request:** `multipart/form-data` with field `file` (ZIP)

**Response:**

```json
{
  "repository_name": "my-project",
  "metrics": {
    "files_scanned": 42,
    "total_lines": 8500,
    "python_files": 20,
    "javascript_files": 15,
    "typescript_files": 7,
    "findings_count": 12
  },
  "scores": {
    "maintainability": 84,
    "security": 90,
    "architecture": 95
  },
  "findings": [],
  "ai_report": "# Repository Audit Report\n..."
}
```

## Scoring

All categories start at 100 and deductions are applied per finding:

| Finding Type       | Category         | Deduction |
|--------------------|------------------|-----------|
| Large file         | Maintainability  | -5        |
| Large function     | Maintainability  | -2        |
| Complexity         | Maintainability  | -3        |
| Security issue     | Security         | -10       |
| Circular dependency| Architecture     | -5        |

Scores are clamped between 0 and 100.

## Testing

### Backend unit and API tests

```bash
cd backend
venv\Scripts\activate          # Windows
pip install -r requirements.txt
pytest tests/ -v
```

**Expected results:**
- `test_compute_scores_*` — scoring deductions and clamping pass
- `test_safe_extract_*` — zip-slip blocked, valid archives extracted
- `test_health_endpoint` — returns `{"status":"ok"}`
- `test_analyze_valid_python_repo` — returns findings and scores for a sample ZIP
- `test_report_service.py` — Groq provider, payload limits, error handling
- `test_duplicate_logic.py` — semantic duplicate detection

### Groq setup and troubleshooting

1. Create a free API key at [console.groq.com/keys](https://console.groq.com/keys).
2. Add to project root `.env`:
   ```
   GROQ_API_KEY=gsk_...
   GROQ_MODEL=llama-3.3-70b-versatile
   ```
3. Restart the backend.

| Symptom | Cause | Fix |
|---------|-------|-----|
| `AI report unavailable.` in report | Missing/invalid key, rate limit, or timeout | Check `GROQ_API_KEY`, wait and retry, or increase `REPORT_TIMEOUT_SECONDS` |
| Automated summary only | No `GROQ_API_KEY` configured | Expected — analysis still works; add key for AI report |
| 429 rate limit | Groq free-tier quota exceeded | Wait for reset or upgrade plan |
| Slow first duplicate analysis | Embedding model download | One-time ~90 MB download; subsequent runs are faster |

**Payload limits:** Only scores, metrics, summaries, and top findings (default 15, max payload 12 KB) are sent to Groq. Source code is never transmitted.

### Phase 2 manual test (dead code sample)

```powershell
.\scripts\start-backend.ps1
curl -X POST -F "file=@samples/dead-code-sample.zip" http://127.0.0.1:8080/api/analyze
```

**Expected:** ~14 findings including 4 unused imports, 4 unused variables, 4 unused functions, plus large file and complexity. Response includes `scores.dead_code`, `metrics.dead_code_summary`, and `metrics.findings_by_category`.

### Manual API test

```bash
curl -X POST -F "file=@your-repo.zip" http://localhost:8000/api/analyze
```

## Security

- ZIP uploads are validated for size and path traversal (zip-slip)
- Extracted archives are size- and file-count-limited
- Uploaded code is never executed — static analysis only

## Ignored Directories

The scanner automatically ignores:

`node_modules`, `.git`, `dist`, `build`, `.next`, `coverage`, `venv`, `__pycache__`

## License

MIT
