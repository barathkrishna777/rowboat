"""Page 3: Connect Google Calendar for real availability."""

import streamlit as st
import httpx
import os

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")

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

# Check for OAuth callback success
params = st.query_params
if params.get("calendar_connected") == "true":
    connected_user_id = params.get("user_id", "")
    if connected_user_id:
        if "calendars_connected" not in st.session_state:
            st.session_state.calendars_connected = {}
        st.session_state.calendars_connected[connected_user_id] = True
        st.success("Google Calendar connected successfully!")
        # Clear the query params
        st.query_params.clear()

# Calendar connection status
st.subheader("Calendar Connection Status")

if "calendars_connected" not in st.session_state:
    st.session_state.calendars_connected = {}

members = st.session_state.get("members", [])
if not members:
    st.info("No members in the group yet. Add members in Step 1.")
    st.stop()

for member in members:
    name = member.get("name", "")
    user_id = member.get("user_id", "")
    connected = st.session_state.calendars_connected.get(user_id, False)

    col1, col2 = st.columns([3, 1])
    with col1:
        if connected:
            st.success(f"**{name}** — Calendar connected")
        else:
            st.warning(f"**{name}** — Not connected")
    with col2:
        if not connected and user_id:
            if st.button("Connect", key=f"connect_{user_id}"):
                try:
                    resp = httpx.get(
                        f"{API_BASE}/api/calendar/auth-url",
                        params={"user_id": user_id},
                        timeout=10.0,
                    )
                    resp.raise_for_status()
                    auth_url = resp.json()["auth_url"]
                    st.markdown(f'<meta http-equiv="refresh" content="0;url={auth_url}">', unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Could not start OAuth: {e}")

st.divider()

# Availability search
st.subheader("Find Group Availability")

connected_count = sum(1 for v in st.session_state.calendars_connected.values() if v)
if connected_count == 0:
    st.info("Connect at least one calendar to search for real availability, or proceed with simulated schedules.")

col1, col2 = st.columns(2)
with col1:
    start_date = st.date_input("Search from")
with col2:
    end_date = st.date_input("Search to")

min_hours = st.slider("Minimum outing duration (hours)", 1, 6, 2)

if st.button("Find Available Times", type="primary"):
    user_ids = [m.get("user_id", "") for m in members if m.get("user_id")]
    if not user_ids:
        st.warning("No members with IDs found.")
        st.stop()

    with st.spinner("Checking calendars..."):
        try:
            resp = httpx.post(
                f"{API_BASE}/api/calendar/availability",
                json={
                    "user_ids": user_ids,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "min_duration_hours": min_hours,
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()

            st.session_state["available_slots"] = data["slots"]

            if data.get("connected_users"):
                st.success(f"Real calendar data from: {', '.join(data['connected_users'])}")
            if data.get("simulated_users"):
                st.info(f"Assumed always free (no calendar): {', '.join(data['simulated_users'])}")

            st.success(f"Found {data['total']} available time slots!")
        except Exception as e:
            st.error(f"Failed to check availability: {e}")

# Display found slots
if "available_slots" in st.session_state:
    slots = st.session_state["available_slots"]
    if not slots:
        st.info("No available slots found in that date range.")
    for slot in slots:
        day_name = slot.get("day_name", "")
        date_str = slot.get("date", "")
        start_time = slot.get("start_time", "")
        end_time = slot.get("end_time", "")
        duration = slot.get("duration_hours", 0)
        is_weekend = slot.get("is_weekend", False)

        badge = " 🎉 Weekend" if is_weekend else ""
        st.write(f"**{day_name}, {date_str}**: {start_time} – {end_time} ({duration:.0f}h){badge}")
