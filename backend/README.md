# OTT Feed Backend

The backend is a Python 3.12 modular monolith built with FastAPI, SQLAlchemy and PostgreSQL 17.

## U05 Recommendation and AI Grounding

U05 lives under `src/ott_feed/recommendation/` and provides:

- Korean/English structured recommendation intent and conversational session transitions.
- Approved-catalog hard filtering, deterministic ranking and diversity.
- Candidate-local metadata evidence and fail-closed candidate/claim validation.
- Provider-neutral bounded AI interpretation/drafting with deterministic fallback.
- Versioned PostgreSQL decision closure and privacy-safe recommendation traces.

The AI provider is optional. Without an approved endpoint, credential, pricing and evaluation configuration, the service uses deterministic intent parsing and evidence-derived explanation templates.

## Verification

Run Ruff, strict MyPy and pytest from this directory using the locked `.venv`. PostgreSQL integration tests require a real PostgreSQL 17 `TEST_DATABASE_URL`; a selected integration test that skips is not a successful gate.
