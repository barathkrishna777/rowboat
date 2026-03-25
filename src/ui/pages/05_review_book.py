"""Page 5: Review itineraries and book with real Google Calendar integration."""

import streamlit as st
import httpx
import os

API_BASE = os.environ.get("API_BASE", "http://localhost:8000")

st.header("Step 5: Review & Book")

if not st.session_state.get("group_id"):
    st.warning("Please create a group first (Step 1).")
    st.stop()

# Check for orchestrator result or search result
orch_result = st.session_state.get("orchestrator_result")
search_result = st.session_state.get("search_result")

if not orch_result and not search_result:
    st.info("Generate a plan first (Step 4) to see venues here.")
    st.stop()

# Get the recommended venue and slot from orchestrator
recommended_venue = None
recommended_slot = None
ranked_venues = []

if orch_result:
    recommended_venue = orch_result.get("recommended_venue")
    recommended_slot = orch_result.get("recommended_slot")
    ranked_venues = orch_result.get("ranked_venues", [])

# Use search result venues as fallback
venues = []
if search_result:
    venues = search_result.get("venues", [])

if not recommended_venue and not venues:
    st.warning("No venues found. Go back and try a different search.")
    st.stop()

st.markdown("Review the AI recommendation and book your outing!")

# Show recommended venue
if recommended_venue:
    st.subheader("AI Recommended Plan")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"### {recommended_venue.get('name', 'Venue')}")
        if recommended_venue.get("address"):
            st.write(f"📍 {recommended_venue['address']}")
        if recommended_venue.get("rating"):
            st.write(f"⭐ {recommended_venue['rating']} | Score: {recommended_venue.get('score', 0)}% match")
        if recommended_venue.get("price_tier"):
            st.write(f"💰 {recommended_venue['price_tier']}")
    with col2:
        if recommended_slot:
            st.markdown("**When:**")
            st.write(f"📅 {recommended_slot.get('day_name', '')} {recommended_slot.get('date', '')}")
            st.write(f"🕐 {recommended_slot.get('start_time', '')} – {recommended_slot.get('end_time', '')}")

    if orch_result.get("estimated_cost_per_person"):
        st.write(f"💵 {orch_result['estimated_cost_per_person']}")

    st.divider()

# Booking section
st.subheader("Book This Outing")

members = st.session_state.get("members", [])
creator = st.session_state.get("creator_name", "")
creator_user_id = st.session_state.get("creator_user_id", "")

# Check if organizer has calendar connected
organizer_connected = st.session_state.get("calendars_connected", {}).get(creator_user_id, False)

if recommended_venue and recommended_slot:
    venue_name = recommended_venue.get("name", "Venue")
    venue_address = recommended_venue.get("address", "")
    start_iso = recommended_slot.get("start_iso", "")
    end_iso = recommended_slot.get("end_iso", "")

    # Get attendee emails
    attendee_emails = [m.get("email", "") for m in members if m.get("email")]
    attendee_emails = [e for e in attendee_emails if e]

    if attendee_emails:
        st.write(f"Calendar invites will be sent to: {', '.join(attendee_emails)}")

    col1, col2 = st.columns(2)
    with col1:
        if organizer_connected and start_iso and end_iso:
            if st.button("Book & Send Calendar Invites", type="primary"):
                with st.spinner("Creating calendar event..."):
                    try:
                        resp = httpx.post(
                            f"{API_BASE}/api/calendar/book",
                            json={
                                "organizer_user_id": creator_user_id,
                                "group_id": st.session_state.get("group_id", ""),
                                "venue_name": venue_name,
                                "venue_address": venue_address,
                                "start_time": start_iso,
                                "end_time": end_iso,
                                "attendee_emails": attendee_emails,
                            },
                            timeout=30.0,
                        )
                        resp.raise_for_status()
                        result = resp.json()

                        st.session_state["booked"] = True
                        st.balloons()
                        st.success(result.get("message", "Booked!"))
                        if result.get("calendar_link"):
                            st.markdown(f"[Open in Google Calendar]({result['calendar_link']})")
                    except httpx.HTTPStatusError as e:
                        detail = e.response.json().get("detail", str(e))
                        st.error(f"Booking failed: {detail}")
                    except Exception as e:
                        st.error(f"Booking failed: {e}")
        else:
            if st.button("Book This Itinerary", type="primary"):
                st.session_state["booked"] = True
                st.balloons()
                st.success("Itinerary booked!")
                if not organizer_connected:
                    st.info("Connect your Google Calendar (Step 3) to also send calendar invites.")

    with col2:
        if st.session_state.get("booked"):
            st.success("Booked!")

elif venues:
    # Fallback: show venue list for manual selection
    st.subheader("Select Venues for Your Outing")

    selected_venues = []
    for i, venue in enumerate(venues):
        col1, col2 = st.columns([0.5, 5])
        with col1:
            selected = st.checkbox("", key=f"select_{i}", label_visibility="collapsed")
        with col2:
            price_str = f" | {venue.get('price_tier', '')}" if venue.get('price_tier') else ""
            st.write(f"**{venue['name']}** — {', '.join(venue.get('categories', []))}{price_str}")
            st.caption(venue.get("address", "No address"))
        if selected:
            selected_venues.append(venue)

    if selected_venues:
        st.divider()
        st.subheader(f"Your Itinerary ({len(selected_venues)} venues)")
        total_cost = 0
        for i, venue in enumerate(selected_venues, 1):
            tier_cost = {"$": 12, "$$": 25, "$$$": 55, "$$$$": 90}
            cost = tier_cost.get(venue.get("price_tier", ""), 20)
            total_cost += cost
            st.write(f"**{i}. {venue['name']}** — ~${cost}/person")

        st.write(f"**Total estimated: ~${total_cost}/person**")

        if st.button("Book This Itinerary", type="primary"):
            st.session_state["booked"] = True
            st.balloons()
            st.success("Itinerary booked!")
