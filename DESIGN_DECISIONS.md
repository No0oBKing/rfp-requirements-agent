# Design Decisions (Summary)

## Architecture
- **Multi-agent stack**: Kept a lean agent set (Parser, Extractor, Evaluator, PromptAdd) orchestrated by an `OrchestratorAgent`, instead of the fuller suggested split (Classifier/Preference/Validation) to reduce complexity while meeting requirements. Rationale: pydantic_ai structured outputs with a single extractor + evaluator covers metadata, spaces, items, preferences, and confidences while keeping prompt/context size smaller and aggregation simpler. More LLM agents would add token overhead, cost/latency, and cross-agent consistency risk without clear gains at this scale. 
- **Deterministic parsing**: PDF/DOCX parsing uses `pypdf`/`python-docx` (no LLM) to avoid nondeterminism and reduce cost.
- **Confidence rescoring**: Added a dedicated evaluator agent to re-score confidences using document context; confidences are stored and surfaced in UI, with accept/reject.
- **Prompt-based additions**: Added a PromptAdd agent for natural-language adds; merges items into existing spaces by room_type match or creates new spaces.
- **Persistence layer**: SQLAlchemy ORM with repositories/services; Alembic migrations manage schema. Added `confidence` and `is_accepted` to items.

## Configuration & Prompts
- **Prompts externalized**: All agent system prompts live in `app/prompts/*.py` for easier edits.
- **Model/keys in settings**: `OPENAI_MODEL`, `OPENAI_API_KEY` via env; also admin auth creds and JWT secret in config. `.env.example` provided.
- **Logging**: logfire configured with toggle to disable upstream sending; logs on key success/failure paths.

## Auth & Security
- **JWT with fixed admin**: Implemented option 1 (no signup); login endpoint issues JWT from env creds. All protected routes require bearer token. Streamlit stores token in session and sends headers.
- **No multi-user roles**: Chosen for simplicity; acceptable for assignment scope.

## API & Business Logic
- **Accepted items only in export**: JSON/CSV exports filter to `is_accepted == True`; null/false items excluded.
- **HITL updates**: Per-item accept/reject and edits via PATCH; new spaces/items via manual forms or prompt add.
- **Confidence handling**: Clamped and persisted; UI shows color dot indicators.

## UI Choices
- **Streamlit**: Two pages (dashboard, analysis). Added login form, cleaned metadata layout.
- **Nested grouping**: Spaces as expanders, items grouped by category with inline confidence dot; accept/reject buttons beside update.

## Trade-offs / Deferred
- No project classifier/spec analyzer agents; extractor + evaluator cover scope for now.
- No user signup/roles; single admin via env.
- No deterministic table extraction; parser can be extended if table fidelity becomes important.
