# Rowboat

**Rowboat** is an AI-powered group outing coordination platform that handles everything end-to-end — from collecting preferences to finding venues, scheduling across calendars, applying constraint-based ranking, and planning. Built as a course project for CMU 24-880 (AI Agents for Engineers) with commercial product aspirations.

**Live demo:** Deployed on Railway with a FastAPI backend and Streamlit frontend.

## Features

### AI Agents
- **Search Agent** — PydanticAI agent that searches Google Places, Yelp, Eventbrite, and Ticketmaster with Gemini fallback for venue recommendations
- **Preference Agent** — Adaptive AI questionnaire that builds user profiles (cuisines, activities, dietary restrictions, budget, dealbreakers, accessibility)
- **Calendar Agent** — Finds time slots where all group members are available, with overnight scheduling support
- **Recommendation Agent** — Combines constraint solving with RAG context for explained, ranked recommendations
- **Orchestrator Agent** — Coordinates all sub-agents autonomously: parses a natural-language request, searches venues, finds available slots, ranks against constraints, and produces a final itinerary ("one-click planning")

### Authentication & Social
- **Multi-provider sign-in** — Google OAuth (with calendar scope) or email/password registration
- **JWT sessions** — Stateless auth with 7-day token expiry
- **Usernames** — Optional unique usernames for friend discovery
- **Friends system** — Send/accept friend requests by username or email, quick-add friends to groups

### Constraint Solver
- **Hard constraints** (instant reject): Budget limit, dietary restrictions, dealbreakers
- **Soft constraints** (weighted 0-100%): Cuisine match (25%), activity match (20%), group consensus (20%), rating (15%), popularity (10%), neighborhood (10%)
- Score badges on each venue card: green (>=70%), orange (>=40%), red (<40%)
- Rejected venues shown faded with violation explanation

### RAG Pipeline (ChromaDB)
- **Venue Knowledge Base** — Every search indexes venues for future semantic retrieval
- **Feedback Memory** — Post-outing feedback indexed for learning from past outings
- **Semantic Search** — Natural language queries like "Find places like the bowling alley we went to last time"

### UI/UX (Kayak-Inspired)
- **Auth gate** — Google sign-in, email login, or email registration with optional username setup
- **Single-page stepper** with 7 steps: Create Group → Preferences → Calendar → Find Venues → Review & Plan → Plan Summary → Feedback
- **Interactive ranking** with gold/silver/bronze highlights
- **Review & Plan** with unified group calendar overlay, Google Maps embed, per-venue time slot dropdown, and deep links to reserve via Google Maps / Yelp
- **Plan Summary** with cost breakdown and calendar invite dispatch
- Light theme (`#FAFBFC`), orange accent (`#FF690F`), green success (`#1DB954`)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **AI Agents** | [PydanticAI](https://ai.pydantic.dev/) with `google-gla:gemini-2.5-flash` |
| **Backend** | FastAPI with async routers (auth, plans, groups, friends, preferences, calendar) |
| **Frontend** | Streamlit single-page app with stepper navigation |
| **Auth** | JWT via `python-jose`, password hashing via `passlib[bcrypt]`, Google OAuth 2.0 |
| **Persistence** | SQLAlchemy async + aiosqlite (SQLite) |
| **Vector DB** | ChromaDB for RAG knowledge base |
| **Venue Search** | Google Places, Yelp Fusion, Eventbrite, Ticketmaster APIs |
| **Calendar** | Google Calendar API (OAuth, free/busy, event creation) |
| **Maps** | Google Maps Embed API |
| **Deployment** | Railway (two services: FastAPI backend + Streamlit frontend) |
| **Testing** | pytest + pytest-asyncio + respx (69 tests) |

## Model Selection & Justification

All five PydanticAI agents use **Gemini 2.5 Flash** (`google-gla:gemini-2.5-flash`). This is a deliberate single-model choice for the MVP:

| Agent | Why Gemini 2.5 Flash fits |
|-------|--------------------------|
| **Search** | Needs to turn natural-language queries into structured API parameters. Flash handles this well with low latency — critical since we fire 4 venue APIs in parallel and need the LLM step to be fast. |
| **Preference** | Generates adaptive follow-up questions from partial user profiles. Conversational and low-stakes; a lightweight model is ideal. |
| **Calendar** | Parses date/time expressions and structures them. The heavy lifting (slot-finding, overlap detection) is deterministic Python — the LLM just handles NL parsing. |
| **Recommendation** | The most reasoning-intensive agent: combines constraint scores with RAG context to produce explained rankings. Flash's reasoning is sufficient here because the constraint solver already does the quantitative work; the LLM explains and narrates. |
| **Orchestrator** | In practice uses a deterministic pipeline (`_fallback_orchestration`) that sequences the other agents without an LLM call. The `Agent` object exists for future use but isn't invoked in the main flow. |

**Why not a larger model (e.g., Gemini 2.5 Pro)?** The bottleneck in Rowboat is latency, not reasoning depth. Users are waiting for a real-time stepper UI. Flash gives ~2-5x faster responses than Pro at a fraction of the cost, and the hard reasoning (constraint solving, calendar overlap) is done in deterministic code, not by the LLM.

**Why not a cheaper model (e.g., Gemini 2.0 Flash)?** 2.5 Flash has significantly better structured-output compliance and instruction-following, which matters for PydanticAI's function-calling protocol. The marginal cost difference is negligible at our scale.

**Fallback:** The Search Agent's Google Places tool falls back to a direct Gemini 2.0 Flash REST call (or Claude Haiku if an Anthropic key is set) when the Places API is unavailable. This uses a simpler model since it's just generating venue JSON from general knowledge.

## Architecture

```
+-----------------------------------------------------------+
|                      Streamlit UI                         |
|        (Auth gate → Single-page stepper flow)             |
+----------------------------+------------------------------+
                             | HTTP
+----------------------------v------------------------------+
|                     FastAPI Backend                        |
|  /api/auth  /api/plans  /api/groups  /api/friends         |
|  /api/preferences  /api/calendar  /api/plans/orchestrate  |
+----+--------+----------+--------+--------+---------------+
     |        |          |        |        |
+----v---+ +--v-------+ +v------+ +--v-----------+ +--v-----------+
| Search | |Preference| |Calendar| |Recommendation| |Orchestrator |
| Agent  | |  Agent   | | Agent  | |    Agent     | |   Agent     |
+--+-----+ +----------+ +--------+ +--+----+-----+ +--+----+-----+
   |                                   |    |          |    |
+--v-----------------------------------v----v----------v----v-----+
|                    External APIs / Tools                        |
|  Google Places · Yelp · Eventbrite · Ticketmaster · Gemini     |
+---------+-----------+-----------+------------------------------+
          |           |           |
   +------v---+ +----v-----+ +---v---------+ +---v-----------+
   | ChromaDB | | SQLite   | | Google Maps | | Google        |
   |  (RAG)   | |  (CRUD)  | |  (Embed)    | | Calendar API  |
   +----------+ +----------+ +-------------+ +---------------+
```

## Project Structure

```
src/
├── agents/              # PydanticAI agents (search, preference, calendar, recommendation, orchestrator)
├── api/                 # FastAPI routers (auth, plans, groups, friends, preferences, calendar)
├── constraints/         # Constraint solver (hard + soft constraints)
├── db/                  # SQLAlchemy tables, CRUD, async engine
├── models/              # Pydantic data models (Event, Venue, User, Constraints, etc.)
├── rag/                 # RAG pipeline (ChromaDB venue store + feedback memory)
├── tools/               # External API integrations (Google Places, Yelp, Eventbrite, Ticketmaster, Google Calendar)
├── ui/
│   ├── app.py           # Streamlit single-page app with auth gate + stepper navigation
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
- Google OAuth credentials (for sign-in and calendar integration)

### Setup

```bash
# Clone the repo
git clone git@github.com:barathkrishna777/rowboat.git
cd rowboat

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env and add your API keys (see .env.example for all required variables)

# Start the backend
uvicorn src.main:app --port 8000

# Start the frontend (in another terminal)
streamlit run src/ui/app.py --server.port 8501
```

Open **http://localhost:8501** in your browser.

### Environment Variables

See `.env.example` for the full list. Key variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key for all AI agents |
| `GOOGLE_CLIENT_ID` | Yes | Google OAuth client ID (sign-in + calendar) |
| `GOOGLE_CLIENT_SECRET` | Yes | Google OAuth client secret |
| `JWT_SECRET` | Yes (prod) | Secret for signing JWT tokens |
| `YELP_API_KEY` | Optional | Yelp Fusion API key for venue search |
| `EVENTBRITE_API_KEY` | Optional | Eventbrite API key for event search |
| `TICKETMASTER_API_KEY` | Optional | Ticketmaster API key for event search |
| `GOOGLE_MAPS_EMBED_KEY` | Optional | Google Maps Embed API key for venue maps |
| `API_BASE_URL` | Prod only | Backend URL (e.g., `https://your-backend.up.railway.app`) |
| `UI_BASE_URL` | Prod only | Frontend URL (e.g., `https://your-frontend.up.railway.app`) |

## API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register with email/password |
| POST | `/api/auth/login` | Login with email/password |
| GET | `/api/auth/google/url` | Get Google OAuth sign-in URL |
| GET | `/api/auth/google/callback` | Google OAuth callback |
| GET | `/api/auth/me` | Get current authenticated user |
| POST | `/api/auth/username` | Set/update username |
| GET | `/api/auth/check-username/{username}` | Check username availability |

### Plans
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/plans/search` | Search venues using AI search agent |
| POST | `/api/plans/recommend` | Score and rank venues against group constraints |
| POST | `/api/plans/orchestrate` | Plan an outing end-to-end using the orchestrator |

### Groups
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/groups/` | Create a new group |
| GET | `/api/groups/{id}` | Get group details |
| POST | `/api/groups/{id}/members` | Add member to group |

### Friends
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/friends/request` | Send a friend request (by username or email) |
| POST | `/api/friends/respond` | Accept or reject a friend request |
| GET | `/api/friends/{user_id}` | Get user's friends list |
| GET | `/api/friends/{user_id}/pending` | Get pending friend requests |
| GET | `/api/friends/search` | Search users by username or email |

### Preferences
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/preferences/{user_id}` | Save user preferences |
| GET | `/api/preferences/{user_id}` | Get user preferences |

### Calendar
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/calendar/auth-url` | Get Google Calendar OAuth URL |
| GET | `/api/calendar/callback` | Calendar OAuth callback |
| GET | `/api/calendar/status/{user_id}` | Check if user has connected calendar |
| POST | `/api/calendar/availability` | Find group availability from real calendars |
| POST | `/api/calendar/book` | Create calendar event with invites |

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

- [x] **Phase 1** — Foundation: project structure, models, search agent, API, UI
- [x] **Phase 2** — Preferences, calendar coordination, SQLite persistence
- [x] **Phase 2.5** — UI/UX polish: Kayak-inspired redesign, interactive ranking, maps
- [x] **Phase 3** — Constraint solver, RAG pipeline (ChromaDB), recommendation agent
- [x] **Phase 4** — Real Google Calendar OAuth, auth system (JWT + Google sign-in), friends system
- [x] **Phase 5** — Orchestrator agent to coordinate all sub-agents autonomously
- [x] **Phase 5.5** — Deployment on Railway, honest booking → planning pivot
- [ ] **Phase 6** — Production frontend (React/Next.js), mobile support
- [ ] **Phase 7** — Production hardening: Postgres, CI/CD, monitoring, rate limiting

## Team

Built at **Carnegie Mellon University** for 24-880 AI Agents for Engineers.

- **Barath Krishna S** — CEO & Co-Founder. MS Robotics at CMU, B.Tech at IIT Bombay.
- **Anushree Sabnis** — Co-Founder. MS MechE (Research) at CMU, B.Tech at VJTI.
- **Naitik Khandelwal** — CTO & Co-Founder. MS Engineering at CMU, B.E. at BITS Pilani.

## License

This project is part of an academic course. All rights reserved.
