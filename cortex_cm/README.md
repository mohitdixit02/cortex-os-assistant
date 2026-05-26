# Cortex CM (Common Module)

The core dependency module for the Cortex AI application. `cortex_cm` provides the foundational database models, Redis configurations, LLM/Sensory model loaders, and generic utilities shared across `cortex_server`, `cortex_core`, `cortex_queue`, and `cortex_event_tool`.

## Key Features & Architecture

### 1. Unified Database Schema (PostgreSQL)
Utilizes **SQLModel** (Pydantic + SQLAlchemy) to define the schema and handle database models.
It manages relationships between users, active sessions, short-term/long-term memory, emotional profiles, task queues, and scheduled events.

**Core Entities:**
*   `User` & `UserConfig`: Core identities and personal preferences (e.g., voice timeouts, timezones).
*   `ChatSession` & `Message`: Thread management and individual conversational turns.
*   `UserShortTermMemory` (STM): Summaries and immediate preferences extracted from recent chat sessions.
*   `UserEmotionalProfile` (LTM): Snapshot of user mood and behavior constraints (e.g., emotional/logical/social levels) mapped to specific times of day.
*   `UserKnowledgeBase` (LTM): Global trait preferences mapped using `pgvector` embeddings for similarity search.
*   `Task` & `UserEvent`: Entities tracking async workflow progress and scheduled reminders.

### 2. Redis Caching & Pub/Sub
Provides isolated Redis connection clients configured for specific use cases via `RedisModeType`:
*   **TOKEN (DB 0):** Caches Auth tokens and rapid-access user configurations.
*   **TASK (DB 1):** Act as the `Pending Queue` where `cortex_server` submits work and `cortex_core` worker consumes it.
*   **RESULT (DB 2):** Uses Redis Pub/Sub (`user_stream:*`) to stream final AI responses or intermediate logic back to the active `cortex_server` websocket.
*   **EVENT (DB 3):** Dedicated data store (Hashes) and sorted sets (ZSET) for the `cortex_event_tool` to schedule and trigger delayed reminders.

### 3. Centralized Model Orchestration
Encapsulates Hugging Face Transformers, Pipelines, and LangChain wrappers within `utility/cortex/__init__.py`. 
Models are configured in `models.py` and implement local-cache-first strategies.

*   **Sensory:** Whisper STT (`openai/whisper-small`) and Kokoro TTS (`hexgrad/Kokoro-82M`).
*   **LLMs:** 
    *   `main` (Casual chatting/fallback)
    *   `planner` & `heavy_planner` (Workflow orchestration)
    *   `main_orchestrator` (High-level decision making)
    *   `heavy_response_model` (Final, in-depth text synthesis)
*   **Embeddings & Classification:** `Sentence-Transformers` for vector mapping and `BERT` for emotion detection.

### 4. Shared Utilities
*   **CRUD Operations:** Pre-built asynchronous wrappers (`create_one`, `get_similar`, etc.) for interacting with PostgreSQL.
*   **Token Streaming:** The `iterate_tokens_async` utility bridges synchronous generator outputs (like LLM token streams) into asynchronous environments.
*   **Time & Environment:** Standardized timezone parsers (`time_utils.py`) and global environment variables (`config.py`).
*   **Colored Logging:** Standardized CLI logging formats specifically color-coded for different microservices.

---

## Directory Structure

```text
cortex_cm/
├── docs/                       # Architecture and Schema Documentation
│   └── TABLE_SCHEMA.md         # Detailed explanation of PostgreSQL entities
├── pg/                         # PostgreSQL SQLModel Definitions
│   ├── enums.py                # Database Enums (RoleType, TaskStatus, etc.)
│   ├── models.py               # SQLModel Table definitions
│   ├── req/
│   │   └── crud.py             # Standardized generic DB operations (create, delete, pgvector similarity search)
│   └── sql/
│       ├── create_tables.sql   # Raw DDL statements (including pgvector extension)
│       └── seed_data.sql       # Dummy data for integration testing
├── redis/                      # Redis Clients and Specific DB Operations
│   ├── config_helper.py        # Fetches user config from Redis Token Cache (fallback to DB)
│   ├── event_tool.py           # ZSET and Hash operations for scheduling events
│   └── redis_client.py         # Singleton Redis connection manager supporting multiple DB targets
└── utility/                    # Shared Helpers
    ├── config.py               # Global `env` provider (dotenv parsing)
    ├── logger.py               # Colored component-based logging
    ├── main.py                 # Async/Sync streaming bridges and chunk formatters
    ├── time_utils.py           # Timezone conversions and time-of-day parsing
    ├── cortex/
    │   ├── __init__.py         # Lazy/Eager loaders for HF Pipelines and Langchain Endpoints
    │   ├── config.py           # Cortex limits (chunk sizes, iteration limits, thresholds)
    │   └── models.py           # Centralized configuration mapping (model paths, precision, tokens)
    └── sensory/
        └── config.py           # Global constants for STT/TTS (sample rates, channels, latencies)
```

---

## Usage Example (CRUD & Similarity Search)

```python
from sqlmodel import Session
from cortex_cm.pg import engine, UserKnowledgeBase
from cortex_cm.pg.req import get_similar

# Search for traits similar to a generated query embedding
with Session(engine) as session:
    results = get_similar(
        session=session,
        model=UserKnowledgeBase,
        query_embedding=[0.1, 0.2, -0.5, ...],
        metric="cosine",
        top_k=3,
        user_id="11111111-1111-1111-1111-111111111111"
    )

for trait, similarity_score in results:
    print(f"Trait: {trait.content} | Score: {similarity_score}")
```