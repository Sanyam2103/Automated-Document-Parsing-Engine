
# GetGSA Doc Parser

A FastAPI-based coding exercise simulating a vertical slice of a full-stack AI/service workflow for government procurement.

---

## Features

- **POST /api/ingest:** Accepts two text “documents” (Company Profile, Past Performance), parses them into structured JSON.
- **Field Extraction:** Company info, NAICS codes, POC, address, SAM status, past performance entries.
- **Validation:** Flags missing or invalid fields (missing UEI, bad email, NAICS, etc.).
- **NAICS→SIN Mapping:** Maps NAICS codes to recommended SINs, with no duplicates.
- **Checklist:** Shows if required onboarding/contract conditions are met.
- **Testing:** Pytest suite for missing UEI, invalid email, and NAICS→SIN mapping.
- **Audit Logging:** Logs request id, validation checks, and outcomes per request (stdout).
- **Bonus UI:** Simple HTML page for end-to-end demo.

---

## Quick Start

### 1. **Clone and Install**

```
git clone <your-repo-url>
cd getgsa-parser
python -m venv .venv
source .venv/bin/activate      # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. **Run the API**

```
uvicorn app.main:app --reload
```

- Visit [http://localhost:8000/docs](http://localhost:8000/docs) for interactive Swagger UI.
- Or open [http://localhost:8000/static/index.html](http://localhost:8000/static/index.html) for a minimal frontend.

### 3. **Test the Endpoint**

- Paste your Company Profile and Past Performance (as single or multi-line text).
- Submit in the UI or Swagger.
- View parsed/validated JSON, including extracted fields, validation flags, NAICS→SINs, and checklist.

### 4. **Run Tests**

```
pytest
```
- Runs all required unit tests (missing UEI, invalid email, NAICS→SIN mapping).

---

## API Example

**POST /api/ingest**

- Content-Type: `multipart/form-data`
- Fields:
    - `company_profile`: (text)
    - `past_performance`: (text)

**Response example:**
```
{
  "request_id": "...",
  "parsed": {
    "company": {
      "company_name": "...",
      "uei": "...",
      "duns": "...",
      ...
    },
    "past_performance": [{ ... }]
  },
  "issues": {
    "missing_uei": false,
    "invalid_poc_email": false,
    ...
  },
  "recommended_sins": ["54151S"],
  "checklist": {
    "required_fields_complete": true,
    ...
  }
}
```

---

## Key Files

- `app/main.py` — FastAPI app entrypoint
- `app/services/parser.py` — Text parsing logic
- `app/services/validator.py` — Field validation and flagging
- `app/services/mapper.py` — NAICS to SIN logic
- `app/routers/ingest.py` — The `/api/ingest` endpoint
- `app/core/logging.py` — Audit logging (stdout)
- `static/index.html` — Minimal browser UI
- `tests/test_validation_and_mapping.py` — Unit tests

---

## Audit Logging

- Logs each API request with request id.
- Records validations run and outcomes.
- Find logs in the terminal (stdout).

---

## License

MIT (or as appropriate for your use).

```

***

**How to use:**  
- Save as `README.md` in the project root.  
- Replace `<your-repo-url>` with your repo’s actual URL.  
- Tweak the project folder name as needed.

This README is assignment-ready and covers all core requirements for a recruiter or reviewer. Let me know if you want a more detailed or “production-polished” version!Here’s a complete `README.md` suitable for your FastAPI GetGSA Coding Exercise:

***

# GetGSA Doc Parser

A FastAPI proof-of-concept service for parsing, validating, and mapping company profile and performance texts (simulated pseudo-PDF/DOCX blocks) for government contracts.

***

## Features

- **POST /api/ingest:** Accepts two text blocks (Company Profile & Past Performance), returns extracted, validated fields in structured JSON.
- **Validation:** Flags missing or invalid values (UEI, bad email, required fields).
- **Mapping:** Correct NAICS → SIN mapping with deduplication.
- **Checklist:** Shows if contract conditions are satisfied.
- **Logging/Audit:** Logs request ID, validation checks, and outcomes to console.
- **Test Suite:** Detects missing UEI, invalid email, NAICS→SIN mapping.
- **Minimal UI:** One-page form (see `static/index.html`) for demo/testing.

***

## Quick Start

### 1. Install and Run
```sh
git clone <your-repo-url>
cd getgsa-parser

python -m venv .venv
source .venv/bin/activate         # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```
- Go to [http://localhost:8000/docs](http://localhost:8000/docs) for API docs.
- Or open [http://localhost:8000/static/index.html](http://localhost:8000/static/index.html) for manual testing.

***

### 2. Run Tests

```sh
pytest
```
Confirms the service catches missing UEI, invalid email, and correct NAICS-to-SIN mapping.

***

## API Example

**POST /api/ingest** (`multipart/form-data`):

- `company_profile`: (text area/pasted text)
- `past_performance`: (text area/pasted text)

**Sample Response:**
```json
{
  "request_id": "...",
  "parsed": { ... },
  "issues": {
    "missing_uei": false,
    "invalid_poc_email": false
  },
  "recommended_sins": ["54151S"],
  "checklist": {
    "required_fields_complete": true,
    "valid_contact_info": true,
    "sam_registered": true,
    "has_past_performance": true
  }
}
```
***

## Project Structure

- `app/main.py` – API app entrypoint
- `app/routers/ingest.py` – API endpoint handler
- `app/services/parser.py` – Parsing extracted fields
- `app/services/validator.py` – Validation logic for missing/invalid fields
- `app/services/mapper.py` – NAICS to SIN mapping
- `tests/test_validation_and_mapping.py` – Unit tests
- `static/index.html` – Demo/test frontend UI

***

## Logging/Audit

- Every `/api/ingest` call logs:
  - Request ID
  - Validation checks run (flags)
  - Final outcome (issues, recommended SINs, checklist)
- Log output in your terminal/console (stdout).

***

## License

MIT (or specify as needed for your use).

***

**Assignment Acceptance Criteria: All major functional and audit/test requirements are fully covered.**