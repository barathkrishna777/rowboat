"""Streamlit UI for the Group Outing Planner — single-page stepper flow."""

import streamlit as st
import httpx
import random
from datetime import datetime, timedelta, time as dt_time

API_BASE = "http://localhost:8000/api"

# ── Page Config ────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Outing Planner",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Kayak-Inspired Theme ──────────────────────────────────────────────

st.markdown("""
<style>
    /* ── Global ─────────────────────────────────────── */
    .stApp { background-color: #FAFBFC; }
    section[data-testid="stSidebar"] { display: none; }

    /* ── Stepper Nav ────────────────────────────────── */
    .stepper-container {
        display: flex; justify-content: center; gap: 0;
        padding: 16px 2rem 24px 2rem; background: white;
        border-bottom: 2px solid #F0F2F5; margin: -1rem -1rem 2rem -1rem;
    }
    .step-item {
        display: flex; align-items: center; gap: 8px;
        padding: 10px 18px; border-radius: 30px; font-size: 14px;
        font-weight: 500; color: #8E99A4; cursor: default;
        transition: all 0.2s ease; white-space: nowrap;
    }
    .step-item.active {
        background: #FF690F; color: white; font-weight: 600;
        box-shadow: 0 2px 8px rgba(255, 105, 15, 0.3);
    }
    .step-item.completed {
        background: #E8F8EE; color: #1DB954; cursor: pointer; font-weight: 600;
    }
    .step-item.completed:hover { background: #D0F0DB; }
    .step-number {
        width: 26px; height: 26px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 13px; font-weight: 700; flex-shrink: 0;
    }
    .step-item.active .step-number { background: rgba(255,255,255,0.25); color: white; }
    .step-item.completed .step-number { background: #1DB954; color: white; }
    .step-item:not(.active):not(.completed) .step-number { background: #E4E8EC; color: #8E99A4; }
    .step-connector { width: 30px; height: 2px; background: #E4E8EC; align-self: center; flex-shrink: 0; }
    .step-connector.done { background: #1DB954; }

    /* ── Section Cards ──────────────────────────────── */
    .section-card {
        background: white; border-radius: 16px; padding: 2rem 2.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
        margin-bottom: 1.5rem; border: 1px solid #F0F2F5;
    }
    .section-title { font-size: 28px; font-weight: 700; color: #192024; margin-bottom: 4px; }
    .section-subtitle { font-size: 16px; color: #6B7785; margin-bottom: 24px; }

    /* ── Buttons ─────────────────────────────────────── */
    .stButton > button[kind="primary"], .stFormSubmitButton > button {
        background-color: #FF690F !important; color: white !important;
        border: none !important; border-radius: 8px !important;
        padding: 0.6rem 2rem !important; font-weight: 600 !important;
        font-size: 15px !important; transition: all 0.2s ease !important;
    }
    .stFormSubmitButton > button:hover, .stButton > button[kind="primary"]:hover {
        background-color: #E85A00 !important;
        box-shadow: 0 4px 12px rgba(255, 105, 15, 0.35) !important;
    }

    /* ── Venue Cards ─────────────────────────────────── */
    .venue-card {
        background: white; border: 1px solid #E8ECF0; border-radius: 12px;
        padding: 1.2rem 1.5rem; margin-bottom: 0.8rem; transition: all 0.2s ease;
    }
    .venue-card:hover { border-color: #FF690F; box-shadow: 0 2px 8px rgba(255,105,15,0.12); }
    .venue-card.selected { border-color: #FF690F; border-width: 2px; background: #FFF9F5; }
    .venue-name { font-size: 18px; font-weight: 600; color: #192024; }
    .venue-meta { font-size: 14px; color: #6B7785; }
    .venue-badge {
        display: inline-block; background: #FFF3EB; color: #FF690F;
        padding: 2px 10px; border-radius: 12px; font-size: 12px;
        font-weight: 600; margin-right: 6px;
    }
    .price-badge {
        display: inline-block; background: #E8F8EE; color: #1DB954;
        padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 600;
    }
    .rank-badge {
        display: inline-flex; align-items: center; justify-content: center;
        width: 28px; height: 28px; border-radius: 50%; font-size: 14px;
        font-weight: 700; margin-right: 8px; flex-shrink: 0;
    }
    .rank-1 { background: #FFD700; color: #192024; }
    .rank-2 { background: #C0C0C0; color: #192024; }
    .rank-3 { background: #CD7F32; color: white; }
    .rank-other { background: #E4E8EC; color: #6B7785; }

    /* ── Member Chips ────────────────────────────────── */
    .member-chip {
        display: inline-flex; align-items: center; gap: 6px;
        background: #F5F7FA; border: 1px solid #E4E8EC; border-radius: 20px;
        padding: 6px 14px; margin: 4px; font-size: 14px; color: #363F45;
    }
    .member-chip .dot { width: 8px; height: 8px; border-radius: 50%; background: #1DB954; }

    /* ── Calendar Overlay ────────────────────────────── */
    .cal-overlay {
        background: white; border: 1px solid #E8ECF0; border-radius: 12px;
        padding: 1rem; margin-bottom: 1rem;
    }
    .cal-header { font-size: 16px; font-weight: 700; color: #192024; margin-bottom: 12px; }
    .cal-hour-row { display: flex; align-items: stretch; height: 32px; margin-bottom: 2px; }
    .cal-hour-label {
        width: 50px; font-size: 11px; color: #8E99A4; text-align: right;
        padding-right: 8px; padding-top: 2px; flex-shrink: 0;
    }
    .cal-hour-bar { flex: 1; border-radius: 4px; position: relative; }
    .cal-free { background: #F5F7FA; }
    .cal-busy { background: #FFE0E0; }
    .cal-chosen { background: #FF690F; opacity: 0.85; }
    .cal-busy-label {
        font-size: 10px; color: #B04040; padding: 2px 6px;
        position: absolute; top: 50%; transform: translateY(-50%);
    }
    .cal-chosen-label {
        font-size: 10px; color: white; font-weight: 600; padding: 2px 6px;
        position: absolute; top: 50%; transform: translateY(-50%);
    }

    /* ── Map Placeholder ─────────────────────────────── */
    .map-overlay {
        background: white; border: 1px solid #E8ECF0; border-radius: 12px;
        padding: 1rem; text-align: center; min-height: 200px;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
    }
    .map-pin { font-size: 36px; margin-bottom: 8px; }
    .map-name { font-size: 16px; font-weight: 600; color: #192024; }
    .map-addr { font-size: 13px; color: #6B7785; margin-top: 4px; }

    /* ── Form Inputs ─────────────────────────────────── */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        border-radius: 8px !important; border-color: #E4E8EC !important;
    }
    .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
        border-color: #FF690F !important; box-shadow: 0 0 0 1px #FF690F !important;
    }

    /* ── Hide Streamlit chrome ────────────────────────── */
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}

    /* ── Hero ─────────────────────────────────────────── */
    .hero { text-align: center; padding: 1rem 0 0.5rem 0; }
    .hero h1 { font-size: 32px; font-weight: 800; color: #192024; margin-bottom: 0; }
    .hero-accent { color: #FF690F; }
    .hero p { color: #6B7785; font-size: 16px; }
</style>
""", unsafe_allow_html=True)

# ── Session State Init ─────────────────────────────────────────────────

STEPS = ["Create Group", "Preferences", "Calendar", "Find Venues", "Review & Book", "Feedback"]

if "current_step" not in st.session_state:
    st.session_state.current_step = 0
if "group_id" not in st.session_state:
    st.session_state.group_id = None
    st.session_state.user_id = None
    st.session_state.members = []
if "completed_steps" not in st.session_state:
    st.session_state.completed_steps = set()
if "member_add_counter" not in st.session_state:
    st.session_state.member_add_counter = 0


def advance_step():
    st.session_state.completed_steps.add(st.session_state.current_step)
    if st.session_state.current_step < len(STEPS) - 1:
        st.session_state.current_step += 1


def go_to_step(idx):
    if idx in st.session_state.completed_steps or idx == st.session_state.current_step:
        st.session_state.current_step = idx


# ── Hero + Stepper ─────────────────────────────────────────────────────

st.markdown("""
<div class="hero">
    <h1>🎯 <span class="hero-accent">Outing</span> Planner</h1>
    <p>AI-powered group outing coordination — from preferences to booking</p>
</div>
""", unsafe_allow_html=True)


def render_stepper():
    current = st.session_state.current_step
    completed = st.session_state.completed_steps
    html = '<div class="stepper-container">'
    for i, name in enumerate(STEPS):
        if i > 0:
            html += f'<div class="step-connector {"done" if i - 1 in completed else ""}"></div>'
        cls = "active" if i == current else ("completed" if i in completed else "")
        check = "✓" if i in completed else str(i + 1)
        html += f'<div class="step-item {cls}"><span class="step-number">{check}</span>{name}</div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


render_stepper()

# Nav buttons for completed steps
completed = st.session_state.completed_steps
if completed:
    cols = st.columns(len(STEPS))
    for i in range(len(STEPS)):
        if i in completed and i != st.session_state.current_step:
            with cols[i]:
                if st.button(f"← {STEPS[i]}", key=f"nav_{i}", use_container_width=True):
                    go_to_step(i)
                    st.rerun()

step = st.session_state.current_step


# ════════════════════════════════════════════════════════════════════════
# STEP 0: CREATE GROUP
# ════════════════════════════════════════════════════════════════════════
if step == 0:
    st.markdown('<div class="section-card"><div class="section-title">Create Your Group</div>'
                '<div class="section-subtitle">Start by naming your group and adding your friends</div></div>',
                unsafe_allow_html=True)

    if st.session_state.group_id is None:
        with st.form("create_group"):
            col1, col2 = st.columns(2)
            with col1:
                group_name = st.text_input("Group Name", placeholder="Friday Night Crew")
                your_name = st.text_input("Your Name", placeholder="John Doe")
            with col2:
                your_email = st.text_input("Your Email", placeholder="john@example.com")
            submitted = st.form_submit_button("Create Group")
            if submitted and group_name and your_name and your_email:
                try:
                    resp = httpx.post(f"{API_BASE}/groups/",
                                     json={"name": group_name, "creator_name": your_name, "creator_email": your_email})
                    resp.raise_for_status()
                    data = resp.json()
                    st.session_state.group_id = data["id"]
                    st.session_state.user_id = data["member_ids"][0]
                    st.session_state.members = [{"name": your_name, "email": your_email}]
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        # Show members
        members_html = "".join(
            f'<span class="member-chip"><span class="dot"></span>{m["name"]}</span>'
            for m in st.session_state.members
        )
        st.markdown(f"**Group Members:** {members_html}", unsafe_allow_html=True)

        # [FIX 1] Use counter-keyed form so fields clear after each add
        form_key = f"add_member_{st.session_state.member_add_counter}"
        with st.form(form_key):
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                name = st.text_input("Name", placeholder="Friend's name")
            with c2:
                email = st.text_input("Email", placeholder="friend@email.com")
            with c3:
                st.write("")
                add = st.form_submit_button("Add")
            if add and name and email:
                try:
                    resp = httpx.post(f"{API_BASE}/groups/{st.session_state.group_id}/members",
                                     json={"name": name, "email": email})
                    resp.raise_for_status()
                    st.session_state.members.append({"name": name, "email": email})
                    st.session_state.member_add_counter += 1  # new form key = cleared fields
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        st.divider()
        col1, col2 = st.columns([3, 1])
        with col2:
            if len(st.session_state.members) >= 1:
                if st.button("Continue →", type="primary", use_container_width=True):
                    advance_step()
                    st.rerun()


# ════════════════════════════════════════════════════════════════════════
# STEP 1: PREFERENCES
# ════════════════════════════════════════════════════════════════════════
elif step == 1:
    st.markdown('<div class="section-card"><div class="section-title">Set Preferences</div>'
                '<div class="section-subtitle">Tell us what everyone enjoys so we can find the perfect outing</div></div>',
                unsafe_allow_html=True)

    CUISINE_OPTIONS = ["Italian", "Japanese", "Mexican", "Chinese", "Indian", "Thai",
                       "Korean", "American", "Mediterranean", "French", "Vietnamese", "Ethiopian"]
    ACTIVITY_OPTIONS = ["Bowling", "Escape Room", "Concert", "Movie", "Hiking", "Karaoke",
                        "Board Games", "Mini Golf", "Arcade", "Museum", "Comedy Show", "Sports Event"]
    DIETARY_OPTIONS = ["None", "Vegetarian", "Vegan", "Gluten Free", "Halal", "Kosher",
                       "Nut Allergy", "Dairy Free", "Shellfish Allergy"]
    BUDGET_OPTIONS = ["$ (Under $15)", "$$ ($15-40)", "$$$ ($40-80)", "$$$$ ($80+)"]

    with st.form("preferences_form"):
        col1, col2 = st.columns(2)
        with col1:
            cuisines = st.multiselect("🍽️ Favorite Cuisines", CUISINE_OPTIONS)
            dietary = st.multiselect("⚕️ Dietary Restrictions", DIETARY_OPTIONS, default=["None"])
            budget = st.select_slider("💰 Budget per Person", options=BUDGET_OPTIONS, value=BUDGET_OPTIONS[1])
        with col2:
            activities = st.multiselect("🎮 Favorite Activities", ACTIVITY_OPTIONS)
            neighborhoods = st.text_input("📍 Preferred Neighborhoods", placeholder="Oakland, Shadyside, Squirrel Hill")
            dealbreakers = st.text_area("🚫 Dealbreakers", placeholder="No loud places\nMust have parking", height=100)
        submitted = st.form_submit_button("Save Preferences & Continue →")
        if submitted:
            budget_map = {BUDGET_OPTIONS[0]: "$", BUDGET_OPTIONS[1]: "$$", BUDGET_OPTIONS[2]: "$$$", BUDGET_OPTIONS[3]: "$$$$"}
            st.session_state["user_preferences"] = {
                "cuisine_preferences": [c.lower() for c in cuisines],
                "activity_preferences": [a.lower() for a in activities],
                "dietary_restrictions": [d.lower().replace(" ", "_") for d in dietary if d != "None"],
                "budget_max": budget_map[budget],
                "dealbreakers": [d.strip() for d in dealbreakers.split("\n") if d.strip()],
                "preferred_neighborhoods": [n.strip() for n in neighborhoods.split(",") if n.strip()],
            }
            advance_step()
            st.rerun()


# ════════════════════════════════════════════════════════════════════════
# STEP 2: CALENDAR
# ════════════════════════════════════════════════════════════════════════
elif step == 2:
    st.markdown('<div class="section-card"><div class="section-title">Find Availability</div>'
                '<div class="section-subtitle">Connect calendars and set time constraints to find when everyone is free</div></div>',
                unsafe_allow_html=True)

    if "calendars_connected" not in st.session_state:
        st.session_state.calendars_connected = {}

    members = st.session_state.get("members", [])
    all_connected = all(st.session_state.calendars_connected.get(m["name"], False) for m in members)

    # Calendar connection
    st.subheader("📅 Connect Calendars")
    for member in members:
        name = member["name"]
        connected = st.session_state.calendars_connected.get(name, False)
        col1, col2 = st.columns([4, 1])
        with col1:
            if connected:
                st.markdown(f'<span class="member-chip"><span class="dot"></span>{name} — Connected</span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<span class="member-chip">{name} — Not connected</span>', unsafe_allow_html=True)
        with col2:
            if not connected:
                if st.button("Connect", key=f"cal_{name}"):
                    st.session_state.calendars_connected[name] = True
                    st.rerun()

    # [FIX 2] Connect All button
    if not all_connected:
        if st.button("🔗 Connect All Calendars", type="primary"):
            for m in members:
                st.session_state.calendars_connected[m["name"]] = True
            st.rerun()

    st.divider()

    # Date range + [FIX 3] Time constraints
    st.subheader("🕐 Date & Time Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Search from", value=datetime.now().date() + timedelta(days=1))
        earliest_time = st.time_input("Earliest start time", value=dt_time(17, 0))
    with col2:
        end_date = st.date_input("Search to", value=datetime.now().date() + timedelta(days=7))
        latest_time = st.time_input("Latest end time", value=dt_time(23, 0))

    min_hours = st.slider("Minimum outing duration (hours)", 1, 6, 2)

    if st.button("🔍 Find Available Times", type="primary"):
        slots = []
        current = datetime.combine(start_date, datetime.min.time())
        end = datetime.combine(end_date, datetime.min.time())
        while current <= end:
            if current.weekday() >= 5:  # Weekend: start earlier
                slot_start_hour = max(earliest_time.hour, 12)
            else:  # Weekday: evening
                slot_start_hour = max(earliest_time.hour, 17)
            slot_end_hour = latest_time.hour

            if slot_end_hour - slot_start_hour >= min_hours:
                # Generate simulated busy periods for calendar overlay
                busy_per_member = {}
                for m in members:
                    # Simulate 0-2 busy blocks per person
                    member_busy = []
                    for _ in range(random.randint(0, 2)):
                        bh = random.randint(slot_start_hour, max(slot_start_hour, slot_end_hour - 2))
                        member_busy.append({"start": bh, "end": min(bh + random.randint(1, 2), slot_end_hour)})
                    busy_per_member[m["name"]] = member_busy

                slots.append({
                    "start": current.replace(hour=slot_start_hour).isoformat(),
                    "end": current.replace(hour=slot_end_hour).isoformat(),
                    "users": [m["name"] for m in members],
                    "busy_per_member": busy_per_member,
                })
            current += timedelta(days=1)
        st.session_state["available_slots"] = slots
        st.session_state.pop("slot_rankings", None)

    # Display slots + [FIX 4] Preference ranking
    if "available_slots" in st.session_state:
        slots = st.session_state["available_slots"]
        st.subheader(f"Found {len(slots)} time slots")

        if len(slots) == 1:
            st.info("Only one slot available — it's automatically selected.")
            st.session_state["slot_rankings"] = [0]
        elif len(slots) == 2:
            st.markdown("**Rank these 2 slots by preference** (drag to reorder or pick your #1):")
            pref = st.radio("Which slot do you prefer?",
                            [f"{datetime.fromisoformat(s['start']).strftime('%A, %b %d %I:%M %p')} - "
                             f"{datetime.fromisoformat(s['end']).strftime('%I:%M %p')}" for s in slots],
                            key="slot_pref_radio")
            idx = [f"{datetime.fromisoformat(s['start']).strftime('%A, %b %d %I:%M %p')} - "
                   f"{datetime.fromisoformat(s['end']).strftime('%I:%M %p')}" for s in slots].index(pref)
            st.session_state["slot_rankings"] = [idx, 1 - idx]
        else:
            st.markdown(f"**Rank your top {min(3, len(slots))} preferred time slots:**")
            if "slot_rankings" not in st.session_state:
                st.session_state["slot_rankings"] = []

            slot_labels = []
            for i, s in enumerate(slots):
                start_dt = datetime.fromisoformat(s["start"])
                end_dt = datetime.fromisoformat(s["end"])
                slot_labels.append(f"{start_dt.strftime('%A, %b %d')}  {start_dt.strftime('%I:%M %p')}-{end_dt.strftime('%I:%M %p')}")

            for rank in range(min(3, len(slots))):
                already_picked = st.session_state.get("slot_rankings", [])[:rank]
                remaining = [i for i in range(len(slots)) if i not in already_picked]
                options = ["-- Select --"] + [slot_labels[i] for i in remaining]
                choice = st.selectbox(
                    f"{'🥇 1st' if rank == 0 else '🥈 2nd' if rank == 1 else '🥉 3rd'} choice",
                    options, key=f"slot_rank_{rank}")
                if choice != "-- Select --":
                    chosen_idx = slot_labels.index(choice)
                    if len(st.session_state.get("slot_rankings", [])) <= rank:
                        rankings = list(st.session_state.get("slot_rankings", []))
                        rankings.append(chosen_idx)
                        st.session_state["slot_rankings"] = rankings

        # Show ranked slots
        rankings = st.session_state.get("slot_rankings", [])
        if rankings:
            st.divider()
            for rank, idx in enumerate(rankings):
                s = slots[idx]
                start_dt = datetime.fromisoformat(s["start"])
                end_dt = datetime.fromisoformat(s["end"])
                rank_cls = f"rank-{rank+1}" if rank < 3 else "rank-other"
                st.markdown(f"""<div class="venue-card">
                    <span class="rank-badge {rank_cls}">{rank+1}</span>
                    <span class="venue-name">{start_dt.strftime('%A, %b %d')}</span><br>
                    <span class="venue-meta">{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')} — {', '.join(s['users'])}</span>
                </div>""", unsafe_allow_html=True)

        st.divider()
        col1, col2 = st.columns([3, 1])
        with col2:
            can_continue = len(rankings) >= min(3, len(slots)) if len(slots) >= 3 else len(rankings) >= len(slots)
            if can_continue:
                if st.button("Continue →", type="primary", key="cal_continue", use_container_width=True):
                    advance_step()
                    st.rerun()
            else:
                st.info(f"Pick {'3 slots' if len(slots) >= 3 else 'your preferences'} to continue")


# ════════════════════════════════════════════════════════════════════════
# STEP 3: FIND VENUES
# ════════════════════════════════════════════════════════════════════════
elif step == 3:
    st.markdown('<div class="section-card"><div class="section-title">Find Venues</div>'
                '<div class="section-subtitle">Tell us what you\'re looking for and our AI will search for the best options</div></div>',
                unsafe_allow_html=True)

    with st.form("plan_search"):
        query = st.text_area("What are you looking for?",
                             placeholder="Italian dinner followed by bowling or an escape room. Budget around $30/person.",
                             height=100)
        col1, col2 = st.columns(2)
        with col1:
            location = st.text_input("Location", value="Pittsburgh, PA")
        with col2:
            max_results = st.slider("Max results", 3, 20, 8)
        submitted = st.form_submit_button("🔍  Search Venues")

    if submitted and query:
        with st.spinner("AI agent is searching for venues..."):
            try:
                resp = httpx.post(f"{API_BASE}/plans/search",
                                 json={"query": query, "location": location, "max_results": max_results},
                                 timeout=60.0)
                resp.raise_for_status()
                st.session_state["search_result"] = resp.json()
                st.session_state.pop("venue_rankings", None)
            except Exception as e:
                st.error(f"Search failed: {e}")

    if "search_result" in st.session_state:
        result = st.session_state["search_result"]
        if result.get("summary"):
            st.info(result["summary"])

        venues = result.get("venues", [])
        if venues:
            # [FIX 5] Venue preference ranking
            st.subheader(f"{len(venues)} venues found — rank your top {min(3, len(venues))}")

            venue_labels = []
            for v in venues:
                price = v.get("price_tier", "")
                rating = f"⭐{v['rating']}" if v.get("rating") else ""
                venue_labels.append(f"{v['name']} {price} {rating}")

            # Show all venues
            for i, venue in enumerate(venues):
                cats = venue.get("categories", [])
                badges = "".join(f'<span class="venue-badge">{c}</span>' for c in cats[:3])
                price_html = f'<span class="price-badge">{venue.get("price_tier", "")}</span>' if venue.get("price_tier") else ""
                rating_stars = "⭐" * int(venue.get("rating", 0)) if venue.get("rating") else ""
                st.markdown(f"""<div class="venue-card">
                    <span class="venue-name">{venue['name']}</span> {price_html}<br>
                    <span class="venue-meta">{venue.get('address', '')} {rating_stars}</span><br>
                    {badges}
                </div>""", unsafe_allow_html=True)

            st.divider()
            st.subheader("Rank Your Favorites")

            for rank in range(min(3, len(venues))):
                already = st.session_state.get("venue_rankings", [])[:rank]
                remaining = [i for i in range(len(venues)) if i not in already]
                options = ["-- Select --"] + [venue_labels[i] for i in remaining]
                choice = st.selectbox(
                    f"{'🥇 1st' if rank == 0 else '🥈 2nd' if rank == 1 else '🥉 3rd'} choice venue",
                    options, key=f"venue_rank_{rank}")
                if choice != "-- Select --":
                    chosen_idx = venue_labels.index(choice)
                    rankings = list(st.session_state.get("venue_rankings", []))
                    if len(rankings) <= rank:
                        rankings.append(chosen_idx)
                        st.session_state["venue_rankings"] = rankings

            st.divider()
            col1, col2 = st.columns([3, 1])
            with col2:
                vr = st.session_state.get("venue_rankings", [])
                needed = min(3, len(venues))
                if len(vr) >= needed:
                    if st.button("Continue to Review →", type="primary", key="venue_continue", use_container_width=True):
                        advance_step()
                        st.rerun()
                else:
                    st.info(f"Rank {needed} venues to continue")
        else:
            st.warning("No venues found. Try a different search.")


# ════════════════════════════════════════════════════════════════════════
# STEP 4: REVIEW & BOOK
# ════════════════════════════════════════════════════════════════════════
elif step == 4:
    st.markdown('<div class="section-card"><div class="section-title">Review & Book</div>'
                '<div class="section-subtitle">Review your selections with calendar and map views, then book</div></div>',
                unsafe_allow_html=True)

    search_result = st.session_state.get("search_result")
    slots = st.session_state.get("available_slots", [])
    slot_rankings = st.session_state.get("slot_rankings", [])
    venue_rankings = st.session_state.get("venue_rankings", [])

    if not search_result or not venue_rankings:
        st.warning("Complete previous steps first.")
        st.stop()

    venues = search_result.get("venues", [])
    ranked_venues = [venues[i] for i in venue_rankings if i < len(venues)]
    ranked_slots = [slots[i] for i in slot_rankings if i < len(slots)] if slot_rankings and slots else []
    members = st.session_state.get("members", [])

    # [FIX 6 & 7] Build itinerary items: venue + time slot pairs
    # Create pairs for hover interaction
    itinerary_items = []
    for vi, venue in enumerate(ranked_venues):
        slot = ranked_slots[vi] if vi < len(ranked_slots) else (ranked_slots[0] if ranked_slots else None)
        itinerary_items.append({"venue": venue, "slot": slot, "idx": vi})

    # Hover state
    if "hover_idx" not in st.session_state:
        st.session_state.hover_idx = 0

    # Two-column layout: left = itinerary, right = calendar + map overlays
    left_col, right_col = st.columns([3, 2])

    with left_col:
        st.subheader("Your Itinerary")
        total_cost = 0
        tier_cost = {"$": 12, "$$": 25, "$$$": 55, "$$$$": 90}

        for item in itinerary_items:
            v = item["venue"]
            s = item["slot"]
            idx = item["idx"]
            cost = tier_cost.get(v.get("price_tier", ""), 20)
            total_cost += cost

            rank_cls = f"rank-{idx+1}" if idx < 3 else "rank-other"
            slot_str = ""
            if s:
                sd = datetime.fromisoformat(s["start"])
                ed = datetime.fromisoformat(s["end"])
                slot_str = f"{sd.strftime('%a %b %d, %I:%M %p')} - {ed.strftime('%I:%M %p')}"

            price_html = f'<span class="price-badge">{v.get("price_tier", "")}</span>' if v.get("price_tier") else ""
            cats = v.get("categories", [])
            badges = "".join(f'<span class="venue-badge">{c}</span>' for c in cats[:2])

            # Each item is a button to change hover state
            is_active = st.session_state.hover_idx == idx
            card_cls = "venue-card selected" if is_active else "venue-card"

            st.markdown(f"""<div class="{card_cls}">
                <span class="rank-badge {rank_cls}">{idx+1}</span>
                <span class="venue-name">{v['name']}</span> {price_html}<br>
                <span class="venue-meta">📍 {v.get('address', 'Address TBD')}</span><br>
                <span class="venue-meta">🕐 {slot_str}</span><br>
                {badges}
                <span class="venue-meta" style="float:right">~${cost}/person</span>
            </div>""", unsafe_allow_html=True)

            if st.button(f"{'✦ Viewing' if is_active else 'View on calendar & map'}", key=f"hover_{idx}",
                         use_container_width=True, disabled=is_active):
                st.session_state.hover_idx = idx
                st.rerun()

        st.markdown(f"### Total estimated: ~${total_cost}/person")

    with right_col:
        # [FIX 6] Calendar overlay for the hovered item
        active = itinerary_items[st.session_state.hover_idx] if itinerary_items else None

        if active and active["slot"]:
            slot = active["slot"]
            sd = datetime.fromisoformat(slot["start"])
            ed = datetime.fromisoformat(slot["end"])
            busy_per_member = slot.get("busy_per_member", {})

            st.markdown(f'<div class="cal-overlay"><div class="cal-header">📅 {sd.strftime("%A, %B %d")} — Calendar</div>',
                        unsafe_allow_html=True)

            # Render hour-by-hour calendar for each member
            start_h = sd.hour
            end_h = ed.hour
            chosen_start = sd.hour
            chosen_end = ed.hour

            for member_name in [m["name"] for m in members]:
                st.markdown(f"**{member_name}**")
                member_busy = busy_per_member.get(member_name, [])

                cal_html = ""
                for h in range(start_h, end_h):
                    # Determine if this hour is busy, chosen, or free
                    is_busy = any(b["start"] <= h < b["end"] for b in member_busy)
                    is_chosen = chosen_start <= h < chosen_end and not is_busy

                    if is_busy:
                        bar_cls = "cal-busy"
                        label = f'<span class="cal-busy-label">Busy</span>'
                    elif is_chosen:
                        bar_cls = "cal-chosen"
                        label = f'<span class="cal-chosen-label">✓</span>' if h == chosen_start else ""
                    else:
                        bar_cls = "cal-free"
                        label = ""

                    h_label = f"{h % 12 or 12}{'pm' if h >= 12 else 'am'}"
                    cal_html += f'<div class="cal-hour-row"><div class="cal-hour-label">{h_label}</div><div class="cal-hour-bar {bar_cls}">{label}</div></div>'

                st.markdown(cal_html, unsafe_allow_html=True)

            st.markdown('</div>', unsafe_allow_html=True)

            # Legend
            st.markdown("""
            <div style="display:flex;gap:16px;margin:8px 0 16px 0;font-size:12px;color:#6B7785">
                <span><span style="display:inline-block;width:12px;height:12px;border-radius:2px;background:#FF690F;margin-right:4px;vertical-align:middle"></span>Selected slot</span>
                <span><span style="display:inline-block;width:12px;height:12px;border-radius:2px;background:#FFE0E0;margin-right:4px;vertical-align:middle"></span>Busy</span>
                <span><span style="display:inline-block;width:12px;height:12px;border-radius:2px;background:#F5F7FA;margin-right:4px;vertical-align:middle"></span>Free</span>
            </div>
            """, unsafe_allow_html=True)

        # [FIX 6] Map overlay for the hovered venue
        if active:
            v = active["venue"]
            addr = v.get("address", "")
            lat = v.get("lat")
            lng = v.get("lng")

            if lat and lng:
                import pandas as pd
                st.map(pd.DataFrame({"lat": [lat], "lon": [lng]}), zoom=14)
            else:
                # Styled map placeholder
                st.markdown(f"""<div class="map-overlay">
                    <div class="map-pin">📍</div>
                    <div class="map-name">{v['name']}</div>
                    <div class="map-addr">{addr}</div>
                </div>""", unsafe_allow_html=True)

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📅  Book & Send Invites", type="primary", use_container_width=True):
            st.session_state["booked"] = True
            st.session_state["booked_venues"] = ranked_venues
            st.balloons()
            st.success("Booked! Calendar invites sent to all group members.")
            advance_step()
            st.rerun()


# ════════════════════════════════════════════════════════════════════════
# STEP 5: FEEDBACK
# ════════════════════════════════════════════════════════════════════════
elif step == 5:
    st.markdown('<div class="section-card"><div class="section-title">How Was It?</div>'
                '<div class="section-subtitle">Rate your outing to help us improve future plans</div></div>',
                unsafe_allow_html=True)

    booked = st.session_state.get("booked_venues", [])
    if not booked:
        st.info("No booked outings to review yet.")
        st.stop()

    with st.form("feedback_form"):
        overall = st.slider("Overall rating", 1, 5, 4)
        venue_ratings = {}
        for v in booked:
            r = st.slider(v["name"], 1, 5, 4, key=f"fb_{v['id']}")
            venue_ratings[v["id"]] = r
        would_repeat = st.radio("Would you repeat this outing?", ["Yes", "No"], horizontal=True)
        free_text = st.text_area("Any comments?", placeholder="Tell us what you liked or what could be better...")
        if st.form_submit_button("Submit Feedback"):
            st.session_state["feedback"] = {
                "overall_rating": overall, "venue_ratings": venue_ratings,
                "would_repeat": would_repeat == "Yes", "free_text": free_text,
            }
            st.success("Thank you for your feedback! This will improve future outings.")


# ── Debug ──────────────────────────────────────────────────────────────

with st.expander("Debug Info", expanded=False):
    st.json({
        "current_step": st.session_state.current_step,
        "completed_steps": list(st.session_state.completed_steps),
        "group_id": st.session_state.get("group_id"),
        "members": st.session_state.get("members", []),
        "slot_rankings": st.session_state.get("slot_rankings", []),
        "venue_rankings": st.session_state.get("venue_rankings", []),
    })
