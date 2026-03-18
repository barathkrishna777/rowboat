"""Streamlit UI for the Group Outing Planner — single-page stepper flow."""

import streamlit as st
import httpx
from datetime import datetime, timedelta

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
    .stApp {
        background-color: #FAFBFC;
    }
    section[data-testid="stSidebar"] { display: none; }

    /* ── Stepper Nav ────────────────────────────────── */
    .stepper-container {
        display: flex;
        justify-content: center;
        gap: 0;
        padding: 16px 0 24px 0;
        background: white;
        border-bottom: 2px solid #F0F2F5;
        margin: -1rem -1rem 2rem -1rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }
    .step-item {
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 10px 18px;
        border-radius: 30px;
        font-size: 14px;
        font-weight: 500;
        color: #8E99A4;
        cursor: default;
        transition: all 0.2s ease;
        white-space: nowrap;
    }
    .step-item.active {
        background: #FF690F;
        color: white;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(255, 105, 15, 0.3);
    }
    .step-item.completed {
        background: #E8F8EE;
        color: #1DB954;
        cursor: pointer;
        font-weight: 600;
    }
    .step-item.completed:hover {
        background: #D0F0DB;
    }
    .step-number {
        width: 26px;
        height: 26px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 13px;
        font-weight: 700;
        flex-shrink: 0;
    }
    .step-item.active .step-number {
        background: rgba(255,255,255,0.25);
        color: white;
    }
    .step-item.completed .step-number {
        background: #1DB954;
        color: white;
    }
    .step-item:not(.active):not(.completed) .step-number {
        background: #E4E8EC;
        color: #8E99A4;
    }
    .step-connector {
        width: 30px;
        height: 2px;
        background: #E4E8EC;
        align-self: center;
        flex-shrink: 0;
    }
    .step-connector.done {
        background: #1DB954;
    }

    /* ── Section Cards ──────────────────────────────── */
    .section-card {
        background: white;
        border-radius: 16px;
        padding: 2rem 2.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
        margin-bottom: 1.5rem;
        border: 1px solid #F0F2F5;
    }
    .section-title {
        font-size: 28px;
        font-weight: 700;
        color: #192024;
        margin-bottom: 4px;
    }
    .section-subtitle {
        font-size: 16px;
        color: #6B7785;
        margin-bottom: 24px;
    }

    /* ── Buttons ─────────────────────────────────────── */
    .stButton > button[kind="primary"],
    .stFormSubmitButton > button {
        background-color: #FF690F !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.6rem 2rem !important;
        font-weight: 600 !important;
        font-size: 15px !important;
        transition: all 0.2s ease !important;
    }
    .stFormSubmitButton > button:hover,
    .stButton > button[kind="primary"]:hover {
        background-color: #E85A00 !important;
        box-shadow: 0 4px 12px rgba(255, 105, 15, 0.35) !important;
    }

    /* ── Venue Cards ─────────────────────────────────── */
    .venue-card {
        background: white;
        border: 1px solid #E8ECF0;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 0.8rem;
        transition: all 0.2s ease;
    }
    .venue-card:hover {
        border-color: #FF690F;
        box-shadow: 0 2px 8px rgba(255,105,15,0.12);
    }
    .venue-name {
        font-size: 18px;
        font-weight: 600;
        color: #192024;
    }
    .venue-meta {
        font-size: 14px;
        color: #6B7785;
    }
    .venue-badge {
        display: inline-block;
        background: #FFF3EB;
        color: #FF690F;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 6px;
    }
    .price-badge {
        display: inline-block;
        background: #E8F8EE;
        color: #1DB954;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
    }

    /* ── Member Chips ────────────────────────────────── */
    .member-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: #F5F7FA;
        border: 1px solid #E4E8EC;
        border-radius: 20px;
        padding: 6px 14px;
        margin: 4px;
        font-size: 14px;
        color: #363F45;
    }
    .member-chip .dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: #1DB954;
    }

    /* ── Form Inputs ─────────────────────────────────── */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 8px !important;
        border-color: #E4E8EC !important;
    }
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #FF690F !important;
        box-shadow: 0 0 0 1px #FF690F !important;
    }

    /* ── Hide default Streamlit chrome ────────────────── */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* ── Hero header ──────────────────────────────────── */
    .hero {
        text-align: center;
        padding: 1rem 0 0.5rem 0;
    }
    .hero h1 {
        font-size: 32px;
        font-weight: 800;
        color: #192024;
        margin-bottom: 0;
    }
    .hero-accent {
        color: #FF690F;
    }
    .hero p {
        color: #6B7785;
        font-size: 16px;
    }
</style>
""", unsafe_allow_html=True)

# ── Session State Init ─────────────────────────────────────────────────

STEPS = [
    "Create Group",
    "Preferences",
    "Calendar",
    "Find Venues",
    "Review & Book",
    "Feedback",
]

if "current_step" not in st.session_state:
    st.session_state.current_step = 0
if "group_id" not in st.session_state:
    st.session_state.group_id = None
    st.session_state.user_id = None
    st.session_state.members = []
if "completed_steps" not in st.session_state:
    st.session_state.completed_steps = set()


def advance_step():
    """Mark current step completed and move to next."""
    st.session_state.completed_steps.add(st.session_state.current_step)
    if st.session_state.current_step < len(STEPS) - 1:
        st.session_state.current_step += 1


def go_to_step(idx):
    """Go to a previously completed step."""
    if idx in st.session_state.completed_steps or idx == st.session_state.current_step:
        st.session_state.current_step = idx


# ── Hero ───────────────────────────────────────────────────────────────

st.markdown("""
<div class="hero">
    <h1>🎯 <span class="hero-accent">Outing</span> Planner</h1>
    <p>AI-powered group outing coordination — from preferences to booking</p>
</div>
""", unsafe_allow_html=True)

# ── Stepper Navigation ────────────────────────────────────────────────

def render_stepper():
    current = st.session_state.current_step
    completed = st.session_state.completed_steps
    html = '<div class="stepper-container">'
    for i, name in enumerate(STEPS):
        if i > 0:
            conn_class = "step-connector done" if i - 1 in completed else "step-connector"
            html += f'<div class="{conn_class}"></div>'

        if i == current:
            cls = "active"
        elif i in completed:
            cls = "completed"
        else:
            cls = ""

        check = "✓" if i in completed else str(i + 1)
        html += f'<div class="step-item {cls}"><span class="step-number">{check}</span>{name}</div>'

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


render_stepper()

# Navigation buttons for going back to completed steps
completed = st.session_state.completed_steps
if completed:
    cols = st.columns(len(STEPS))
    for i in range(len(STEPS)):
        if i in completed and i != st.session_state.current_step:
            with cols[i]:
                if st.button(f"← {STEPS[i]}", key=f"nav_{i}", use_container_width=True):
                    go_to_step(i)
                    st.rerun()


# ── Step Content ───────────────────────────────────────────────────────

step = st.session_state.current_step

# ────────────────────────────────────────────────────────────────────────
# STEP 0: CREATE GROUP
# ────────────────────────────────────────────────────────────────────────
if step == 0:
    st.markdown('<div class="section-card"><div class="section-title">Create Your Group</div><div class="section-subtitle">Start by naming your group and adding your friends</div></div>', unsafe_allow_html=True)

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
                    resp = httpx.post(
                        f"{API_BASE}/groups/",
                        json={"name": group_name, "creator_name": your_name, "creator_email": your_email},
                    )
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
        members_html = ""
        for m in st.session_state.members:
            members_html += f'<span class="member-chip"><span class="dot"></span>{m["name"]}</span>'
        st.markdown(f"**Group Members:** {members_html}", unsafe_allow_html=True)

        # Add member form
        with st.form("add_member"):
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                name = st.text_input("Name", placeholder="Friend's name")
            with c2:
                email = st.text_input("Email", placeholder="friend@email.com")
            with c3:
                st.write("")  # spacer
                add = st.form_submit_button("Add")

            if add and name and email:
                try:
                    resp = httpx.post(
                        f"{API_BASE}/groups/{st.session_state.group_id}/members",
                        json={"name": name, "email": email},
                    )
                    resp.raise_for_status()
                    st.session_state.members.append({"name": name, "email": email})
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

# ────────────────────────────────────────────────────────────────────────
# STEP 1: PREFERENCES
# ────────────────────────────────────────────────────────────────────────
elif step == 1:
    st.markdown('<div class="section-card"><div class="section-title">Set Preferences</div><div class="section-subtitle">Tell us what everyone enjoys so we can find the perfect outing</div></div>', unsafe_allow_html=True)

    CUISINE_OPTIONS = ["Italian", "Japanese", "Mexican", "Chinese", "Indian", "Thai", "Korean", "American", "Mediterranean", "French", "Vietnamese", "Ethiopian"]
    ACTIVITY_OPTIONS = ["Bowling", "Escape Room", "Concert", "Movie", "Hiking", "Karaoke", "Board Games", "Mini Golf", "Arcade", "Museum", "Comedy Show", "Sports Event"]
    DIETARY_OPTIONS = ["None", "Vegetarian", "Vegan", "Gluten Free", "Halal", "Kosher", "Nut Allergy", "Dairy Free", "Shellfish Allergy"]
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

        submitted = st.form_submit_button("Save Preferences")

        if submitted:
            budget_map = {BUDGET_OPTIONS[0]: "$", BUDGET_OPTIONS[1]: "$$", BUDGET_OPTIONS[2]: "$$$", BUDGET_OPTIONS[3]: "$$$$"}
            prefs = {
                "cuisine_preferences": [c.lower() for c in cuisines],
                "activity_preferences": [a.lower() for a in activities],
                "dietary_restrictions": [d.lower().replace(" ", "_") for d in dietary if d != "None"],
                "budget_max": budget_map[budget],
                "dealbreakers": [d.strip() for d in dealbreakers.split("\n") if d.strip()],
                "preferred_neighborhoods": [n.strip() for n in neighborhoods.split(",") if n.strip()],
            }
            st.session_state["user_preferences"] = prefs
            st.success("Preferences saved!")
            advance_step()
            st.rerun()

# ────────────────────────────────────────────────────────────────────────
# STEP 2: CALENDAR
# ────────────────────────────────────────────────────────────────────────
elif step == 2:
    st.markdown('<div class="section-card"><div class="section-title">Find Availability</div><div class="section-subtitle">Connect calendars to find when everyone is free</div></div>', unsafe_allow_html=True)

    if "calendars_connected" not in st.session_state:
        st.session_state.calendars_connected = {}

    members = st.session_state.get("members", [])

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
                if st.button(f"Connect", key=f"cal_{name}"):
                    st.session_state.calendars_connected[name] = True
                    st.rerun()

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Search from", value=datetime.now().date() + timedelta(days=1))
    with col2:
        end_date = st.date_input("Search to", value=datetime.now().date() + timedelta(days=7))

    if st.button("Find Available Times", type="primary"):
        slots = []
        current = datetime.combine(start_date, datetime.min.time())
        end = datetime.combine(end_date, datetime.min.time())
        while current <= end:
            if current.weekday() >= 5:
                slots.append({"start": current.replace(hour=12).isoformat(), "end": current.replace(hour=22).isoformat(), "users": [m["name"] for m in members]})
            else:
                slots.append({"start": current.replace(hour=18).isoformat(), "end": current.replace(hour=22).isoformat(), "users": [m["name"] for m in members]})
            current += timedelta(days=1)
        st.session_state["available_slots"] = slots

    if "available_slots" in st.session_state:
        st.subheader(f"Found {len(st.session_state['available_slots'])} time slots")
        for slot in st.session_state["available_slots"]:
            start = datetime.fromisoformat(slot["start"])
            end = datetime.fromisoformat(slot["end"])
            duration = (end - start).total_seconds() / 3600
            day_name = start.strftime("%A, %b %d")
            time_range = f"{start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}"
            st.markdown(f"""<div class="venue-card">
                <span class="venue-name">{day_name}</span><br>
                <span class="venue-meta">{time_range} ({duration:.0f}h) — {', '.join(slot['users'])}</span>
            </div>""", unsafe_allow_html=True)

        st.divider()
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("Continue →", type="primary", key="cal_continue", use_container_width=True):
                advance_step()
                st.rerun()

# ────────────────────────────────────────────────────────────────────────
# STEP 3: FIND VENUES
# ────────────────────────────────────────────────────────────────────────
elif step == 3:
    st.markdown('<div class="section-card"><div class="section-title">Find Venues</div><div class="section-subtitle">Tell us what you\'re looking for and our AI will search for the best options</div></div>', unsafe_allow_html=True)

    with st.form("plan_search"):
        query = st.text_area(
            "What are you looking for?",
            placeholder="Italian dinner followed by bowling or an escape room. Budget around $30/person.",
            height=100,
        )
        col1, col2 = st.columns(2)
        with col1:
            location = st.text_input("Location", value="Pittsburgh, PA")
        with col2:
            max_results = st.slider("Max results", 3, 20, 8)
        submitted = st.form_submit_button("🔍  Search Venues")

    if submitted and query:
        with st.spinner("AI agent is searching for venues..."):
            try:
                resp = httpx.post(
                    f"{API_BASE}/plans/search",
                    json={"query": query, "location": location, "max_results": max_results},
                    timeout=60.0,
                )
                resp.raise_for_status()
                st.session_state["search_result"] = resp.json()
            except Exception as e:
                st.error(f"Search failed: {e}")

    if "search_result" in st.session_state:
        result = st.session_state["search_result"]
        if result.get("summary"):
            st.info(result["summary"])

        venues = result.get("venues", [])
        if venues:
            st.subheader(f"{len(venues)} venues found")
            for i, venue in enumerate(venues):
                rating_stars = "⭐" * int(venue.get("rating", 0)) if venue.get("rating") else ""
                price = venue.get("price_tier", "")
                cats = venue.get("categories", [])

                badges = "".join(f'<span class="venue-badge">{c}</span>' for c in cats[:3])
                price_html = f'<span class="price-badge">{price}</span>' if price else ""

                st.markdown(f"""<div class="venue-card">
                    <span class="venue-name">{venue['name']}</span> {price_html}<br>
                    <span class="venue-meta">{venue.get('address', '')} {rating_stars}</span><br>
                    {badges}
                </div>""", unsafe_allow_html=True)

            st.divider()
            col1, col2 = st.columns([3, 1])
            with col2:
                if st.button("Continue to Review →", type="primary", key="venue_continue", use_container_width=True):
                    advance_step()
                    st.rerun()
        else:
            st.warning("No venues found. Try a different search.")

# ────────────────────────────────────────────────────────────────────────
# STEP 4: REVIEW & BOOK
# ────────────────────────────────────────────────────────────────────────
elif step == 4:
    st.markdown('<div class="section-card"><div class="section-title">Review & Book</div><div class="section-subtitle">Select venues for your itinerary and book the outing</div></div>', unsafe_allow_html=True)

    search_result = st.session_state.get("search_result")
    if not search_result:
        st.warning("Search for venues first (Step 4).")
        st.stop()

    venues = search_result.get("venues", [])
    selected = []

    for i, venue in enumerate(venues):
        col1, col2 = st.columns([0.3, 5])
        with col1:
            checked = st.checkbox("", key=f"sel_{i}", label_visibility="collapsed")
        with col2:
            price = venue.get("price_tier", "")
            rating = f"⭐ {venue.get('rating', '')}" if venue.get("rating") else ""
            st.markdown(f"**{venue['name']}** — {', '.join(venue.get('categories', [])[:2])} {price} {rating}")
            st.caption(venue.get("address", ""))
        if checked:
            selected.append(venue)

    if selected:
        st.divider()
        st.subheader(f"Your Itinerary — {len(selected)} venues")

        total_cost = 0
        tier_cost = {"$": 12, "$$": 25, "$$$": 55, "$$$$": 90}
        for i, v in enumerate(selected, 1):
            cost = tier_cost.get(v.get("price_tier", ""), 20)
            total_cost += cost
            st.markdown(f"""<div class="venue-card">
                <span class="venue-name">{i}. {v['name']}</span><br>
                <span class="venue-meta">{v.get('address', '')} — ~${cost}/person</span>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"### Total: ~${total_cost}/person")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📅  Book & Send Invites", type="primary", use_container_width=True):
                st.session_state["booked"] = True
                st.session_state["booked_venues"] = selected
                st.balloons()
                st.success("Booked! Calendar invites sent to all group members.")
                advance_step()
                st.rerun()

# ────────────────────────────────────────────────────────────────────────
# STEP 5: FEEDBACK
# ────────────────────────────────────────────────────────────────────────
elif step == 5:
    st.markdown('<div class="section-card"><div class="section-title">How Was It?</div><div class="section-subtitle">Rate your outing to help us improve future plans</div></div>', unsafe_allow_html=True)

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
            feedback = {
                "overall_rating": overall,
                "venue_ratings": venue_ratings,
                "would_repeat": would_repeat == "Yes",
                "free_text": free_text,
            }
            st.session_state["feedback"] = feedback
            st.success("Thank you for your feedback! This will improve future outings.")
            st.json(feedback)

# ── Debug ──────────────────────────────────────────────────────────────

with st.expander("Debug Info", expanded=False):
    st.json({
        "current_step": st.session_state.current_step,
        "completed_steps": list(st.session_state.completed_steps),
        "group_id": st.session_state.get("group_id"),
        "members": st.session_state.get("members", []),
    })
