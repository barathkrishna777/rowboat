"""Streamlit UI for the Group Outing Planner — single-page stepper flow."""

import streamlit as st
import httpx
import urllib.parse
from datetime import datetime, timedelta, time as dt_time
# from streamlit_sortables import sort_items  # replaced with custom card reorder
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.getenv("API_BASE", "http://localhost:8000") + "/api"
MAPS_EMBED_KEY = os.getenv("GOOGLE_MAPS_EMBED_KEY", "")

# ── Page Config ────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Outing Planner",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── WebSocket Keep-Alive (prevents Railway proxy from dropping connection) ──
import streamlit.components.v1 as components
components.html("""
<script>
(function keepAlive() {
    setInterval(function() {
        fetch(window.location.href, {method: 'HEAD', cache: 'no-store'}).catch(function(){});
    }, 25000);
})();
</script>
""", height=0)

# ── Kayak-Inspired Theme ──────────────────────────────────────────────

st.markdown("""
<style>
    .stApp { background-color: #FAFBFC; }
    section[data-testid="stSidebar"] { display: none; }

    /* ── Stepper ─────────────────────────────────────── */
    .stepper-container {
        display: flex; justify-content: center; gap: 0;
        padding: 16px 2rem 24px 2rem; background: white;
        border-bottom: 2px solid #F0F2F5; margin: -1rem -1rem 2rem -1rem;
    }
    .step-item {
        display: flex; align-items: center; gap: 8px;
        padding: 10px 18px; border-radius: 30px; font-size: 14px;
        font-weight: 500; color: #8E99A4; cursor: default;
        transition: all 0.2s ease; white-space: nowrap;
    }
    .step-item.active { background: #FF690F; color: white; font-weight: 600; box-shadow: 0 2px 8px rgba(255,105,15,0.3); }
    .step-item.completed { background: #E8F8EE; color: #1DB954; cursor: pointer; font-weight: 600; }
    .step-item.completed:hover { background: #D0F0DB; }
    .step-number { width: 26px; height: 26px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; flex-shrink: 0; }
    .step-item.active .step-number { background: rgba(255,255,255,0.25); color: white; }
    .step-item.completed .step-number { background: #1DB954; color: white; }
    .step-item:not(.active):not(.completed) .step-number { background: #E4E8EC; color: #8E99A4; }
    .step-connector { width: 30px; height: 2px; background: #E4E8EC; align-self: center; flex-shrink: 0; }
    .step-connector.done { background: #1DB954; }

    /* ── Section Cards ──────────────────────────────── */
    .section-card { background: white; border-radius: 16px; padding: 2rem 2.5rem; box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04); margin-bottom: 1.5rem; border: 1px solid #F0F2F5; }
    .section-title { font-size: 28px; font-weight: 700; color: #192024; margin-bottom: 4px; }
    .section-subtitle { font-size: 16px; color: #6B7785; margin-bottom: 24px; }

    /* ── Buttons ──────────────────────────────────────── */
    .stButton > button[kind="primary"], .stFormSubmitButton > button { background-color: #FF690F !important; color: white !important; border: none !important; border-radius: 8px !important; padding: 0.6rem 2rem !important; font-weight: 600 !important; font-size: 15px !important; transition: all 0.2s ease !important; }
    .stFormSubmitButton > button:hover, .stButton > button[kind="primary"]:hover { background-color: #E85A00 !important; box-shadow: 0 4px 12px rgba(255,105,15,0.35) !important; }

    /* ── Cards ────────────────────────────────────────── */
    .venue-card { background: white; border: 1px solid #E8ECF0; border-radius: 12px; padding: 1.2rem 1.5rem; margin-bottom: 0.8rem; transition: all 0.2s ease; }
    .venue-card:hover { border-color: #FF690F; box-shadow: 0 2px 8px rgba(255,105,15,0.12); }
    .venue-card.selected { border-color: #FF690F; border-width: 2px; background: #FFF9F5; }
    .venue-card.pref-1 { border-left: 4px solid #FFD700; background: #FFFDF5; }
    .venue-card.pref-2 { border-left: 4px solid #C0C0C0; background: #FAFBFC; }
    .venue-card.pref-3 { border-left: 4px solid #CD7F32; background: #FDFAF7; }
    .venue-name { font-size: 18px; font-weight: 600; color: #192024; }
    .venue-meta { font-size: 14px; color: #6B7785; }
    .venue-badge { display: inline-block; background: #FFF3EB; color: #FF690F; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; margin-right: 6px; }
    .price-badge { display: inline-block; background: #E8F8EE; color: #1DB954; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
    .rank-badge { display: inline-flex; align-items: center; justify-content: center; width: 28px; height: 28px; border-radius: 50%; font-size: 14px; font-weight: 700; margin-right: 8px; flex-shrink: 0; }
    .rank-1 { background: #FFD700; color: #192024; }
    .rank-2 { background: #C0C0C0; color: #192024; }
    .rank-3 { background: #CD7F32; color: white; }
    .rank-other { background: #E4E8EC; color: #6B7785; }
    .pref-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 2px; }
    .pref-label-1 { color: #B8960F; }
    .pref-label-2 { color: #888; }
    .pref-label-3 { color: #8B5E3C; }

    /* ── Member Chips ─────────────────────────────────── */
    .member-chip { display: inline-flex; align-items: center; gap: 6px; background: #F5F7FA; border: 1px solid #E4E8EC; border-radius: 20px; padding: 6px 14px; margin: 4px; font-size: 14px; color: #363F45; }
    .member-chip .dot { width: 8px; height: 8px; border-radius: 50%; background: #1DB954; }

    /* ── Reorder Buttons ──────────────────────────────── */
    .reorder-btn { display: inline-flex; align-items: center; gap: 2px; background: #F5F7FA; border: 1px solid #E4E8EC; border-radius: 6px; padding: 2px 8px; font-size: 12px; color: #6B7785; cursor: pointer; }
    .reorder-btn:hover { background: #E8ECF0; color: #192024; }

    /* ── Unified Calendar ─────────────────────────────── */
    .cal-overlay { background: white; border: 1px solid #E8ECF0; border-radius: 12px; padding: 1rem 1.2rem; margin-bottom: 1rem; }
    .cal-header { font-size: 18px; font-weight: 700; color: #192024; margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px solid #F0F2F5; }
    .cal-grid { display: grid; gap: 2px; }
    .cal-grid-header { font-size: 14px; font-weight: 700; color: #192024; text-align: center; padding: 6px 0; }
    .cal-cell { height: 28px; border-radius: 3px; position: relative; }
    .cal-free { background: #F0F2F5; }
    .cal-busy { background: #FECACA; }
    .cal-chosen { background: #FEF3C7; }
    .cal-chosen-highlight { background: #D1FAE5; border-radius: 4px; box-shadow: 0 0 0 1px rgba(16,185,129,0.3); }
    .cal-hour-label { font-size: 11px; color: #8E99A4; text-align: right; padding-right: 6px; display: flex; align-items: center; justify-content: flex-end; }
    .cal-cell-label { font-size: 9px; padding: 2px 4px; position: absolute; top: 50%; transform: translateY(-50%); }
    .cal-cell-busy { color: #991B1B; }
    .cal-cell-chosen { color: #065F46; font-weight: 600; }

    /* ── Form Inputs ──────────────────────────────────── */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea { border-radius: 8px !important; border-color: #E4E8EC !important; }
    .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus { border-color: #FF690F !important; box-shadow: 0 0 0 1px #FF690F !important; }

    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    .hero { text-align: center; padding: 1rem 0 0.5rem 0; }
    .hero h1 { font-size: 32px; font-weight: 800; color: #192024; margin-bottom: 0; }
    .hero-accent { color: #FF690F; }
    .hero p { color: #6B7785; font-size: 16px; }

    /* ── Friends ──────────────────────────────────────── */
    .friend-card { display: flex; align-items: center; gap: 12px; background: white; border: 1px solid #E8ECF0; border-radius: 12px; padding: 12px 16px; margin-bottom: 8px; transition: all 0.2s ease; }
    .friend-card:hover { border-color: #FF690F; box-shadow: 0 2px 8px rgba(255,105,15,0.08); }
    .friend-avatar { width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 16px; font-weight: 700; color: white; flex-shrink: 0; }
    .friend-info { flex: 1; }
    .friend-name { font-size: 15px; font-weight: 600; color: #192024; }
    .friend-email { font-size: 13px; color: #6B7785; }
    .friend-badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
    .friend-badge-pending { background: #FFF3EB; color: #FF690F; }
    .friend-badge-accepted { background: #E8F8EE; color: #1DB954; }
    .friend-count { display: inline-flex; align-items: center; gap: 6px; background: #F5F7FA; border: 1px solid #E4E8EC; border-radius: 20px; padding: 4px 14px; font-size: 13px; color: #6B7785; font-weight: 500; }
    .friend-count .count-num { font-weight: 700; color: #FF690F; }
    .request-card { background: #FFFBF5; border: 1px solid #FFE0C2; border-radius: 12px; padding: 14px 16px; margin-bottom: 8px; }
    .friends-empty { text-align: center; padding: 2rem; color: #8E99A4; }
    .friends-empty-icon { font-size: 48px; margin-bottom: 8px; }
</style>
""", unsafe_allow_html=True)

# ── Session State ──────────────────────────────────────────────────────

STEPS = ["Create Group", "Preferences", "Calendar", "Find Venues", "Review & Plan", "Plan Summary", "Feedback"]

if "current_step" not in st.session_state:
    st.session_state.current_step = 0
if "group_id" not in st.session_state:
    st.session_state.group_id = None
    st.session_state.user_id = None
    st.session_state.members = []
if "completed_steps" not in st.session_state:
    st.session_state.completed_steps = set()
if "member_add_counter" not in st.session_state:
    st.session_state.member_add_counter = 0
if "orchestrator_result" not in st.session_state:
    st.session_state.orchestrator_result = None
if "show_friends_panel" not in st.session_state:
    st.session_state.show_friends_panel = False
if "friends_list" not in st.session_state:
    st.session_state.friends_list = []
if "friend_req_counter" not in st.session_state:
    st.session_state.friend_req_counter = 0
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None
    st.session_state.auth_user = None

# ── Pick up auth token from Google OAuth redirect ─────────────────────
_qp = st.query_params
if "auth_token" in _qp and not st.session_state.auth_token:
    _token = _qp["auth_token"]
    try:
        resp = httpx.get(
            f"{API_BASE}/auth/me",
            headers={"Authorization": f"Bearer {_token}"},
            timeout=5.0,
        )
        if resp.status_code == 200:
            user_data = resp.json()
            st.session_state.auth_token = _token
            st.session_state.auth_user = user_data
            st.session_state.user_id = user_data["id"]
            st.session_state.creator_user_id = user_data["id"]
    except Exception:
        pass
    st.query_params.clear()
    st.rerun()


def advance_step():
    st.session_state.completed_steps.add(st.session_state.current_step)
    if st.session_state.current_step < len(STEPS) - 1:
        st.session_state.current_step += 1


def go_to_step(idx):
    if idx in st.session_state.completed_steps or idx == st.session_state.current_step:
        st.session_state.current_step = idx


# ══════════════════════════════════════════════════════════════════════
# AUTH GATE — shown when user is not signed in
# ══════════════════════════════════════════════════════════════════════

if not st.session_state.auth_token:
    st.markdown(
        '<div class="hero"><h1>🎯 <span class="hero-accent">Rowboat</span></h1>'
        '<p>AI-powered group outing coordination — from preferences to a plan in under a minute</p></div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-card" style="max-width:480px;margin:0 auto;">'
                '<div class="section-title" style="text-align:center;">Welcome</div>'
                '<div class="section-subtitle" style="text-align:center;">Sign in to plan outings with your friends</div>'
                '</div>', unsafe_allow_html=True)

    auth_tab_google, auth_tab_email_login, auth_tab_email_signup = st.tabs([
        "Sign in with Google", "Email Login", "Create Account",
    ])

    with auth_tab_google:
        st.markdown("Sign in with your Google account to get started. "
                    "This also connects your **Google Calendar** automatically.")
        try:
            resp = httpx.get(f"{API_BASE}/auth/google/url", timeout=5.0)
            if resp.status_code == 200:
                google_url = resp.json().get("auth_url", "")
                if google_url:
                    st.link_button("🔗 Sign in with Google", google_url, use_container_width=True)
                else:
                    st.warning("Google OAuth is not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET.")
            else:
                st.warning("Could not get Google sign-in URL.")
        except Exception as e:
            st.error(f"Cannot reach backend: {e}")

    with auth_tab_email_login:
        with st.form("email_login"):
            login_email = st.text_input("Email")
            login_password = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In", type="primary"):
                if login_email and login_password:
                    try:
                        resp = httpx.post(
                            f"{API_BASE}/auth/login",
                            data={"username": login_email, "password": login_password},
                            timeout=10.0,
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            st.session_state.auth_token = data["access_token"]
                            st.session_state.auth_user = data["user"]
                            st.session_state.user_id = data["user"]["id"]
                            st.session_state.creator_user_id = data["user"]["id"]
                            st.rerun()
                        else:
                            detail = resp.json().get("detail", "Login failed")
                            st.error(detail)
                    except Exception as e:
                        st.error(f"Error: {e}")
        st.caption("Don't have an account? Use the **Create Account** tab.")

    with auth_tab_email_signup:
        st.markdown("Create an account with email. You can connect Google Calendar later from the Calendar step.")
        with st.form("email_signup"):
            reg_name = st.text_input("Full Name")
            reg_email = st.text_input("Email")
            reg_username = st.text_input("Username (optional)", placeholder="e.g. johndoe42",
                                         help="3-30 characters: letters, numbers, underscores. Friends can find you by this.")
            reg_password = st.text_input("Password", type="password")
            reg_password2 = st.text_input("Confirm Password", type="password")
            if st.form_submit_button("Create Account", type="primary"):
                if not reg_name or not reg_email or not reg_password:
                    st.error("Please fill in all required fields.")
                elif reg_password != reg_password2:
                    st.error("Passwords don't match.")
                elif len(reg_password) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    try:
                        payload = {
                            "name": reg_name,
                            "email": reg_email,
                            "password": reg_password,
                        }
                        if reg_username:
                            payload["username"] = reg_username
                        resp = httpx.post(f"{API_BASE}/auth/register", json=payload, timeout=10.0)
                        if resp.status_code == 200:
                            data = resp.json()
                            st.session_state.auth_token = data["access_token"]
                            st.session_state.auth_user = data["user"]
                            st.session_state.user_id = data["user"]["id"]
                            st.session_state.creator_user_id = data["user"]["id"]
                            st.rerun()
                        else:
                            detail = resp.json().get("detail", "Registration failed")
                            st.error(detail)
                    except Exception as e:
                        st.error(f"Error: {e}")

    st.stop()

# ══════════════════════════════════════════════════════════════════════
# USERNAME SETUP — shown once if user has no username
# ══════════════════════════════════════════════════════════════════════

auth_user = st.session_state.auth_user or {}
if not auth_user.get("username"):
    st.markdown(
        '<div class="hero"><h1>🎯 <span class="hero-accent">Rowboat</span></h1></div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-card" style="max-width:480px;margin:0 auto;">'
                '<div class="section-title">Choose a username</div>'
                '<div class="section-subtitle">Friends can find and add you by your username</div>'
                '</div>', unsafe_allow_html=True)

    with st.form("set_username"):
        new_username = st.text_input("Username", placeholder="e.g. johndoe42",
                                      help="3-30 characters: letters, numbers, underscores")
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.form_submit_button("Set Username", type="primary"):
                if new_username:
                    try:
                        resp = httpx.post(
                            f"{API_BASE}/auth/username",
                            json={"username": new_username},
                            headers={"Authorization": f"Bearer {st.session_state.auth_token}"},
                            timeout=10.0,
                        )
                        if resp.status_code == 200:
                            st.session_state.auth_user = resp.json()
                            st.rerun()
                        else:
                            detail = resp.json().get("detail", "Failed")
                            st.error(detail)
                    except Exception as e:
                        st.error(f"Error: {e}")
        with col2:
            if st.form_submit_button("Skip for now"):
                st.session_state.auth_user["username"] = "__skipped__"
                st.rerun()

    st.stop()


# ══════════════════════════════════════════════════════════════════════
# MAIN APP — user is authenticated
# ══════════════════════════════════════════════════════════════════════

# ── Hero + Stepper ─────────────────────────────────────────────────────

_display_name = auth_user.get("name", "")
_display_username = auth_user.get("username", "")
_username_tag = f' <span style="color:#6B7785;font-size:14px;">@{_display_username}</span>' if _display_username and _display_username != "__skipped__" else ""

st.markdown(
    f'<div class="hero"><h1>🎯 <span class="hero-accent">Outing</span> Planner</h1>'
    f'<p>Welcome back, <strong>{_display_name}</strong>{_username_tag}</p></div>',
    unsafe_allow_html=True,
)

# Sign-out button in the corner
_signout_col1, _signout_col2 = st.columns([6, 1])
with _signout_col2:
    if st.button("Sign Out", key="signout_btn"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# ── Avatar color helper ───────────────────────────────────────────────
_AVATAR_COLORS = ["#FF690F", "#1DB954", "#4A90D9", "#9B59B6", "#E74C3C", "#F39C12", "#1ABC9C", "#34495E"]


def _avatar_color(name: str) -> str:
    return _AVATAR_COLORS[sum(ord(c) for c in name) % len(_AVATAR_COLORS)]


def _register_current_user():
    """Register the current user with the friends API so they can be found by email."""
    uid = st.session_state.get("user_id")
    if not uid or not st.session_state.get("members"):
        return
    me = st.session_state.members[0]
    try:
        httpx.post(f"{API_BASE}/friends/register", json={
            "user_id": uid, "name": me["name"], "email": me["email"],
        }, timeout=5.0)
    except Exception:
        pass


def _refresh_friends():
    """Fetch the latest friends list from the API."""
    uid = st.session_state.get("user_id")
    if not uid:
        return
    try:
        resp = httpx.get(f"{API_BASE}/friends/{uid}/friends", timeout=5.0)
        resp.raise_for_status()
        st.session_state.friends_list = resp.json()
    except Exception:
        pass


# ── Friends Panel Toggle ──────────────────────────────────────────────

if st.session_state.get("user_id"):
    _refresh_friends()
    n_friends = len(st.session_state.friends_list)

    # Check for incoming requests
    incoming_requests = []
    try:
        resp = httpx.get(f"{API_BASE}/friends/{st.session_state.user_id}/requests/incoming", timeout=5.0)
        if resp.status_code == 200:
            incoming_requests = resp.json()
    except Exception:
        pass

    n_pending = len(incoming_requests)
    badge_html = f' <span style="background:#E74C3C;color:white;border-radius:50%;padding:1px 7px;font-size:11px;font-weight:700;">{n_pending}</span>' if n_pending else ""

    fcol1, fcol2 = st.columns([6, 1])
    with fcol2:
        btn_label = "👥 Friends" if not st.session_state.show_friends_panel else "✕ Close"
        if st.button(btn_label, key="toggle_friends", use_container_width=True):
            st.session_state.show_friends_panel = not st.session_state.show_friends_panel
            st.rerun()
    with fcol1:
        if n_friends or n_pending:
            st.markdown(
                f'<span class="friend-count"><span class="count-num">{n_friends}</span> friend{"s" if n_friends != 1 else ""}'
                f'{badge_html}</span>',
                unsafe_allow_html=True,
            )

    # ── Friends Management Panel ──────────────────────────────────────
    if st.session_state.show_friends_panel:
        st.markdown("---")
        st.markdown('<div class="section-card"><div class="section-title">👥 Friends</div>'
                    '<div class="section-subtitle">Manage your friends to quickly add them to outings</div></div>',
                    unsafe_allow_html=True)

        tab_friends, tab_requests, tab_add = st.tabs(["My Friends", f"Requests ({n_pending})", "Add Friend"])

        with tab_friends:
            if st.session_state.friends_list:
                for friend in st.session_state.friends_list:
                    fname = friend.get("name", "Unknown")
                    femail = friend.get("email", "")
                    fusername = friend.get("username", "")
                    fsubtitle = f"@{fusername}" if fusername else femail
                    color = _avatar_color(fname)
                    initial = fname[0].upper() if fname else "?"

                    fc1, fc2 = st.columns([8, 1])
                    with fc1:
                        st.markdown(
                            f'<div class="friend-card">'
                            f'<div class="friend-avatar" style="background:{color}">{initial}</div>'
                            f'<div class="friend-info"><div class="friend-name">{fname}</div>'
                            f'<div class="friend-email">{fsubtitle}</div></div>'
                            f'<span class="friend-badge friend-badge-accepted">Friends</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    with fc2:
                        if st.button("✕", key=f"rm_friend_{friend.get('id', fname)}", help="Remove friend"):
                            try:
                                httpx.delete(
                                    f"{API_BASE}/friends/{st.session_state.user_id}/friends/{friend['id']}",
                                    timeout=5.0,
                                )
                                _refresh_friends()
                                st.rerun()
                            except Exception:
                                st.error("Failed to remove friend")
            else:
                st.markdown(
                    '<div class="friends-empty"><div class="friends-empty-icon">👋</div>'
                    'No friends yet. Add some to get started!</div>',
                    unsafe_allow_html=True,
                )

        with tab_requests:
            if incoming_requests:
                for req in incoming_requests:
                    requester = req.get("requester", {})
                    rname = requester.get("name", "Unknown") if requester else "Unknown"
                    remail = requester.get("email", "") if requester else ""
                    color = _avatar_color(rname)
                    initial = rname[0].upper() if rname else "?"
                    fid = req.get("id")

                    st.markdown(
                        f'<div class="request-card">'
                        f'<div style="display:flex;align-items:center;gap:10px;">'
                        f'<div class="friend-avatar" style="background:{color}">{initial}</div>'
                        f'<div class="friend-info"><div class="friend-name">{rname}</div>'
                        f'<div class="friend-email">{remail}</div></div>'
                        f'<span class="friend-badge friend-badge-pending">Pending</span>'
                        f'</div></div>',
                        unsafe_allow_html=True,
                    )
                    rc1, rc2, _ = st.columns([1, 1, 4])
                    with rc1:
                        if st.button("✅ Accept", key=f"accept_{fid}", use_container_width=True):
                            try:
                                httpx.post(
                                    f"{API_BASE}/friends/{st.session_state.user_id}/respond/{fid}",
                                    json={"accept": True}, timeout=5.0,
                                )
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
                    with rc2:
                        if st.button("✕ Decline", key=f"decline_{fid}", use_container_width=True):
                            try:
                                httpx.post(
                                    f"{API_BASE}/friends/{st.session_state.user_id}/respond/{fid}",
                                    json={"accept": False}, timeout=5.0,
                                )
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {e}")
            else:
                st.info("No pending friend requests.")

            # Show outgoing
            outgoing_requests = []
            try:
                resp = httpx.get(f"{API_BASE}/friends/{st.session_state.user_id}/requests/outgoing", timeout=5.0)
                if resp.status_code == 200:
                    outgoing_requests = resp.json()
            except Exception:
                pass
            if outgoing_requests:
                st.caption("**Sent requests**")
                for req in outgoing_requests:
                    addressee = req.get("addressee", {})
                    aname = addressee.get("name", "Unknown") if addressee else "Unknown"
                    aemail = addressee.get("email", "") if addressee else ""
                    st.markdown(
                        f'<span class="member-chip">⏳ {aname} ({aemail})</span>',
                        unsafe_allow_html=True,
                    )

        with tab_add:
            st.markdown("Add a friend by their **username** or **email address**.")
            form_key = f"add_friend_{st.session_state.friend_req_counter}"
            with st.form(form_key):
                add_method = st.radio("Find by", ["Username", "Email"], horizontal=True, label_visibility="collapsed")
                if add_method == "Username":
                    friend_username = st.text_input("Username", placeholder="e.g. johndoe42")
                    friend_email = ""
                else:
                    friend_email = st.text_input("Email", placeholder="friend@example.com")
                    friend_username = ""
                send_btn = st.form_submit_button("Send Friend Request", type="primary")
                if send_btn and (friend_email or friend_username):
                    try:
                        payload = {}
                        if friend_username:
                            payload["to_username"] = friend_username
                        else:
                            payload["to_email"] = friend_email
                        resp = httpx.post(
                            f"{API_BASE}/friends/{st.session_state.user_id}/request",
                            json=payload, timeout=5.0,
                        )
                        resp.raise_for_status()
                        target_display = f"@{friend_username}" if friend_username else friend_email
                        st.success(f"Friend request sent to {target_display}!")
                        st.session_state.friend_req_counter += 1
                        st.rerun()
                    except httpx.HTTPStatusError as e:
                        detail = e.response.json().get("detail", str(e))
                        st.error(detail)
                    except Exception as e:
                        st.error(f"Error: {e}")

        st.markdown("---")


def render_stepper():
    cur = st.session_state.current_step
    done = st.session_state.completed_steps
    html = '<div class="stepper-container">'
    for i, name in enumerate(STEPS):
        if i > 0:
            html += f'<div class="step-connector {"done" if i-1 in done else ""}"></div>'
        cls = "active" if i == cur else ("completed" if i in done else "")
        html += f'<div class="step-item {cls}"><span class="step-number">{"✓" if i in done else i+1}</span>{name}</div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


render_stepper()

done = st.session_state.completed_steps
if done:
    cols = st.columns(len(STEPS))
    for i in range(len(STEPS)):
        if i in done and i != st.session_state.current_step:
            with cols[i]:
                if st.button(f"← {STEPS[i]}", key=f"nav_{i}", use_container_width=True):
                    go_to_step(i)
                    st.rerun()

step = st.session_state.current_step


# ════════════════════════════════════════════════════════════════════════
# STEP 0: CREATE GROUP
# ════════════════════════════════════════════════════════════════════════
if step == 0:
    st.markdown('<div class="section-card"><div class="section-title">Create Your Group</div>'
                '<div class="section-subtitle">Start by naming your group and adding your friends</div></div>',
                unsafe_allow_html=True)

    if st.session_state.group_id is None:
        _me = st.session_state.auth_user or {}
        _my_name = _me.get("name", "")
        _my_email = _me.get("email", "")
        _my_uid = _me.get("id", st.session_state.get("user_id", ""))
        _my_uname = _me.get("username", "")
        _uname_display = f" (@{_my_uname})" if _my_uname and _my_uname != "__skipped__" else ""

        st.markdown(f"Creating group as **{_my_name}**{_uname_display} ({_my_email})")

        with st.form("create_group"):
            group_name = st.text_input("Group Name", placeholder="Friday Night Crew")
            submitted = st.form_submit_button("Create Group", type="primary")
            if submitted and group_name:
                try:
                    resp = httpx.post(f"{API_BASE}/groups/",
                                     json={"name": group_name, "creator_name": _my_name, "creator_email": _my_email})
                    resp.raise_for_status()
                    data = resp.json()
                    creator_uid = data["member_ids"][0]
                    st.session_state.group_id = data["id"]
                    st.session_state.user_id = creator_uid
                    st.session_state.creator_user_id = creator_uid
                    st.session_state.members = [{"name": _my_name, "email": _my_email, "user_id": creator_uid}]
                    if "member_user_ids" not in st.session_state:
                        st.session_state.member_user_ids = {}
                    st.session_state.member_user_ids[_my_name] = creator_uid
                    _register_current_user()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    else:
        members_html = "".join(f'<span class="member-chip"><span class="dot"></span>{m["name"]}</span>' for m in st.session_state.members)
        st.markdown(f"**Group Members:** {members_html}", unsafe_allow_html=True)

        form_key = f"add_member_{st.session_state.member_add_counter}"
        with st.form(form_key):
            c1, c2, c3 = st.columns([2, 2, 1])
            with c1:
                name = st.text_input("Name", placeholder="Friend's name")
            with c2:
                email = st.text_input("Email", placeholder="friend@email.com")
            with c3:
                st.write("")
                add = st.form_submit_button("Add")
            if add and name and email:
                try:
                    resp = httpx.post(f"{API_BASE}/groups/{st.session_state.group_id}/members",
                                     json={"name": name, "email": email})
                    resp.raise_for_status()
                    data = resp.json()
                    # The newest member_id is the last one in the list
                    new_uid = data["member_ids"][-1] if data.get("member_ids") else ""
                    st.session_state.members.append({"name": name, "email": email, "user_id": new_uid})
                    if "member_user_ids" not in st.session_state:
                        st.session_state.member_user_ids = {}
                    st.session_state.member_user_ids[name] = new_uid
                    st.session_state.member_add_counter += 1
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        # ── Quick Add from Friends ────────────────────────────────────
        if st.session_state.friends_list:
            current_emails = {m.get("email", "").lower() for m in st.session_state.members}
            available_friends = [
                f for f in st.session_state.friends_list
                if f.get("email", "").lower() not in current_emails
            ]
            if available_friends:
                with st.expander("⚡ Quick Add from Friends", expanded=True):
                    st.caption("Click to instantly add a friend to this group")
                    for friend in available_friends:
                        fname = friend.get("name", "Unknown")
                        femail = friend.get("email", "")
                        color = _avatar_color(fname)
                        initial = fname[0].upper() if fname else "?"

                        af1, af2 = st.columns([6, 1])
                        with af1:
                            st.markdown(
                                f'<div class="friend-card">'
                                f'<div class="friend-avatar" style="background:{color}">{initial}</div>'
                                f'<div class="friend-info"><div class="friend-name">{fname}</div>'
                                f'<div class="friend-email">{femail}</div></div>'
                                f'</div>',
                                unsafe_allow_html=True,
                            )
                        with af2:
                            if st.button("+ Add", key=f"qadd_{friend.get('id', fname)}", use_container_width=True):
                                try:
                                    resp = httpx.post(
                                        f"{API_BASE}/groups/{st.session_state.group_id}/members",
                                        json={"name": fname, "email": femail},
                                    )
                                    resp.raise_for_status()
                                    st.session_state.members.append({"name": fname, "email": femail})
                                    st.session_state.member_add_counter += 1
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")

        # Mini calendar status
        calendars_connected = st.session_state.get("calendars_connected", {})
        if calendars_connected and any(calendars_connected.values()):
            with st.expander("📅 Calendar Status", expanded=False):
                for m in st.session_state.members:
                    uid = m.get("user_id", "")
                    connected = calendars_connected.get(uid, False)
                    icon = "🟢" if connected else "⚪"
                    status = "Connected" if connected else "Not connected"
                    st.caption(f"{icon} **{m['name']}** — {status}")

        st.divider()

        if len(st.session_state.members) >= 2:
            # ── Quick Plan (Orchestrator) ──
            st.markdown("""<div style="background: linear-gradient(135deg, #FFF5ED, #FFF0E0);
                border: 2px solid #FF690F; border-radius: 16px; padding: 24px; margin: 16px 0;">
                <h3 style="margin:0 0 8px 0; color: #FF690F;">⚡ Quick Plan</h3>
                <p style="margin:0; color: #6B7785; font-size: 14px;">
                Let our AI orchestrator handle everything — just describe what you want and it'll find venues,
                check availability, rank options, and build your itinerary in one shot.</p>
            </div>""", unsafe_allow_html=True)

            with st.form("quick_plan_form"):
                quick_request = st.text_input(
                    "What are you planning?",
                    placeholder="e.g., Bowling night with dinner and drinks for the group",
                )
                qp_col1, qp_col2, qp_col3 = st.columns(3)
                with qp_col1:
                    qp_location = st.text_input("Location", value="Pittsburgh, PA")
                with qp_col2:
                    qp_date_start = st.date_input("From", value=datetime.today() + timedelta(days=1))
                with qp_col3:
                    qp_date_end = st.date_input("To", value=datetime.today() + timedelta(days=7))

                qp_submit = st.form_submit_button("⚡ Plan It!", type="primary", use_container_width=True)

                if qp_submit and quick_request:
                    with st.spinner("🤖 Orchestrator working — coordinating Search, Calendar, and Recommendation agents..."):
                        try:
                            # Build preferences from session if available
                            prefs_payload = []
                            if st.session_state.get("preferences"):
                                prefs_payload = [st.session_state["preferences"]]

                            payload = {
                                "request": quick_request,
                                "group_name": st.session_state.get("group_name", "My Group"),
                                "members": st.session_state.members,
                                "preferences": prefs_payload,
                                "location": qp_location,
                                "date_range_start": qp_date_start.isoformat(),
                                "date_range_end": qp_date_end.isoformat(),
                                "earliest_time": "09:00",
                                "latest_time": "23:00",
                            }
                            resp = httpx.post(f"{API_BASE}/plans/orchestrate", json=payload, timeout=120.0)
                            resp.raise_for_status()
                            st.session_state.orchestrator_result = resp.json()
                            st.rerun()
                        except Exception as e:
                            st.error(f"Orchestrator failed: {e}")

            # Show orchestrator results
            if st.session_state.get("orchestrator_result"):
                plan = st.session_state.orchestrator_result
                st.markdown("---")
                st.markdown("### 🎯 Orchestrator Results")

                # Agent log (collapsible)
                with st.expander("🤖 Agent Coordination Log", expanded=True):
                    for log_entry in plan.get("agent_log", []):
                        if "[Search]" in log_entry:
                            st.markdown(f"🔍 {log_entry}")
                        elif "[Calendar]" in log_entry:
                            st.markdown(f"📅 {log_entry}")
                        elif "[Recommend]" in log_entry:
                            st.markdown(f"⭐ {log_entry}")
                        elif "[Itinerary]" in log_entry:
                            st.markdown(f"📋 {log_entry}")
                        elif "[Parse]" in log_entry:
                            st.markdown(f"🧠 {log_entry}")
                        else:
                            st.markdown(f"⚙️ {log_entry}")

                # Recommended venue + slot
                rec_venue = plan.get("recommended_venue")
                rec_slot = plan.get("recommended_slot")
                if rec_venue:
                    st.markdown(f"""<div class="venue-card pref-1" style="margin-top:16px;">
                        <div style="font-size:11px; color:#FF690F; font-weight:700; text-transform:uppercase; margin-bottom:4px;">
                            ⚡ AI RECOMMENDED
                        </div>
                        <span class="rank-badge" style="background:#FFD700; color:#333;">★</span>
                        <span class="venue-name" style="font-size:18px; font-weight:700;">{rec_venue.get('name','')}</span>
                        <span class="venue-badge">{rec_venue.get('price_tier','$$')}</span><br>
                        <span class="venue-meta">📍 {rec_venue.get('address','')}</span><br>
                        <span class="venue-meta">⭐ {rec_venue.get('rating', 'N/A')} &nbsp;|&nbsp;
                        Score: {rec_venue.get('score', 0)}% match</span><br>
                        <span class="venue-meta">💰 {plan.get('estimated_cost_per_person', '')}</span>
                    </div>""", unsafe_allow_html=True)

                if rec_slot:
                    slot_weekend = "🌴 Weekend" if rec_slot.get("is_weekend") else "💼 Weekday"
                    st.markdown(f"""<div class="venue-card" style="margin-top:8px; border-left: 4px solid #1DB954;">
                        <span class="venue-name">📅 {rec_slot.get('day', '')} {rec_slot.get('date', '')}</span>
                        <span class="venue-badge">{slot_weekend}</span><br>
                        <span class="venue-meta">🕐 {rec_slot.get('start_time', '')} – {rec_slot.get('end_time', '')}</span>
                    </div>""", unsafe_allow_html=True)

                # Summary
                if plan.get("itinerary_summary"):
                    st.success(f"📋 {plan['itinerary_summary']}")

                # Stats
                sc1, sc2, sc3, sc4 = st.columns(4)
                with sc1:
                    st.metric("Venues Found", plan.get("venues_found", 0))
                with sc2:
                    st.metric("Ranked", len(plan.get("ranked_venues", [])))
                with sc3:
                    st.metric("Rejected", len(plan.get("rejected_venues", [])))
                with sc4:
                    st.metric("Time Slots", len(plan.get("available_slots", [])))

                # All ranked venues (collapsible)
                ranked = plan.get("ranked_venues", [])
                if ranked:
                    with st.expander(f"📊 All {len(ranked)} Ranked Venues"):
                        for i, sv in enumerate(ranked):
                            v = sv.get("venue", {})
                            score = round(sv.get("score", 0) * 100)
                            score_color = "#1DB954" if score >= 70 else ("#FF690F" if score >= 40 else "#E53E3E")
                            cats = " · ".join(sv.get("venue", {}).get("categories", []))
                            st.markdown(f"""<div class="venue-card">
                                <span class="rank-badge rank-other">{i+1}</span>
                                <span class="venue-name">{v.get('name','')}</span>
                                <span style="background:{score_color}; color:white; padding:2px 8px;
                                    border-radius:12px; font-size:12px; font-weight:600;">{score}%</span>
                                <span class="venue-badge">{v.get('price_tier','')}</span><br>
                                <span class="venue-meta">📍 {v.get('address','')}</span><br>
                                <span class="venue-meta">{cats}</span><br>
                                <span class="venue-meta" style="color:#6B7785; font-style:italic;">
                                    {sv.get('explanation','')}</span>
                            </div>""", unsafe_allow_html=True)

                # Accept plan button
                if rec_venue and rec_slot:
                    st.divider()
                    bc1, bc2 = st.columns([1, 1])
                    with bc1:
                        if st.button("✅ Accept This Plan", type="primary", use_container_width=True):
                            st.session_state["accepted_plan"] = plan
                            st.session_state.current_step = 5  # Plan Summary step
                            st.session_state.completed_steps.update({0, 1, 2, 3, 4})
                            st.rerun()
                    with bc2:
                        st.caption("You can send calendar invites on the next screen.")

                # Option to continue with manual flow
                st.divider()
                st.caption("Want more control? Customize your plan step-by-step below.")

        # Manual continue button
        _, col2 = st.columns([3, 1])
        with col2:
            if len(st.session_state.members) >= 1:
                if st.button("Customize Step-by-Step →", type="primary", use_container_width=True):
                    advance_step()
                    st.rerun()


# ════════════════════════════════════════════════════════════════════════
# STEP 1: PREFERENCES
# ════════════════════════════════════════════════════════════════════════
elif step == 1:
    st.markdown('<div class="section-card"><div class="section-title">Set Preferences</div>'
                '<div class="section-subtitle">Tell us what everyone enjoys so we can find the perfect outing</div></div>',
                unsafe_allow_html=True)

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
        if st.form_submit_button("Save Preferences & Continue →"):
            budget_map = {BUDGET_OPTIONS[0]: "$", BUDGET_OPTIONS[1]: "$$", BUDGET_OPTIONS[2]: "$$$", BUDGET_OPTIONS[3]: "$$$$"}
            st.session_state["user_preferences"] = {
                "cuisine_preferences": [c.lower() for c in cuisines],
                "activity_preferences": [a.lower() for a in activities],
                "dietary_restrictions": [d.lower().replace(" ", "_") for d in dietary if d != "None"],
                "budget_max": budget_map[budget],
                "dealbreakers": [d.strip() for d in dealbreakers.split("\n") if d.strip()],
                "preferred_neighborhoods": [n.strip() for n in neighborhoods.split(",") if n.strip()],
            }
            advance_step()
            st.rerun()


# ════════════════════════════════════════════════════════════════════════
# STEP 2: CALENDAR
# ════════════════════════════════════════════════════════════════════════
elif step == 2:
    st.markdown('<div class="section-card"><div class="section-title">Find Availability</div>'
                '<div class="section-subtitle">Connect calendars and set time constraints to find when everyone is free</div></div>',
                unsafe_allow_html=True)

    if "calendars_connected" not in st.session_state:
        st.session_state.calendars_connected = {}

    members = st.session_state.get("members", [])

    # Check real calendar connection status for each member via the API
    member_user_ids = st.session_state.get("member_user_ids", {})
    for member in members:
        nm = member["name"]
        uid = member_user_ids.get(nm) or member.get("user_id", "")
        if uid and nm not in st.session_state.calendars_connected:
            try:
                status_resp = httpx.get(f"{API_BASE}/calendar/status/{uid}", timeout=5.0)
                if status_resp.status_code == 200:
                    st.session_state.calendars_connected[nm] = status_resp.json().get("connected", False)
            except Exception:
                pass

    all_connected = all(st.session_state.calendars_connected.get(m["name"], False) for m in members)

    st.subheader("📅 Connect Calendars")

    if not all_connected:
        st.info("Connect your Google Calendar for real availability data. Members without a connected calendar will be assumed free.")

    for member in members:
        nm = member["name"]
        connected = st.session_state.calendars_connected.get(nm, False)
        uid = member_user_ids.get(nm) or member.get("user_id", "")
        col1, col2 = st.columns([4, 1])
        with col1:
            if connected:
                st.markdown(f'<span class="member-chip"><span class="dot"></span>{nm} — Connected ✓</span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<span class="member-chip">{nm} — Not connected</span>', unsafe_allow_html=True)
        with col2:
            if not connected and uid:
                try:
                    auth_resp = httpx.get(f"{API_BASE}/calendar/auth-url", params={"user_id": uid}, timeout=5.0)
                    if auth_resp.status_code == 200:
                        auth_url = auth_resp.json().get("auth_url", "")
                        if auth_url:
                            st.link_button("Connect Google", auth_url, use_container_width=True)
                except Exception:
                    if st.button("Connect", key=f"cal_{nm}"):
                        st.session_state.calendars_connected[nm] = True
                        st.rerun()
            elif not connected:
                if st.button("Skip (assume free)", key=f"cal_{nm}"):
                    st.session_state.calendars_connected[nm] = True
                    st.rerun()

    st.divider()

    # [FIX 3] Date + Time constraints with overnight wrap-around
    st.subheader("🕐 Date & Time Range")
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Search from", value=datetime.now().date() + timedelta(days=1))
        earliest_time = st.time_input("Earliest start time", value=dt_time(9, 0))
    with col2:
        end_date = st.date_input("Search to", value=datetime.now().date() + timedelta(days=7))
        latest_time = st.time_input("Latest end time", value=dt_time(23, 0))

    wraps_overnight = latest_time.hour < earliest_time.hour or (latest_time.hour == 0 and earliest_time.hour > 0)
    if wraps_overnight:
        st.caption(f"⏰ End time wraps to next day — slots will run from {earliest_time.strftime('%I:%M %p')} to {latest_time.strftime('%I:%M %p')} (+1 day)")

    min_hours = st.slider("Minimum outing duration (hours)", 1, 6, 2)

    if st.button("🔍 Find Available Times", type="primary"):
        member_user_ids = st.session_state.get("member_user_ids", {})
        user_ids_list = []
        for m in members:
            uid = member_user_ids.get(m["name"]) or m.get("user_id", "")
            if uid:
                user_ids_list.append(uid)

        # Try the real calendar availability API first
        api_slots = []
        use_real_api = bool(user_ids_list)
        if use_real_api:
            try:
                avail_resp = httpx.post(
                    f"{API_BASE}/calendar/availability",
                    json={
                        "user_ids": user_ids_list,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                        "min_duration_hours": float(min_hours),
                        "preferred_start_hour": earliest_time.hour,
                        "preferred_end_hour": latest_time.hour,
                    },
                    timeout=30.0,
                )
                if avail_resp.status_code == 200:
                    avail_data = avail_resp.json()
                    api_slots = avail_data.get("slots", [])
                    connected = avail_data.get("connected_users", [])
                    simulated = avail_data.get("simulated_users", [])
                    if connected:
                        st.success(f"Real calendar data used for: {', '.join(connected)}")
                    if simulated:
                        st.caption(f"Assumed always free (no calendar connected): {', '.join(simulated)}")
            except Exception:
                use_real_api = False

        # Build slot list from API response or fallback to local generation
        slots = []
        if api_slots:
            for s in api_slots:
                sd = datetime.fromisoformat(s["start_iso"])
                ed = datetime.fromisoformat(s["end_iso"])
                slot_start_hour = sd.hour
                slot_end_hour = ed.hour if ed.date() == sd.date() else ed.hour + 24

                busy_per_member = {m["name"]: [] for m in members}
                slots.append({
                    "start": sd.isoformat(),
                    "end": ed.isoformat(),
                    "start_h": slot_start_hour,
                    "end_h": slot_end_hour,
                    "users": [m["name"] for m in members],
                    "busy_per_member": busy_per_member,
                })
        else:
            current = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.min.time())
            while current <= end_dt:
                slot_start_hour = earliest_time.hour
                if wraps_overnight:
                    slot_end_hour = latest_time.hour + 24
                else:
                    slot_end_hour = latest_time.hour

                duration = slot_end_hour - slot_start_hour
                if duration >= min_hours:
                    busy_per_member = {m["name"]: [] for m in members}

                    actual_end = current.replace(hour=slot_end_hour % 24)
                    if wraps_overnight:
                        actual_end += timedelta(days=1)

                    slots.append({
                        "start": current.replace(hour=slot_start_hour).isoformat(),
                        "end": actual_end.isoformat(),
                        "start_h": slot_start_hour,
                        "end_h": slot_end_hour,
                        "users": [m["name"] for m in members],
                        "busy_per_member": busy_per_member,
                    })
                current += timedelta(days=1)

        st.session_state["available_slots"] = slots
        if "slot_order" in st.session_state:
            del st.session_state["slot_order"]

    # Slot reordering with venue-card style
    if "available_slots" in st.session_state:
        slots = st.session_state["available_slots"]
        st.subheader(f"Found {len(slots)} time slots — reorder your preferences")
        st.caption("Use the ▲ ▼ buttons to rank your preferred time slots. Top 3 are highlighted with gold, silver, and bronze.")

        # Maintain ordering in session state
        if "slot_order" not in st.session_state or len(st.session_state["slot_order"]) != len(slots):
            st.session_state["slot_order"] = list(range(len(slots)))

        order = st.session_state["slot_order"]

        for pos, slot_idx in enumerate(order):
            s = slots[slot_idx]
            sd = datetime.fromisoformat(s["start"])
            ed = datetime.fromisoformat(s["end"])
            dur = (ed - sd).total_seconds() / 3600
            day_str = sd.strftime("%A, %b %d")
            time_str = f"{sd.strftime('%I:%M %p')} – {ed.strftime('%I:%M %p')}"
            members_str = ", ".join(s.get("users", []))
            weekend = "🌴 Weekend" if sd.weekday() >= 5 else "💼 Weekday"

            # Card styling — top 3 get medal highlights
            pref_cls = ""
            pref_label = ""
            rank_cls = "rank-other"
            if pos == 0:
                pref_cls = "pref-1"
                pref_label = '<div class="pref-label pref-label-1">🥇 1st preference</div>'
                rank_cls = "rank-1"
            elif pos == 1:
                pref_cls = "pref-2"
                pref_label = '<div class="pref-label pref-label-2">🥈 2nd preference</div>'
                rank_cls = "rank-2"
            elif pos == 2:
                pref_cls = "pref-3"
                pref_label = '<div class="pref-label pref-label-3">🥉 3rd preference</div>'
                rank_cls = "rank-3"

            card_col, btn_col = st.columns([10, 1])
            with card_col:
                st.markdown(
                    f'<div class="venue-card {pref_cls}">'
                    f'{pref_label}'
                    f'<span class="rank-badge {rank_cls}">{pos+1}</span>'
                    f'<span class="venue-name">📅 {day_str}</span> '
                    f'<span class="venue-badge">{weekend}</span><br>'
                    f'<span class="venue-meta">🕐 {time_str} ({dur:.0f}h)</span><br>'
                    f'<span class="venue-meta">👥 {members_str}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            with btn_col:
                if pos > 0:
                    if st.button("▲", key=f"slot_up_{pos}"):
                        order[pos], order[pos-1] = order[pos-1], order[pos]
                        st.rerun()
                if pos < len(order) - 1:
                    if st.button("▼", key=f"slot_down_{pos}"):
                        order[pos], order[pos+1] = order[pos+1], order[pos]
                        st.rerun()

        st.session_state["slot_rankings"] = order

        st.divider()
        _, col2 = st.columns([3, 1])
        with col2:
            if st.button("Continue →", type="primary", key="cal_continue", use_container_width=True):
                advance_step()
                st.rerun()


# ════════════════════════════════════════════════════════════════════════
# STEP 3: FIND VENUES
# ════════════════════════════════════════════════════════════════════════
elif step == 3:
    st.markdown('<div class="section-card"><div class="section-title">Find Venues</div>'
                '<div class="section-subtitle">Tell us what you\'re looking for and our AI will search for the best options</div></div>',
                unsafe_allow_html=True)

    with st.form("plan_search"):
        query = st.text_area("What are you looking for?",
                             placeholder="Italian dinner followed by bowling or an escape room. Budget around $30/person.", height=100)
        col1, col2 = st.columns(2)
        with col1:
            location = st.text_input("Location", value="Pittsburgh, PA")
        with col2:
            max_results = st.slider("Max results", 3, 20, 8)
        submitted = st.form_submit_button("🔍  Search Venues")

    if submitted and query:
        with st.spinner("AI agent is searching for venues..."):
            try:
                resp = httpx.post(f"{API_BASE}/plans/search",
                                 json={"query": query, "location": location, "max_results": max_results}, timeout=60.0)
                resp.raise_for_status()
                search_data = resp.json()
                st.session_state["search_result"] = search_data
                if "venue_order" in st.session_state:
                    del st.session_state["venue_order"]
                if "venue_scores" in st.session_state:
                    del st.session_state["venue_scores"]
            except Exception as e:
                st.error(f"Search failed: {e}")

        # Run constraint solver on search results
        if "search_result" in st.session_state:
            search_data = st.session_state["search_result"]
            raw_venues = search_data.get("venues", [])
            if raw_venues:
                with st.spinner("🧠 Scoring venues against group preferences..."):
                    try:
                        user_prefs = st.session_state.get("user_preferences", {})
                        members = st.session_state.get("members", [])
                        prefs_list = []
                        for _ in members:
                            prefs_list.append(user_prefs)

                        rec_resp = httpx.post(f"{API_BASE}/plans/recommend",
                            json={
                                "venues": raw_venues,
                                "preferences": prefs_list,
                                "group_id": st.session_state.get("group_id", ""),
                                "budget_max": user_prefs.get("budget_max", "$$"),
                                "dietary_restrictions": user_prefs.get("dietary_restrictions", []),
                                "dealbreakers": user_prefs.get("dealbreakers", []),
                                "member_names": [m["name"] for m in members],
                            }, timeout=90.0)
                        rec_resp.raise_for_status()
                        rec_data = rec_resp.json()

                        # Store scores keyed by venue name for display
                        score_map = {}
                        for sv in rec_data.get("ranked_venues", []):
                            vn = sv.get("venue", {}).get("name", "")
                            score_map[vn] = {
                                "score": sv.get("score", 0),
                                "breakdown": sv.get("score_breakdown", {}),
                                "explanation": sv.get("explanation", ""),
                            }
                        for sv in rec_data.get("rejected_venues", []):
                            vn = sv.get("venue", {}).get("name", "")
                            score_map[vn] = {
                                "score": 0,
                                "breakdown": sv.get("score_breakdown", {}),
                                "explanation": sv.get("explanation", ""),
                            }
                        st.session_state["venue_scores"] = score_map
                        if rec_data.get("rag_insights"):
                            st.session_state["rag_insights"] = rec_data["rag_insights"]

                        # Re-sort venues by constraint score (best first)
                        scored_order = sorted(
                            range(len(raw_venues)),
                            key=lambda i: score_map.get(raw_venues[i].get("name", ""), {}).get("score", 0),
                            reverse=True,
                        )
                        st.session_state["venue_order"] = scored_order

                    except Exception as e:
                        st.info("Showing venues in order of relevance.")

    if "search_result" in st.session_state:
        result = st.session_state["search_result"]
        if result.get("summary"):
            st.info(result["summary"])

        # Show RAG insights if available
        rag_insights = st.session_state.get("rag_insights")
        if rag_insights:
            st.caption(f"🧠 {rag_insights}")

        venues = result.get("venues", [])
        score_map = st.session_state.get("venue_scores", {})

        if venues:
            st.subheader(f"{len(venues)} venues found — ranked by group fit")
            st.caption("Venues are auto-ranked by how well they match your group's preferences. Use ▲ ▼ to adjust. Top 3 are highlighted.")

            # Maintain ordering in session state
            if "venue_order" not in st.session_state or len(st.session_state["venue_order"]) != len(venues):
                st.session_state["venue_order"] = list(range(len(venues)))

            v_order = st.session_state["venue_order"]

            for pos, vi in enumerate(v_order):
                venue = venues[vi]
                cats = venue.get("categories", [])
                price = venue.get("price_tier", "")
                rating_val = venue.get("rating", 0)
                rating = f"{'⭐' * int(rating_val)}" if rating_val else ""
                addr = venue.get("address", "")

                # Get constraint score
                v_score_info = score_map.get(venue.get("name", ""), {})
                v_score = v_score_info.get("score", -1)
                v_explanation = v_score_info.get("explanation", "")
                v_breakdown = v_score_info.get("breakdown", {})
                rejected = v_score == 0 and "hard_constraint_violations" in v_breakdown

                pref_cls = ""
                pref_label = ""
                rank_cls = "rank-other"
                if rejected:
                    pref_cls = ""
                    pref_label = '<div class="pref-label" style="color:#DC2626;font-size:11px;">❌ CONSTRAINT VIOLATION</div>'
                elif pos == 0:
                    pref_cls = "pref-1"
                    pref_label = '<div class="pref-label pref-label-1">🥇 1st preference</div>'
                    rank_cls = "rank-1"
                elif pos == 1:
                    pref_cls = "pref-2"
                    pref_label = '<div class="pref-label pref-label-2">🥈 2nd preference</div>'
                    rank_cls = "rank-2"
                elif pos == 2:
                    pref_cls = "pref-3"
                    pref_label = '<div class="pref-label pref-label-3">🥉 3rd preference</div>'
                    rank_cls = "rank-3"

                cat_badges = "".join(f'<span class="venue-badge">{c}</span>' for c in cats[:3])
                price_html = f'<span class="price-badge">{price}</span>' if price else ""

                # Score badge
                score_html = ""
                if v_score >= 0:
                    score_pct = int(v_score * 100)
                    if score_pct >= 70:
                        score_color = "#1DB954"
                    elif score_pct >= 40:
                        score_color = "#FF9500"
                    else:
                        score_color = "#DC2626"
                    score_html = (
                        f'<span style="float:right;background:{score_color};color:white;'
                        f'padding:2px 10px;border-radius:12px;font-size:12px;font-weight:600;">'
                        f'{score_pct}% match</span>'
                    )

                card_opacity = "opacity:0.5;" if rejected else ""

                card_col, btn_col = st.columns([10, 1])
                with card_col:
                    st.markdown(
                        f'<div class="venue-card {pref_cls}" style="{card_opacity}">'
                        f'{pref_label}'
                        f'<span class="rank-badge {rank_cls}">{pos+1}</span>'
                        f'<span class="venue-name">{venue["name"]}</span> {price_html} {score_html}'
                        f'<span class="venue-meta" style="margin-left:8px">{rating}</span><br>'
                        f'<span class="venue-meta">📍 {addr}</span><br>'
                        f'{cat_badges}'
                        f'<div style="font-size:11px;color:#8E99A4;margin-top:4px;">{v_explanation}</div>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
                with btn_col:
                    if pos > 0:
                        if st.button("▲", key=f"venue_up_{pos}"):
                            v_order[pos], v_order[pos-1] = v_order[pos-1], v_order[pos]
                            st.rerun()
                    if pos < len(v_order) - 1:
                        if st.button("▼", key=f"venue_down_{pos}"):
                            v_order[pos], v_order[pos+1] = v_order[pos+1], v_order[pos]
                            st.rerun()

            st.session_state["venue_rankings"] = v_order

            st.divider()
            _, col2 = st.columns([3, 1])
            with col2:
                if st.button("Continue to Review →", type="primary", key="venue_continue", use_container_width=True):
                    advance_step()
                    st.rerun()
        else:
            st.warning("No venues found. Try a different search.")


# ════════════════════════════════════════════════════════════════════════
# STEP 4: REVIEW & BOOK
# ════════════════════════════════════════════════════════════════════════
elif step == 4:
    st.markdown('<div class="section-card"><div class="section-title">Review & Plan</div>'
                '<div class="section-subtitle">Review your selections with calendar and map views, then finalize your plan</div></div>',
                unsafe_allow_html=True)

    search_result = st.session_state.get("search_result")
    slots = st.session_state.get("available_slots", [])
    slot_rankings = st.session_state.get("slot_rankings", [])
    venue_rankings = st.session_state.get("venue_rankings", [])

    if not search_result or not venue_rankings:
        st.warning("Complete previous steps first.")
        st.stop()

    venues = search_result.get("venues", [])
    ranked_venues = [venues[i] for i in venue_rankings if i < len(venues)]
    ranked_slots = [slots[i] for i in slot_rankings if i < len(slots)] if slot_rankings and slots else []
    members = st.session_state.get("members", [])
    user_prefs = st.session_state.get("user_preferences", {})
    preferred_cuisines = [c.lower() for c in user_prefs.get("cuisine_preferences", [])]

    # [FIX 3] Only use slots where ALL members are free
    valid_slots = []
    for s in ranked_slots:
        busy_per = s.get("busy_per_member", {})
        start_h = s.get("start_h", datetime.fromisoformat(s["start"]).hour)
        end_h = s.get("end_h", datetime.fromisoformat(s["end"]).hour)
        all_free = True
        for m in members:
            for b in busy_per.get(m["name"], []):
                if b["start"] <= start_h and b["end"] >= end_h:
                    all_free = False
                    break
            if not all_free:
                break
        if all_free:
            valid_slots.append(s)

    # Build itinerary items — each venue paired with ALL valid slots
    itinerary_items = []
    for vi, venue in enumerate(ranked_venues):
        itinerary_items.append({"venue": venue, "slots": valid_slots, "idx": vi})

    # Per-venue selected slot stored in session state
    if "venue_slot_choices" not in st.session_state:
        st.session_state.venue_slot_choices = {}
    if "hover_idx" not in st.session_state:
        st.session_state.hover_idx = 0
    if "selected_booking" not in st.session_state:
        st.session_state.selected_booking = None

    left_col, right_col = st.columns([3, 2])

    with left_col:
        st.subheader("Your Itinerary")
        st.caption("Click on a card to select your venue. The right panel previews the focused card.")
        tier_cost = {"$": 12, "$$": 25, "$$$": 55, "$$$$": 90}

        for item in itinerary_items:
            v = item["venue"]
            available_slots = item["slots"]
            idx = item["idx"]
            cost = tier_cost.get(v.get("price_tier", ""), 20)

            # Determine which slot is chosen for this venue
            chosen_slot_idx = st.session_state.venue_slot_choices.get(idx, 0)
            if chosen_slot_idx >= len(available_slots):
                chosen_slot_idx = 0
            s = available_slots[chosen_slot_idx] if available_slots else None

            rank_cls = f"rank-{idx+1}" if idx < 3 else "rank-other"
            slot_str = ""
            if s:
                sd = datetime.fromisoformat(s["start"])
                ed = datetime.fromisoformat(s["end"])
                slot_str = f"{sd.strftime('%a %b %d, %I:%M %p')} – {ed.strftime('%I:%M %p')}"

            price_html = f'<span class="price-badge">{v.get("price_tier","")}</span>' if v.get("price_tier") else ""

            # Category + cuisine badges
            cat_badges = "".join(f'<span class="venue-badge">{c}</span>' for c in v.get("categories", [])[:2])
            venue_cats_lower = [c.lower() for c in v.get("categories", [])]
            venue_name_lower = v.get("name", "").lower()
            cuisine_matches = [c.title() for c in preferred_cuisines if c in venue_cats_lower or c in venue_name_lower]
            cuisine_badges = "".join(f'<span class="venue-badge" style="background:#E8F8EE;color:#1DB954">🍽️ {c}</span>' for c in cuisine_matches)

            is_selected = st.session_state.selected_booking == idx
            is_viewing = st.session_state.hover_idx == idx
            card_cls = "venue-card selected" if is_selected else ("venue-card" + (" selected" if is_viewing else ""))

            selected_marker = ""
            if is_selected:
                selected_marker = '<span style="float:right;background:#1DB954;color:white;padding:2px 10px;border-radius:12px;font-size:12px;font-weight:600;">✓ Selected</span>'

            st.markdown(f"""<div class="{card_cls}">
                <span class="rank-badge {rank_cls}">{idx+1}</span>
                <span class="venue-name">{v['name']}</span> {price_html} {selected_marker}<br>
                <span class="venue-meta">📍 {v.get('address','Address TBD')}</span><br>
                <span class="venue-meta">🕐 {slot_str}</span><br>
                {cat_badges}{cuisine_badges}
                <span class="venue-meta" style="float:right">~${cost}/person</span>
            </div>""", unsafe_allow_html=True)

            # Time slot dropdown if multiple slots available
            btn_cols = st.columns([2, 1, 1]) if len(available_slots) > 1 else st.columns([1, 1])
            col_i = 0
            if len(available_slots) > 1:
                with btn_cols[col_i]:
                    slot_options = []
                    for si, sl in enumerate(available_slots):
                        ssd = datetime.fromisoformat(sl["start"])
                        sed = datetime.fromisoformat(sl["end"])
                        slot_options.append(f"{ssd.strftime('%a %b %d, %I:%M %p')} – {sed.strftime('%I:%M %p')}")
                    new_choice = st.selectbox(
                        "Time slot", slot_options, index=chosen_slot_idx,
                        key=f"slot_choice_{idx}", label_visibility="collapsed"
                    )
                    new_idx = slot_options.index(new_choice)
                    if new_idx != chosen_slot_idx:
                        st.session_state.venue_slot_choices[idx] = new_idx
                        st.rerun()
                col_i += 1

            with btn_cols[col_i]:
                if st.button("🔍 Preview" if not is_viewing else "✦ Viewing", key=f"hover_{idx}",
                             use_container_width=True, disabled=is_viewing):
                    st.session_state.hover_idx = idx
                    st.rerun()
            with btn_cols[col_i + 1]:
                if is_selected:
                    st.button("✓ Selected", key=f"sel_{idx}", use_container_width=True, disabled=True)
                else:
                    if st.button("📌 Select", key=f"sel_{idx}", use_container_width=True):
                        st.session_state.selected_booking = idx
                        st.session_state.hover_idx = idx
                        st.rerun()

    with right_col:
        active = itinerary_items[st.session_state.hover_idx] if itinerary_items else None

        # Calendar overlay — all members side-by-side, chosen slot highlighted
        if active and active["slots"]:
            active_slot_idx = st.session_state.venue_slot_choices.get(active["idx"], 0)
            if active_slot_idx >= len(active["slots"]):
                active_slot_idx = 0
            slot = active["slots"][active_slot_idx]
            sd = datetime.fromisoformat(slot["start"])
            ed = datetime.fromisoformat(slot["end"])
            busy_per_member = slot.get("busy_per_member", {})
            start_h = slot.get("start_h", sd.hour)
            end_h = slot.get("end_h", ed.hour)
            if end_h <= start_h:
                end_h = ed.hour + 24 if ed.hour < start_h else ed.hour

            # Determine which hours everyone is free (the "chosen" window)
            member_names = [m["name"] for m in members]
            n_members = len(member_names)

            # Find the contiguous block where ALL members are free
            all_free_hours = set()
            for h in range(start_h, end_h):
                everyone_free = True
                for nm in member_names:
                    member_busy = busy_per_member.get(nm, [])
                    if any(b["start"] <= h < b["end"] for b in member_busy):
                        everyone_free = False
                        break
                if everyone_free:
                    all_free_hours.add(h)

            cal_html = f'<div class="cal-overlay">'
            cal_html += f'<div class="cal-header">📅 {sd.strftime("%A, %B %d")} — Group Calendar</div>'

            grid_cols = f"50px {'1fr ' * n_members}"
            cal_html += f'<div class="cal-grid" style="grid-template-columns: {grid_cols};">'
            cal_html += '<div class="cal-grid-header"></div>'
            for nm in member_names:
                cal_html += f'<div class="cal-grid-header" style="font-size:15px;font-weight:700;">{nm}</div>'

            for h in range(start_h, end_h):
                display_h = h % 24
                h_label = f"{display_h % 12 or 12}{'pm' if display_h >= 12 else 'am'}"
                cal_html += f'<div class="cal-hour-label">{h_label}</div>'

                for nm in member_names:
                    member_busy = busy_per_member.get(nm, [])
                    is_busy = any(b["start"] <= h < b["end"] for b in member_busy)

                    if is_busy:
                        cal_html += '<div class="cal-cell cal-busy"><span class="cal-cell-label cal-cell-busy">Busy</span></div>'
                    elif h in all_free_hours:
                        # Everyone free — prominent green highlight for the chosen slot
                        cal_html += '<div class="cal-cell cal-chosen-highlight"></div>'
                    else:
                        # Available for this member but not everyone — light green
                        cal_html += '<div class="cal-cell" style="background:#E8F8EE;border-radius:3px;"></div>'

            cal_html += '</div>'

            # Legend inside the overlay
            cal_html += """<div style="display:flex;gap:16px;margin:12px 0 4px 0;font-size:12px;color:#6B7785">
                <span><span style="display:inline-block;width:12px;height:12px;border-radius:3px;background:#D1FAE5;border:1px solid rgba(16,185,129,0.3);margin-right:4px;vertical-align:middle"></span>Everyone free</span>
                <span><span style="display:inline-block;width:12px;height:12px;border-radius:3px;background:#E8F8EE;margin-right:4px;vertical-align:middle"></span>Available</span>
                <span><span style="display:inline-block;width:12px;height:12px;border-radius:3px;background:#FECACA;margin-right:4px;vertical-align:middle"></span>Busy</span>
            </div>"""

            cal_html += '</div>'
            st.markdown(cal_html, unsafe_allow_html=True)

        # [FIX 6] Google Maps embed iframe
        if active:
            v = active["venue"]
            addr = v.get("address", "")
            venue_name = v.get("name", "")
            query_str = urllib.parse.quote(f"{venue_name}, {addr}")

            st.markdown(f"""<div class="cal-overlay">
                <div class="cal-header">📍 {venue_name}</div>
                <iframe width="100%" height="250" style="border:0; border-radius:8px;"
                    loading="lazy" allowfullscreen referrerpolicy="no-referrer-when-downgrade"
                    src="https://www.google.com/maps/embed/v1/search?key={MAPS_EMBED_KEY}&q={query_str}">
                </iframe>
                <div class="venue-meta" style="margin-top:8px">{addr}</div>
            </div>""", unsafe_allow_html=True)

    st.divider()
    sel_idx = st.session_state.selected_booking
    if sel_idx is None:
        st.warning("👆 Please select a venue above to finalize your plan.")
    else:
        chosen = itinerary_items[sel_idx]
        chosen_v = chosen["venue"]
        chosen_slot_idx = st.session_state.venue_slot_choices.get(sel_idx, 0)
        if chosen_slot_idx >= len(valid_slots):
            chosen_slot_idx = 0
        chosen_s = valid_slots[chosen_slot_idx] if valid_slots else None
        chosen_cost = tier_cost.get(chosen_v.get("price_tier", ""), 20)
        slot_str = ""
        if chosen_s:
            sd = datetime.fromisoformat(chosen_s["start"])
            ed = datetime.fromisoformat(chosen_s["end"])
            slot_str = f"{sd.strftime('%a %b %d, %I:%M %p')} – {ed.strftime('%I:%M %p')}"

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅  Confirm Plan & Send Calendar Invites", type="primary", use_container_width=True):
                st.session_state["booked"] = True
                st.session_state["booked_venues"] = [chosen_v]
                st.session_state["booked_item"] = {
                    "venue": chosen_v,
                    "slot": chosen_s,
                    "slot_str": slot_str,
                    "cost": chosen_cost,
                }
                st.session_state["booked_members"] = [m["name"] for m in members]
                st.session_state["booked_total_cost"] = chosen_cost
                st.balloons()
                advance_step()
                st.rerun()
        with col2:
            # Deep-link to venue on Google Maps for manual reservation
            venue_name = chosen_v.get("name", "")
            venue_addr = chosen_v.get("address", "")
            maps_query = urllib.parse.quote(f"{venue_name} {venue_addr}")
            st.link_button("📍 Open on Google Maps", f"https://www.google.com/maps/search/?api=1&query={maps_query}", use_container_width=True)


# ════════════════════════════════════════════════════════════════════════
# STEP 5: BOOKING SUMMARY
# ════════════════════════════════════════════════════════════════════════
elif step == 5:
    accepted_plan = st.session_state.get("accepted_plan")
    booked_item = st.session_state.get("booked_item", {})
    already_booked = st.session_state.get("booking_confirmed", False)

    members = st.session_state.get("members", [])
    member_names = [m["name"] for m in members]
    creator_user_id = st.session_state.get("creator_user_id", "")
    organizer_connected = st.session_state.get("calendars_connected", {}).get(creator_user_id, False)

    # Determine venue/slot from either accepted plan or manual flow
    venue = None
    slot = None
    slot_str = ""
    cost_per_person = 0
    start_iso = ""
    end_iso = ""

    if accepted_plan:
        venue = accepted_plan.get("recommended_venue", {})
        slot = accepted_plan.get("recommended_slot", {})
        slot_str = f"{slot.get('day', '')} {slot.get('date', '')} — {slot.get('start_time', '')} to {slot.get('end_time', '')}"
        start_iso = slot.get("start_iso", "")
        end_iso = slot.get("end_iso", "")
        cost_str = accepted_plan.get("estimated_cost_per_person", "")
        # Parse cost string like "~$25/person" to number
        import re
        cost_match = re.search(r"\$(\d+)", str(cost_str))
        cost_per_person = int(cost_match.group(1)) if cost_match else 0
    elif booked_item:
        venue = booked_item.get("venue", {})
        slot = booked_item.get("slot", {})
        slot_str = booked_item.get("slot_str", "")
        cost_per_person = st.session_state.get("booked_total_cost", 0)

    if not venue:
        st.warning("No plan selected. Go back and generate a plan first.")
        st.stop()

    # Header depends on plan state
    if already_booked:
        st.markdown('<div class="section-card"><div class="section-title">🎉 Plan Confirmed!</div>'
                    '<div class="section-subtitle">Here\'s a summary of your group outing plan</div></div>',
                    unsafe_allow_html=True)
        if st.session_state.get("calendar_invites_sent"):
            st.success("Calendar invites have been sent to all group members!")
        else:
            st.success("Plan confirmed! Connect Google Calendar to send invites automatically.")
    else:
        st.markdown('<div class="section-card"><div class="section-title">📋 Confirm & Coordinate</div>'
                    '<div class="section-subtitle">Confirm your outing details and send calendar invites</div></div>',
                    unsafe_allow_html=True)

    # Group info
    members_html = "".join(f'<span class="member-chip"><span class="dot"></span>{m}</span>' for m in member_names)
    st.markdown(f"**Group:** {members_html}", unsafe_allow_html=True)

    st.divider()
    st.subheader("📋 Plan Details")

    cats = venue.get("categories", [])
    badges = "".join(f'<span class="venue-badge">{c}</span>' for c in cats[:3])
    price_html = f'<span class="venue-badge">{venue.get("price_tier","")}</span>' if venue.get("price_tier") else ""
    rating_val = venue.get("rating")
    rating_stars = f"{'⭐' * int(float(rating_val))}" if rating_val else ""

    card_lines = [
        f'<span class="venue-name" style="font-size:22px;">{venue.get("name", "Venue")}</span> {price_html}',
        f'<span class="venue-meta" style="font-size:15px;">📍 {venue.get("address", "Address TBD")}</span>',
        f'<span class="venue-meta" style="font-size:15px;">🕐 {slot_str}</span>',
    ]
    if rating_stars:
        card_lines.append(f'<span class="venue-meta">{rating_stars}</span>')
    if badges:
        card_lines.append(badges)
    card_html = "<br>".join(card_lines)

    st.markdown(f'<div class="venue-card selected" style="border-width:2px;">{card_html}</div>', unsafe_allow_html=True)

    # Google Maps embed for the venue
    addr = venue.get("address", "")
    venue_name = venue.get("name", "")
    query_str = urllib.parse.quote(f"{venue_name}, {addr}")
    if MAPS_EMBED_KEY:
        st.markdown(f"""<div class="cal-overlay">
            <div class="cal-header">📍 Location</div>
            <iframe width="100%" height="220" style="border:0; border-radius:8px;"
                loading="lazy" allowfullscreen referrerpolicy="no-referrer-when-downgrade"
                src="https://www.google.com/maps/embed/v1/search?key={MAPS_EMBED_KEY}&q={query_str}">
            </iframe>
        </div>""", unsafe_allow_html=True)

    # Venue deep-links for manual reservation
    maps_link = f"https://www.google.com/maps/search/?api=1&query={query_str}"
    yelp_link = f"https://www.yelp.com/search?find_desc={urllib.parse.quote(venue_name)}&find_loc={urllib.parse.quote(addr)}"
    link_cols = st.columns(3)
    with link_cols[0]:
        st.link_button("📍 Google Maps", maps_link, use_container_width=True)
    with link_cols[1]:
        st.link_button("⭐ Search on Yelp", yelp_link, use_container_width=True)
    with link_cols[2]:
        google_q = urllib.parse.quote(f"{venue_name} {addr} reservations")
        st.link_button("🔗 Find Reservations", f"https://www.google.com/search?q={google_q}", use_container_width=True)

    st.divider()

    # Cost summary
    n_members = len(member_names)
    if cost_per_person > 0:
        st.markdown(f"""
        <div class="section-card" style="background: #FFF9F5; border-color: #FF690F;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <div>
                    <div style="font-size:14px; color:#6B7785;">Estimated cost per person</div>
                    <div style="font-size:28px; font-weight:700; color:#FF690F;">~${cost_per_person}</div>
                </div>
                <div>
                    <div style="font-size:14px; color:#6B7785;">Group total ({n_members} people)</div>
                    <div style="font-size:28px; font-weight:700; color:#192024;">~${cost_per_person * n_members}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.divider()

    # Plan confirmation action
    if not already_booked:
        attendee_emails = [m.get("email", "") for m in members if m.get("email")]
        attendee_emails = [e for e in attendee_emails if e]

        if attendee_emails:
            st.caption(f"Calendar invites will be sent to: {', '.join(attendee_emails)}")

        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            if organizer_connected and start_iso and end_iso:
                if st.button("📅 Confirm & Send Calendar Invites", type="primary", use_container_width=True):
                    with st.spinner("Creating calendar event..."):
                        try:
                            api_base = API_BASE.replace("/api", "")
                            resp = httpx.post(
                                f"{api_base}/api/calendar/book",
                                json={
                                    "organizer_user_id": creator_user_id,
                                    "group_id": st.session_state.get("group_id", ""),
                                    "venue_name": venue.get("name", ""),
                                    "venue_address": venue.get("address", ""),
                                    "start_time": start_iso,
                                    "end_time": end_iso,
                                    "attendee_emails": attendee_emails,
                                },
                                timeout=30.0,
                            )
                            resp.raise_for_status()
                            result = resp.json()

                            st.session_state["booking_confirmed"] = True
                            st.session_state["calendar_invites_sent"] = True
                            st.balloons()
                            st.success(result.get("message", "Plan confirmed!"))
                            if result.get("calendar_link"):
                                st.markdown(f"[Open in Google Calendar]({result['calendar_link']})")
                            st.rerun()
                        except httpx.HTTPStatusError as e:
                            detail = e.response.json().get("detail", str(e))
                            st.error(f"Failed: {detail}")
                        except Exception as e:
                            st.error(f"Failed: {e}")
            else:
                if st.button("✅ Confirm Plan", type="primary", use_container_width=True):
                    st.session_state["booking_confirmed"] = True
                    st.balloons()
                    st.success("Plan confirmed!")
                    if not organizer_connected:
                        st.info("Connect your Google Calendar to send calendar invites automatically.")
                    st.rerun()
        with bc2:
            # Deep-link to venue for manual reservation
            v_name = venue.get("name", "")
            v_addr = venue.get("address", "")
            maps_q = urllib.parse.quote(f"{v_name} {v_addr}")
            st.link_button("📍 Open on Google Maps", f"https://www.google.com/maps/search/?api=1&query={maps_q}", use_container_width=True)
        with bc3:
            if st.button("← Back", use_container_width=True):
                st.session_state.current_step = 0
                st.rerun()

    st.divider()
    _, col2 = st.columns([3, 1])
    with col2:
        if already_booked:
            if st.button("Continue to Feedback →", type="primary", key="summary_continue", use_container_width=True):
                advance_step()
                st.rerun()


# ════════════════════════════════════════════════════════════════════════
# STEP 6: FEEDBACK
# ════════════════════════════════════════════════════════════════════════
elif step == 6:
    st.markdown('<div class="section-card"><div class="section-title">How Was It?</div>'
                '<div class="section-subtitle">Rate your outing to help us improve future plans</div></div>',
                unsafe_allow_html=True)

    booked = st.session_state.get("booked_venues", [])
    if not booked:
        st.info("No planned outings to review yet.")
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
            st.session_state["feedback"] = {
                "overall_rating": overall, "venue_ratings": venue_ratings,
                "would_repeat": would_repeat == "Yes", "free_text": free_text,
            }
            st.success("Thank you for your feedback! This will improve future outings.")


# ── Debug ──────────────────────────────────────────────────────────────
with st.expander("Debug Info", expanded=False):
    st.json({
        "current_step": st.session_state.current_step,
        "completed_steps": list(st.session_state.completed_steps),
        "group_id": st.session_state.get("group_id"),
        "members": st.session_state.get("members", []),
        "slot_rankings": st.session_state.get("slot_rankings", []),
        "venue_rankings": st.session_state.get("venue_rankings", []),
    })
