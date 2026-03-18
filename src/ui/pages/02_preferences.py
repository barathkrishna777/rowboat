"""Page 2: Preference quiz for group members."""

import streamlit as st

st.header("Step 2: Set Your Preferences")

if not st.session_state.get("group_id"):
    st.warning("Please create a group first (Step 1).")
    st.stop()

CUISINE_OPTIONS = [
    "Italian", "Japanese", "Mexican", "Chinese", "Indian", "Thai",
    "Korean", "American", "Mediterranean", "French", "Vietnamese", "Ethiopian",
]
ACTIVITY_OPTIONS = [
    "Bowling", "Escape Room", "Concert", "Movie", "Hiking", "Karaoke",
    "Board Games", "Mini Golf", "Arcade", "Museum", "Comedy Show", "Sports Event",
]
DIETARY_OPTIONS = [
    "None", "Vegetarian", "Vegan", "Gluten Free", "Halal", "Kosher",
    "Nut Allergy", "Dairy Free", "Shellfish Allergy",
]
BUDGET_OPTIONS = ["$ (Under $15/person)", "$$ ($15-40/person)", "$$$  ($40-80/person)", "$$$$ ($80+/person)"]

with st.form("preferences_form"):
    st.subheader("Food Preferences")
    cuisines = st.multiselect("Favorite cuisines", CUISINE_OPTIONS)

    st.subheader("Activity Preferences")
    activities = st.multiselect("Favorite activities", ACTIVITY_OPTIONS)

    st.subheader("Dietary Restrictions")
    dietary = st.multiselect("Any dietary restrictions?", DIETARY_OPTIONS, default=["None"])

    st.subheader("Budget")
    budget = st.select_slider("Maximum budget per person", options=BUDGET_OPTIONS, value=BUDGET_OPTIONS[1])

    st.subheader("Dealbreakers")
    dealbreakers = st.text_area(
        "Anything you absolutely don't want? (one per line)",
        placeholder="No loud places\nMust have parking\nNo smoking areas",
    )

    st.subheader("Preferred Neighborhoods")
    neighborhoods = st.text_input(
        "Preferred areas (comma-separated)",
        placeholder="Oakland, Shadyside, Squirrel Hill",
    )

    st.subheader("Accessibility")
    accessibility = st.text_input(
        "Any accessibility needs? (comma-separated)",
        placeholder="Wheelchair accessible, elevator access",
    )

    submitted = st.form_submit_button("Save Preferences")

    if submitted:
        budget_map = {
            BUDGET_OPTIONS[0]: "$",
            BUDGET_OPTIONS[1]: "$$",
            BUDGET_OPTIONS[2]: "$$$",
            BUDGET_OPTIONS[3]: "$$$$",
        }
        dietary_map = {
            "None": "none", "Vegetarian": "vegetarian", "Vegan": "vegan",
            "Gluten Free": "gluten_free", "Halal": "halal", "Kosher": "kosher",
            "Nut Allergy": "nut_allergy", "Dairy Free": "dairy_free",
            "Shellfish Allergy": "shellfish_allergy",
        }

        prefs = {
            "cuisine_preferences": [c.lower() for c in cuisines],
            "activity_preferences": [a.lower() for a in activities],
            "dietary_restrictions": [dietary_map[d] for d in dietary if d != "None"],
            "budget_max": budget_map[budget],
            "dealbreakers": [d.strip() for d in dealbreakers.split("\n") if d.strip()],
            "preferred_neighborhoods": [n.strip() for n in neighborhoods.split(",") if n.strip()],
            "accessibility_needs": [a.strip() for a in accessibility.split(",") if a.strip()],
        }
        st.session_state["preferences"] = prefs
        st.success("Preferences saved!")
        st.json(prefs)
