"""Page 4: Generate outing plans using the AI agent."""

import streamlit as st
import httpx

API_BASE = "http://localhost:8000/api"

st.header("Step 4: Generate Outing Plan")

if not st.session_state.get("group_id"):
    st.warning("Please create a group first (Step 1).")
    st.stop()

st.markdown("Describe what kind of outing you're looking for, and the AI agent will search for venues.")

with st.form("plan_search"):
    query = st.text_area(
        "What are you looking for?",
        placeholder="We want a fun Saturday evening — dinner at a nice Italian place followed by bowling or an escape room. Budget is around $30 per person.",
        height=100,
    )
    location = st.text_input("Location", value="Pittsburgh, PA")
    max_results = st.slider("Max results per source", 5, 20, 10)
    submitted = st.form_submit_button("Search")

if submitted and query:
    with st.spinner("AI agent is searching venues across Yelp, Eventbrite, and Ticketmaster..."):
        try:
            resp = httpx.post(
                f"{API_BASE}/plans/search",
                json={"query": query, "location": location, "max_results": max_results},
                timeout=60.0,
            )
            resp.raise_for_status()
            result = resp.json()

            st.session_state["search_result"] = result

        except Exception as e:
            st.error(f"Search failed: {e}")

# Display results
if "search_result" in st.session_state:
    result = st.session_state["search_result"]

    st.subheader("Agent Summary")
    st.info(result.get("summary", "No summary available"))

    sources = result.get("sources_searched", [])
    if sources:
        st.caption(f"Sources searched: {', '.join(sources)}")

    venues = result.get("venues", [])
    if venues:
        st.subheader(f"Found {len(venues)} Venues")

        for i, venue in enumerate(venues):
            with st.expander(f"{i+1}. {venue['name']} — {venue.get('category', 'N/A')}"):
                cols = st.columns([2, 1])
                with cols[0]:
                    st.write(f"**Address:** {venue.get('address', 'N/A')}")
                    st.write(f"**Categories:** {', '.join(venue.get('categories', []))}")
                    if venue.get("rating"):
                        st.write(f"**Rating:** {'⭐' * int(venue['rating'])} ({venue['rating']})")
                    if venue.get("review_count"):
                        st.write(f"**Reviews:** {venue['review_count']}")
                    if venue.get("price_tier"):
                        st.write(f"**Price:** {venue['price_tier']}")
                    if venue.get("url"):
                        st.write(f"[View Details]({venue['url']})")
                with cols[1]:
                    if venue.get("image_url"):
                        st.image(venue["image_url"], width=200)
                    st.write(f"**Source:** {venue.get('source', 'N/A')}")
    else:
        st.warning("No venues found. Try adjusting your search.")
