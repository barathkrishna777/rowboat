"""Page 1: Create a group and add members."""

import streamlit as st
import httpx

API_BASE = "http://localhost:8000/api"

st.header("Step 1: Create Your Group")

if "group_id" not in st.session_state:
    st.session_state.group_id = None
    st.session_state.user_id = None
    st.session_state.members = []

# Create group form
if st.session_state.group_id is None:
    with st.form("create_group"):
        group_name = st.text_input("Group Name", placeholder="Friday Night Crew")
        your_name = st.text_input("Your Name", placeholder="John Doe")
        your_email = st.text_input("Your Email", placeholder="john@example.com")
        submitted = st.form_submit_button("Create Group")

        if submitted and group_name and your_name and your_email:
            try:
                resp = httpx.post(
                    f"{API_BASE}/groups/",
                    json={
                        "name": group_name,
                        "creator_name": your_name,
                        "creator_email": your_email,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                st.session_state.group_id = data["id"]
                st.session_state.user_id = data["member_ids"][0]
                st.session_state.members = [{"name": your_name, "email": your_email}]
                st.success(f"Group '{group_name}' created!")
                st.rerun()
            except Exception as e:
                st.error(f"Error creating group: {e}")
else:
    st.success(f"Group ID: `{st.session_state.group_id}`")

    # Add members
    st.subheader("Add Members")
    with st.form("add_member"):
        name = st.text_input("Member Name")
        email = st.text_input("Member Email")
        add = st.form_submit_button("Add Member")

        if add and name and email:
            try:
                resp = httpx.post(
                    f"{API_BASE}/groups/{st.session_state.group_id}/members",
                    json={"name": name, "email": email},
                )
                resp.raise_for_status()
                st.session_state.members.append({"name": name, "email": email})
                st.success(f"Added {name}!")
                st.rerun()
            except Exception as e:
                st.error(f"Error adding member: {e}")

    # Show current members
    if st.session_state.members:
        st.subheader("Current Members")
        for i, m in enumerate(st.session_state.members, 1):
            st.write(f"{i}. **{m['name']}** ({m['email']})")

    if st.button("Reset Group"):
        st.session_state.group_id = None
        st.session_state.user_id = None
        st.session_state.members = []
        st.rerun()
