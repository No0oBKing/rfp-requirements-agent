# Architecture

```mermaid
flowchart LR
    subgraph UI["Streamlit UI"]
        A1["Upload Doc (login w/ JWT)"]
        A2["View Analysis / Edit / Accept-Reject"]
        A3["Prompt Add (Spaces/Items)"]
        A4["Export Accepted Items"]
    end

    subgraph API["FastAPI"]
        APIRouter["Routes (/auth/login, /projects/...)"]
        Auth["JWT auth (admin env creds)"]
        Service["ProjectService (orchestration/exports)"]
        Orchestrator["OrchestratorAgent (parser + extractor + evaluator)"]
        PromptAdd["PromptAddAgent"]
        Repo["Repositories (Projects/Spaces/Items/Documents)"]
    end

    subgraph Agents["LLM Agents (pydantic_ai)"]
        Parser["DocumentParser (PDF/DOCX)"]
        Extractor["RequirementsExtractor (prompt: extractor_prompt.py)"]
        Evaluator["ConfidenceEvaluator (prompt: evaluator_prompt.py)"]
        PromptAdder["PromptAdd (prompt: prompt_add_prompt.py)"]
    end

    subgraph DB["PostgreSQL"]
        TblProj[(projects)]
        TblSpace[(spaces)]
        TblItem[(items + confidence + is_accepted)]
        TblDoc[(documents)]
    end

    subgraph Files["Prompts & Config"]
        P1["prompts/extractor_prompt.py"]
        P2["prompts/evaluator_prompt.py"]
        P3["prompts/prompt_add_prompt.py"]
        Env[".env (DB/LLM/auth/logfire)"]
    end

    UI -->|JWT login| APIRouter
    APIRouter --> Auth
    Auth --> APIRouter
    APIRouter --> Service
    Service --> Orchestrator
    Service --> PromptAdd
    Service --> Repo
    Repo --> DB

    Orchestrator --> Parser
    Orchestrator --> Extractor
    Orchestrator --> Evaluator

    PromptAdd --> PromptAdder

    Extractor --> P1
    Evaluator --> P2
    PromptAdder --> P3

    UI -->|Upload/Analyze| APIRouter
    UI -->|Edit/Accept/Reject| APIRouter
    UI -->|Prompt Add| APIRouter
    UI -->|Export accepted| APIRouter
```

## Flow Description
- User logs in (JWT) via Streamlit. UI stores the token and includes it in all API calls.
- Upload triggers document save; analyze triggers parser → extractor → evaluator via orchestrator; results are persisted to Postgres.
- Users review spaces/items, edit fields, and accept/reject items; statuses and edits are saved.
- Prompt-based additions send user text to PromptAddAgent; outputs are merged into existing spaces or new ones.
- Exports (JSON/CSV) include only items marked accepted.

## ER Diagram

```mermaid
erDiagram
    PROJECT ||--o{ SPACE : has
    PROJECT ||--o{ DOCUMENT : has
    SPACE ||--o{ ITEM : contains

    PROJECT {
        int id PK
        string name
        string client_type
        string location
        string timeline
        string budget_range
        datetime created_at
    }
    SPACE {
        int id PK
        int project_id FK
        string room_type
        string dimension
        string area
    }
    ITEM {
        int id PK
        int space_id FK
        string name
        string category
        string technical_specs
        string material_preference
        string color_preference
        string brand_preference
        string special_instruction
        int quantity
        float confidence
        bool is_accepted
    }
    DOCUMENT {
        int id PK
        int project_id FK
        string filename
        string file_path
        datetime upload_date
    }
```
