# trial_book_m-m

Workflow-driven AI book generation system with FastAPI, Streamlit, PostgreSQL, Excel import, human review gates, Serper snippet injection, and final draft export.

## Stack

- FastAPI backend
- Streamlit editor UI
- PostgreSQL
- SQLAlchemy ORM
- Google AI Studio / Generative Language API (`gemma-4-26b-a4b-it`)
- OpenPyXL Excel import
- Serper research integration with fallback
- Teams/email notifications
- Local artifact storage with Supabase-compatible adapter interface

## Run locally

1. Copy `.env.example` to `.env` (do **not** commit your real credentials or keys). Fill in required fields as described below.
2. Start all containers:

```bash
docker compose up --build
```

3. Open the services:
- API docs: `http://localhost:8000/docs`
- Streamlit UI: `http://localhost:8501`

## Demo flow

1. (Optional) Run `python sample_input_generator.py` to create a local `sample_input.xlsx` file for bulk import.
2. Upload Excel in Streamlit or create a book manually in the UI.
3. Review and approve outline.
4. Review and approve each chapter—regenerating as needed.
5. Compile the finished book to download `.txt` and `.docx` outputs from the UI.

---

## Environment variables
- Use `.env.example` for all variable documentation and as a starting point.
- Key required fields:
  - Set `GOOGLE_API_KEY` for free Gemma (AI Studio) use
  - Set `SMTP_*` and `NOTIFICATION_EMAIL_TO` for email notifications (see README for Gmail app password instructions if needed)
  - All other variables are required for basic workflow

---

## Important files and folders

- `app/main.py` — FastAPI backend entrypoint
- `app/api/` — Modular API routes (books, chapters, outlines, artifacts, reviews)
- `app/db/models/` — Modular SQLAlchemy ORM models split by domain
- `app/services/` — Business logic for workflow, LLMs, import/export, notifications
- `streamlit_app.py` — UI dashboard+review frontend
- `docker-compose.yml` — Runs DB, API, UI together
- `.env.example` — Required environment/config fields
- `requirements.txt` — All Python dependencies for development
- `artifacts/` — Compiled book outputs (auto-generated, gitignored)
- `sample_input_generator.py` — Demo input generator
- `tests/manual_google_probe.py` — (gitignored) script to verify your key/model (not part of submission)

---

## DB structure screenshot for submission

1. Use DBeaver or pgAdmin to connect to your Docker Postgres:
   - Host: `localhost` or `127.0.0.1`
   - Port: as configured in Docker (`5432` or `5433`)
   - Database: `bookgen`
   - Username: `postgres`
   - Password: `postgres`
2. Expand database tree to show all tables — take a screenshot.
3. Double-click some tables (`books`, `outlines`, `chapter_versions`, `book_artifacts`), choose 'View Data', and take data screenshots.

Attach these screenshots to your submission. Terminal screenshots (psql/\dt, SELECT * FROM ...) are also accepted.

## Output files for submission
- Download `.txt` and `.docx` after compiling a book (see `artifacts/<book-id>/final_draft.txt` and `.docx`).
- Attach these actual outputs to your submission ZIP or upload as requested.

## Screenshots for submission checklist
- Streamlit dashboard UI
- Review outline/chapter screen
- DB structure from DBeaver/pgAdmin
- Example output file
- Email notification in your inbox (optional but helpful)

---

## Architecture highlights
- Modular API, services, and models for maintainability
- Asynchronous review gates and gating logic across stages
- Context chaining for chapters via stored summaries
- SQLite import, artifact export, Google API fallback logic
- Designed for free usage: runs with Gemma for LLM, local DB, free SMTP
- Backgrounding, job queue, and full Supabase/S3 adapters considered for future expansion

## Limitations
- Free-tier Google model is sometimes slow or responds with unstructured output
- System uses robust parsing, validation, and fallback to keep workflows going
- Background job manager (e.g., Celery) would be next for production

For more, see inline comments and "docs/".

## Architecture notes

- The system runs on self-hosted PostgreSQL by default.
- Persistence and storage are organized so Supabase-compatible adapters can be added without changing workflow logic.
- Chapters are generated sequentially and consume summaries of previous chapters for context chaining.
- Research uses Serper snippets when configured and deterministic fallback snippets otherwise.
