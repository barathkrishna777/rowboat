# Rowboat Discover/Presets Handoff (for a new LLM chat)

## 1) Product context
Rowboat is an app for coordinating group outings. The web app has a **Discover** flow where users browse swipe cards (`/swipe`) and a planning flow (`/plan`).

The recent work focused on making Discover more intentional:
- Discover entry is now a decision point (vibe vs presets).
- Presets can be built-in or user-created.
- Presets can be favorited.
- Selecting a preset tailors the swipe feed.
- Natural-language preset creation is available (heuristic parser).

---

## 2) Current Discover UX (intended)
- `/discover`: only two cards:
  - **Choose your vibe!**
  - **Presets**
- `/discover/presets`:
  - shows built-in + custom presets
  - heart button toggles favorite (favorites pinned to top)
  - “Use this preset” sends user to `/swipe?preset_id=...`
- `/discover/create`:
  - manual creation path
  - natural-language creation path
- `/discover/create/manual`:
  - preference-style form (cuisine/activity/dietary/budget/dealbreakers)
- `/discover/create/magic`:
  - user enters free text
  - backend parses to structured criteria
  - user reviews/saves generated preset

---

## 3) Backend architecture added/updated

### Data model
- `PresetTable` (`presets`): stores custom presets per user.
- `PresetFavoriteTable` (`preset_favorites`): stores favorites by `(user_id, preset_id)` and supports both built-in + custom IDs.

### Models
- `src/models/preset.py`
  - `PresetCriteria`
  - `Preset`, `PresetCreate`
  - `PresetFavoriteUpdate`
  - `PresetParseRequest`, `PresetParseResponse`

### Built-in catalog
- `src/presets/catalog.py`
  - canonical built-in presets
  - `get_built_in_preset()` lookup helper

### Preset parser + ranking helpers
- `src/presets/agent.py`
  - `parse_natural_language_preset(text)`
  - `rank_hangouts_for_preset(cards, criteria)`
  - currently deterministic keyword/heuristic logic

### API
- `src/api/presets.py`
  - `GET /api/presets`
  - `POST /api/presets`
  - `PATCH /api/presets/{preset_id}/favorite`
  - `POST /api/presets/parse`
- `src/api/hangouts.py`
  - `GET /api/hangouts/feed/me?preset_id=...`
  - applies preset ranking and returns `match_reason`

### App wiring
- `src/main.py` includes presets router at `/api/presets`.

---

## 4) Frontend architecture added/updated
- `web/src/lib/api.ts`
  - `presets.list/create/setFavorite/parse`
  - hangout feed supports optional `presetId`
  - `Hangout.match_reason` typed
- `web/src/app/discover/*`
  - `page.tsx` (intent entry)
  - `presets/page.tsx` (favorite hearts + pinned favorites)
  - `create/page.tsx`
  - `create/manual/page.tsx`
  - `create/magic/page.tsx`
  - `vibe/page.tsx` (still placeholder)
- `web/src/app/swipe/page.tsx`
  - reads `preset_id` query param
  - shows “Why suggested” from backend `match_reason`

---

## 5) Plan status (phases)

## Phase 1 — Discover IA skeleton
**Status:** Done
- Discover entry structure and route scaffolding.

## Phase 2 — Preset domain + manual create
**Status:** Done
- Preset APIs, DB persistence, favorites, manual preset creation.

## Phase 3 — Natural-language creation
**Status:** Done (heuristic implementation)
- Parse endpoint + UI generate/review/save flow.
- Not yet LLM-orchestrator backed.

## Phase 4 — Better preset ranking
**Status:** Done (heuristic implementation)
- Shared ranking helper used in feed.
- Exposes per-card reason string.

## Phase 5 — Vibe flow
**Status:** Not done
- `/discover/vibe` is still placeholder.
- Needs real vibe input UI and mapping to `PresetCriteria`.

## Phase 6 — Swipe animation parity
**Status:** Not done
- Need true swipe animation on button and keyboard actions.

---

## 6) Remaining work (prioritized)
1. **Implement vibe flow**
   - Build UI controls on `/discover/vibe`.
   - Map output to `PresetCriteria`.
   - Optionally allow save as custom preset.
2. **Improve ranking quality beyond keywords**
   - Replace deterministic scorer with orchestrator/LLM-assisted ranking.
   - Keep deterministic fallback for reliability.
3. **Upgrade natural-language parsing**
   - Use orchestrator/LLM extraction into strict schema.
   - Add confidence + ambiguity handling + user correction loop.
4. **Implement swipe animation parity**
   - Same directional animation for click and arrow keys.
5. **Preset management quality-of-life**
   - edit/delete custom presets
   - duplicate built-in to custom
   - optional sharing/export

---

## 7) Known caveats / technical debt
- Current parser/ranker is heuristic and keyword-based; good baseline but not semantically robust.
- No dedicated migration framework changes were added yet for existing deployed DB upgrades (tables are created via metadata init).
- Vibe flow is not implemented yet.
- Swipe interactions currently change card index immediately (no full animated deck transition system yet).

---

## 8) Suggested first prompt for a new LLM
Use this prompt to continue implementation:

> You are joining the Rowboat codebase. Read `docs/LLM_HANDOFF_DISCOVER_PRESETS.md` first, then implement Phase 5 (vibe flow) with a reusable mapping to `PresetCriteria`, and after that implement Phase 6 swipe animation parity for both click and arrow-key actions. Keep API and UI contracts backward compatible.

---

## 9) Quick verification commands
From repo root:

```bash
python -m pytest tests/test_models.py -q
npm --prefix web run build
```

If you need local run:

```bash
npm --prefix web install
npm --prefix web run dev
```
