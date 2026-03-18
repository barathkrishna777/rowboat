"""Page 3: Connect Google Calendar for availability."""

import streamlit as st

st.header("Step 3: Connect Google Calendar")

if not st.session_state.get("group_id"):
    st.warning("Please create a group first (Step 1).")
    st.stop()

st.markdown(
    """
    Connect your Google Calendar so the agent can find times when everyone is free.

    **What we access:**
    - Free/busy information only (not event details)
    - Ability to create events (for sending invites)

    **Privacy:** We never read your event titles or descriptions — only whether you're busy or free.
    """
)

# For MVP without real OAuth, simulate calendar connection
st.subheader("Calendar Connection Status")

if "calendars_connected" not in st.session_state:
    st.session_state.calendars_connected = {}

members = st.session_state.get("members", [])
if not members:
    st.info("No members in the group yet. Add members in Step 1.")
    st.stop()

for member in members:
    name = member["name"]
    connected = st.session_state.calendars_connected.get(name, False)

    col1, col2 = st.columns([3, 1])
    with col1:
        if connected:
            st.success(f"{name} — Calendar connected")
        else:
            st.warning(f"{name} — Not connected")
    with col2:
        if not connected:
            if st.button(f"Connect", key=f"connect_{name}"):
                # In production, this would redirect to Google OAuth
                st.session_state.calendars_connected[name] = True
                st.rerun()

st.divider()

# Availability search
st.subheader("Find Group Availability")

connected_count = sum(1 for v in st.session_state.calendars_connected.values() if v)
if connected_count == 0:
    st.info("Connect at least one calendar to search for availability.")
    st.stop()

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Search from")
with col2:
    end_date = st.date_input("Search to")

min_hours = st.slider("Minimum outing duration (hours)", 1, 6, 2)

if st.button("Find Available Times"):
    # For MVP, generate simulated availability
    from datetime import datetime, timedelta

    st.session_state["available_slots"] = []
    current = datetime.combine(start_date, datetime.min.time().replace(hour=17))
    end = datetime.combine(end_date, datetime.min.time().replace(hour=23))

    while current < end:
        # Simulate some available evening slots
        if current.weekday() < 5:  # Weekdays
            slot_start = current.replace(hour=18)
            slot_end = current.replace(hour=22)
        else:  # Weekends
            slot_start = current.replace(hour=12)
            slot_end = current.replace(hour=22)

        st.session_state["available_slots"].append({
            "start": slot_start.isoformat(),
            "end": slot_end.isoformat(),
            "available_users": [m["name"] for m in members],
        })
        current += timedelta(days=1)

    st.success(f"Found {len(st.session_state['available_slots'])} available time slots!")

# Display found slots
if "available_slots" in st.session_state:
    slots = st.session_state["available_slots"]
    for i, slot in enumerate(slots):
        from datetime import datetime as dt

        start = dt.fromisoformat(slot["start"])
        end = dt.fromisoformat(slot["end"])
        duration = (end - start).total_seconds() / 3600

        day_name = start.strftime("%A, %B %d")
        time_range = f"{start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}"

        st.write(f"**{day_name}**: {time_range} ({duration:.0f}h) — {', '.join(slot['available_users'])}")
