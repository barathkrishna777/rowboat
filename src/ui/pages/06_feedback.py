"""Page 6: Post-event feedback."""

import streamlit as st

st.header("Step 6: Post-Event Feedback")

if not st.session_state.get("group_id"):
    st.warning("Please create a group first (Step 1).")
    st.stop()

booked_venues = st.session_state.get("booked_venues", [])
if not booked_venues:
    st.info("No booked events yet. Complete Steps 4 and 5 first.")
    st.stop()

st.markdown("Help us improve future outings by rating your experience!")

with st.form("feedback"):
    st.subheader("Overall Rating")
    overall = st.slider("How was the outing overall?", 1, 5, 4)

    st.subheader("Venue Ratings")
    venue_ratings = {}
    for venue in booked_venues:
        rating = st.slider(
            f"{venue['name']}",
            1, 5, 4,
            key=f"rating_{venue['id']}",
        )
        venue_ratings[venue["id"]] = rating

    st.subheader("Would you do this again?")
    would_repeat = st.radio("Would you repeat this outing?", ["Yes", "No"], horizontal=True)

    st.subheader("What did you like?")
    liked = st.text_area("Tell us what you enjoyed (one per line)", placeholder="Great food\nFun atmosphere\nEasy to get to")

    st.subheader("What could be better?")
    disliked = st.text_area("Tell us what could improve (one per line)", placeholder="Too crowded\nService was slow")

    st.subheader("Additional Comments")
    free_text = st.text_area("Anything else?", placeholder="Optional")

    submitted = st.form_submit_button("Submit Feedback")

    if submitted:
        feedback = {
            "overall_rating": overall,
            "venue_ratings": venue_ratings,
            "would_repeat": would_repeat == "Yes",
            "liked": [l.strip() for l in liked.split("\n") if l.strip()],
            "disliked": [d.strip() for d in disliked.split("\n") if d.strip()],
            "free_text": free_text if free_text else None,
        }
        st.session_state["feedback"] = feedback
        st.success("Thank you for your feedback! This will help improve future outings.")
        st.json(feedback)
