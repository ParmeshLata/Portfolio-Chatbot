# Interview Chatbot — Fixed Version

AI portfolio representative using Gradio, Groq-compatible chat completions, ChromaDB (default embeddings), resume and LinkedIn PDF retrieval, and optional Pushover notifications.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
```

Set `GROQ_API_KEY` and a model supported by your Groq account in `.env`. Put the resume PDF at `docs/Parmesh_Lata_Resume.pdf` and the LinkedIn PDF at `docs/Linkedin.pdf` (or edit the corresponding `.env` paths). These private PDFs are **not included** in this archive.

```bash
python app.py
```

Open http://127.0.0.1:7860. Public Gradio sharing is disabled by default. Enable only if you understand the access/privacy implications. Pushover is optional; set `PUSHOVER_USER` and `PUSHOVER_TOKEN` for notifications.

## Fixes
- Bound tool-call rounds; validated and deduplicated tool requests; added HTTP timeout and error handling.
- Index resume and LinkedIn with section-aware chunking, preserve pre-heading text, and sync stale ChromaDB chunks.
- Remove duplicate full-document system prompt context; include retrieved excerpts per question.
- Configure paths, model, identity and sharing with environment variables.
- Make bot identity transparent; no invented candidate-specific claims.

## Notes
- The model decides when to call tools. Unknown-question notification is best-effort, not guaranteed. If guaranteed auditing is needed, implement a separate deterministic classifier/logging pipeline.
- Retrieval currently uses nearest neighbors without a calibrated distance threshold. Test against real PDFs before selecting a threshold.
- PDF scans without a text layer require OCR (not included).
- Existing ChromaDB entries in the configured collection are replaced by the current document set on startup. Back up `data/` if needed.
- A public production deployment should add authentication, rate limits, privacy notice, and observability.
