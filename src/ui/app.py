"""Streamlit UI for the Group Outing Planner."""

import streamlit as st

st.set_page_config(
    page_title="Outing Planner",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Group Outing Planner")
st.markdown(
    """
    An AI-powered agent that coordinates group outings end-to-end.

    **How it works:**
    1. **Create a Group** — Add your friends and set up a group
    2. **Set Preferences** — Each member fills out a quick preference quiz
    3. **Connect Calendar** — Sync Google Calendar to find availability
    4. **Generate Plan** — AI searches venues and creates itineraries
    5. **Review & Book** — Pick your favorite plan and book it
    6. **Give Feedback** — Rate the outing to improve future plans

    Use the sidebar to navigate between steps.
    """
)

# Show current session state for debugging
if st.checkbox("Show debug info", value=False):
    st.json(
        {
            "group_id": st.session_state.get("group_id"),
            "user_id": st.session_state.get("user_id"),
            "members": st.session_state.get("members", []),
        }
    )
