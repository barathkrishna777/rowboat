"""Page 5: Review itineraries and book."""

import streamlit as st

st.header("Step 5: Review & Book")

if not st.session_state.get("group_id"):
    st.warning("Please create a group first (Step 1).")
    st.stop()

search_result = st.session_state.get("search_result")
if not search_result:
    st.info("Generate a plan first (Step 4) to see venues here.")
    st.stop()

venues = search_result.get("venues", [])
if not venues:
    st.warning("No venues found. Go back to Step 4 and try a different search.")
    st.stop()

st.markdown("Select venues to build your itinerary, then book!")

# Venue selection
st.subheader("Select Venues for Your Outing")

selected_venues = []
for i, venue in enumerate(venues):
    col1, col2, col3 = st.columns([0.5, 3, 1])
    with col1:
        selected = st.checkbox("", key=f"select_{i}", label_visibility="collapsed")
    with col2:
        rating_str = f"{'⭐' * int(venue.get('rating', 0))} " if venue.get('rating') else ""
        price_str = f" | {venue.get('price_tier', '')}" if venue.get('price_tier') else ""
        st.write(f"**{venue['name']}** — {', '.join(venue.get('categories', []))}{price_str}")
        st.caption(f"{rating_str}{venue.get('address', 'No address')}")
    with col3:
        st.write(f"Source: {venue.get('source', 'N/A')}")

    if selected:
        selected_venues.append(venue)

if selected_venues:
    st.divider()
    st.subheader(f"Your Itinerary ({len(selected_venues)} venues)")

    total_cost = 0
    for i, venue in enumerate(selected_venues, 1):
        st.write(f"**{i}. {venue['name']}**")
        st.caption(venue.get("address", ""))
        # Estimate cost based on price tier
        tier_cost = {"$": 12, "$$": 25, "$$$": 55, "$$$$": 90}
        cost = tier_cost.get(venue.get("price_tier", ""), 20)
        total_cost += cost
        st.write(f"Estimated: ~${cost}/person")

    st.divider()
    st.write(f"**Total estimated cost: ~${total_cost}/person**")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Book This Itinerary", type="primary"):
            # Simulate booking
            st.session_state["booked"] = True
            st.session_state["booked_venues"] = selected_venues
            st.balloons()
            st.success("Itinerary booked! Calendar invites will be sent to all group members.")
    with col2:
        if st.button("Send Calendar Invites"):
            if st.session_state.get("booked"):
                st.success("Calendar invites sent to all group members!")
            else:
                st.warning("Book the itinerary first.")
else:
    st.info("Select at least one venue above to build your itinerary.")
