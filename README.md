# Rowboat

**Rowboat** is an AI-powered group outing coordination platform that handles everything end-to-end -- from collecting preferences to finding venues, scheduling across calendars, applying constraint-based ranking, and booking. Built as a course project for CMU 24-880 (AI Agents for Engineers) with commercial product aspirations.

## Features

### AI Agents
- **Search Agent** -- PydanticAI agent that searches Google Places, Yelp, Eventbrite, and Ticketmaster with Gemini fallback for venue recommendations
- **Preference Agent** -- Adaptive AI questionnaire that builds user profiles (cuisines, activities, dietary restrictions, budget, dealbreakers, accessibility)
- **Calendar Agent** -- Finds time slots where all group members are available, with overnight scheduling support
- **Recommendation Agent** -- Combines constraint solving with RAG context for explained, ranked recommendations
- **Orchestrator Agent** -- Coordinates all sub-agents autonomously: parses a natural-language request, searches venues, finds available slots, ranks against constraints, and produces a final itinerary ("one-click planning")

### Constraint Solver
- **Hard constraints** (instant reject): Budget limit, dietary restrictions, dealbreakers
- **Soft constraints** (weighted 0-100%): Cuisine match (25%), activity match (20%), group consensus (20%), rating (15%), popularity (10%), neighborhood (10%)
- Score badges on each venue card: green (>=70%), orange (>=40%), red (<40%)
- Rejected venues shown faded with violation explanation

### RAG Pipeline (ChromaDB)
- **Venue Knowledge Base** -- Every search indexes venues for future semantic retrieval
- **Feedback Memory** -- Post-outing feedback indexed for learning from past outings
- **Semantic Search** -- Natural language queries like "Find places like the bowling alley we went to last time"

### UI/UX (Kayak-Inspired)
- **Single-page stepper** with 7 steps: Create Group -> Preferences -> Calendar -> Find Venues -> Review & Book -> Booking Summary -> Feedback
- **Interactive ranking** with gold/silver/bronze highlights
- **Review & Book** with unified group calendar overlay, Google Maps embed, per-venue time slot dropdown
- **Booking Summary** with cost breakdown and calendar invite dispatch
- Light theme (`#FAFBFC`), orange accent (`#FF690F`), green success (`#1DB954`)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **AI Agents** | [PydanticAI](https://ai.pydantic.dev/) with `google-gla:gemini-2.5-flash` |
| **Backend** | FastAPI with async routers (plans, groups, preferences, calendar) |
| **Frontend** | Streamlit single-page app with stepper navigation |
| **Persistence** | SQLAlchemy async + aiosqlite (SQLite) |
| **Vector DB** | ChromaDB for RAG knowledge base |
| **Venue Search** | Google Places API with Gemini direct-call fallback |
| **Maps** | Google Maps Embed API |
| **Testing** | pytest + pytest-asyncio + respx (69 tests) |

## Architecture

```
+-----------------------------------------------------------+
|                      Streamlit UI                         |
|             (Single-page stepper flow)                    |
+----------------------------+------------------------------+
                             | HTTP
+----------------------------v------------------------------+
|                     FastAPI Backend                        |
|  /api/plans  /api/groups  /api/preferences                |
|  /api/calendar  /api/plans/recommend  /api/plans/orchestrate |
+----+--------+----------+--------+--------+---------------+
     |        |          |        |        |
+----v---+ +--v-------+ +v------+ +--v-----------+ +--v-----------+
| Search | |Preference| |Calendar| |Recommendation| |Orchestrator |
| Agent  | |  Agent   | | Agent  | |    Agent     | |   Agent     |
+--+-----+ +----------+ +--------+ +--+----+-----+ +--+----+-----+
   |                                   |    |          |    |
+--v-----------------------------------v----v----------v----v-----+
|                    External APIs / Tools                        |
|       Google Places . Yelp . Eventbrite . Gemini               |
+---------+-----------+-----------+------------------------------+
          |           |           |
   +------v---+ +----v-----+ +---v---------+
   | ChromaDB | | SQLite   | | Google Maps |
   |  (RAG)   | |  (CRUD)  | |  (Embed)    |
   +----------+ +----------+ +-------------+
```

## Project Structure

```
src/
├── agents/              # PydanticAI agents (search, preference, calendar, recommendation, orchestrator)
├── api/                 # FastAPI routers (plans, groups, preferences, calendar)
├── constraints/         # Constraint solver (hard + soft constraints)
├── db/                  # SQLAlchemy tables, CRUD, async engine
├── models/              # Pydantic data models (Event, Venue, Constraints, etc.)
├── rag/                 # RAG pipeline (ChromaDB venue store + feedback memory)
├── tools/               # External API integrations (Google Places, Yelp, etc.)
├── ui/
│   ├── app.py           # Streamlit single-page app with stepper navigation
│   └── pages/           # Step pages (create group, preferences, calendar, plan, review, feedback)
├── config.py            # Settings via pydantic-settings
└── main.py              # FastAPI app entrypoint
tests/
├── test_constraints.py  # Constraint solver tests (27 tests)
├── test_db.py           # Database CRUD tests (9 tests)
├── test_models.py       # Model validation tests (15 tests)
├── test_orchestrator.py # Orchestrator agent tests (5 tests)
├── test_tools/
│   ├── test_calendar.py # Calendar availability tests (8 tests)
│   └── test_yelp.py     # Yelp API tests (5 tests)
```

## Quick Start

### Prerequisites
- Python 3.11+
- A [Gemini API key](https://aistudio.google.com/apikey) (Tier 1 recommended)

### Setup

```bash
# Clone the repo
git clone git@github.com:barathkrishna777/rowboat.git
cd rowboat

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY and GOOGLE_MAPS_EMBED_KEY

# Start the backend
uvicorn src.main:app --port 8000

# Start the frontend (in another terminal)
streamlit run src/ui/app.py --server.port 8501
```

Open **http://localhost:8501** in your browser.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/plans/search` | Search venues using AI search agent |
| POST | `/api/plans/recommend` | Score and rank venues against group constraints |
| POST | `/api/plans/orchestrate` | Plan an outing end-to-end using the orchestrator agent |
| POST | `/api/groups/` | Create a new group |
| GET | `/api/groups/{id}` | Get group details |
| POST | `/api/groups/{id}/members` | Add member to group |
| POST | `/api/preferences/{user_id}` | Save user preferences |
| GET | `/api/preferences/{user_id}` | Get user preferences |
| POST | `/api/calendar/availability` | Check group availability |

## Development

```bash
# Run tests (69 tests)
pytest

# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/
```

## Roadmap

- [x] **Phase 1** -- Foundation: project structure, models, search agent, API, UI
- [x] **Phase 2** -- Preferences, calendar coordination, SQLite persistence
- [x] **Phase 2.5** -- UI/UX polish: Kayak-inspired redesign, interactive ranking, maps
- [x] **Phase 3** -- Constraint solver, RAG pipeline (ChromaDB), recommendation agent
- [ ] **Phase 4** -- Real Google Calendar OAuth + live booking integrations
- [x] **Phase 5** -- Orchestrator agent to coordinate all sub-agents autonomously
- [ ] **Phase 6** -- Production hardening, deployment, analytics dashboard

## Team

Built by students at **Carnegie Mellon University** for the 24-880 AI Agents for Engineers course.

## License

This project is part of an academic course. All rights reserved.
