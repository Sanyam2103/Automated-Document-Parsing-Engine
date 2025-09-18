
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
git clone https://github.com/Sanyam2103/Automated-Document-Parsing-Engine.git
cd Automated-Document-Parsing-Engine
python -m venv .venv
 On Windows: .venv\Scripts\activate
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



