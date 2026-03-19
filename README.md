# 🎯 Rowboat — AI-Powered Group Outing Planner

**Rowboat** is a multi-agent AI system that coordinates group outings end-to-end — from collecting preferences to finding venues, scheduling across calendars, and booking. Built as a course project for CMU 24-880 (AI Agents for Engineers) with commercial product aspirations.

## Features

- **Smart Preference Collection** — AI-driven questionnaire that learns each member's cuisine, activity, budget, and accessibility preferences
- **Calendar Coordination** — Finds time slots where all group members are available, with support for overnight scheduling
- **AI Venue Search** — PydanticAI agent searches Google Places (with Gemini fallback) for venue recommendations matching group preferences
- **Interactive Ranking** — Rank time slots and venues by preference with visual gold/silver/bronze highlights
- **Review & Book** — Side-by-side itinerary view with unified group calendar overlay and Google Maps embed
- **Booking Summary** — Confirmation page with cost breakdown and calendar invite dispatch
- **Feedback Loop** — Post-outing ratings to improve future recommendations

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **AI Agents** | [PydanticAI](https://docs.pydantic.dev/latest/concepts/agents/) v1.70 with `google-gla:gemini-2.5-flash` |
| **Backend** | FastAPI with async routers (plans, groups, preferences, calendar) |
| **Frontend** | Streamlit single-page app with stepper navigation |
| **Persistence** | SQLAlchemy async + aiosqlite (SQLite) |
| **Venue Search** | Google Places API with Gemini direct-call fallback |
| **Maps** | Google Maps Embed API |
| **Testing** | pytest + pytest-asyncio + respx |

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  Streamlit UI                    │
│         (Single-page stepper flow)              │
└──────────────────────┬──────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────┐
│                  FastAPI Backend                 │
│   /api/plans  /api/groups  /api/preferences     │
│                /api/calendar                     │
└──────┬───────────┬───────────┬──────────────────┘
       │           │           │
┌──────▼──┐  ┌─────▼────┐  ┌──▼──────────┐
│ Search  │  │Preference│  │  Calendar   │
│  Agent  │  │  Agent   │  │   Agent     │
└──┬──────┘  └──────────┘  └─────────────┘
   │
┌──▼──────────────────────────────────────────────┐
│              External APIs / Tools              │
│  Google Places · Yelp · Eventbrite · Gemini     │
└─────────────────────────────────────────────────┘
```

## Project Structure

```
src/
├── agents/              # PydanticAI agents (search, preference, calendar)
├── api/                 # FastAPI routers
├── db/                  # SQLAlchemy tables, CRUD, async engine
├── models/              # Pydantic data models (Event, Venue, etc.)
├── tools/               # External API integrations (Google Places, Yelp, etc.)
├── ui/                  # Streamlit single-page app
├── rag/                 # RAG pipeline (Phase 3)
├── constraints/         # Constraint solver (Phase 3)
├── config.py            # Settings via pydantic-settings
└── main.py              # FastAPI app entrypoint
tests/
├── test_tools/          # Tool integration tests
├── test_agents/         # Agent unit tests
├── test_db.py           # Database CRUD tests
└── test_models.py       # Model validation tests
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
# Edit .env and add your GEMINI_API_KEY

# Start the backend
uvicorn src.main:app --port 8000

# Start the frontend (in another terminal)
streamlit run src/ui/app.py --server.port 8501
```

Open **http://localhost:8501** in your browser.

## Design Philosophy

Inspired by [Kayak's](https://www.kayak.com) clean, bright UI:
- **Light theme** with `#FAFBFC` background
- **Orange accent** (`#FF690F`) for primary actions
- **Green highlights** (`#1DB954`) for success states
- Card-based layout with smooth transitions and visual hierarchy

## Development

```bash
# Run tests
pytest

# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/
```

## Roadmap

- [x] **Phase 1** — Foundation: project structure, models, search agent, API, UI
- [x] **Phase 2** — Preferences, calendar coordination, SQLite persistence
- [x] **Phase 2.5** — UI/UX polish: Kayak-inspired redesign, interactive ranking, maps
- [ ] **Phase 3** — RAG pipeline + constraint solver for smarter recommendations
- [ ] **Phase 4** — Real Google Calendar OAuth + live booking integrations
- [ ] **Phase 5** — Orchestrator agent to coordinate all sub-agents autonomously
- [ ] **Phase 6** — Production hardening, deployment, analytics dashboard

## Team

Built by students at **Carnegie Mellon University** for the 24-880 AI Agents for Engineers course.

## License

This project is part of an academic course. All rights reserved.
