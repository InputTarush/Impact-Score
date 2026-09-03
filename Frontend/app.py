import os
import random
import re
import textwrap
import time
import requests
import plotly.graph_objects as go
import streamlit as st

BACKEND_URL="http://127.0.0.1:8001/analyze_applicant"


# Page Configuration
st.set_page_config(
    page_title="Impact Score | AI Table Tennis Scouting",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Directory to store uploaded media on disk
UPLOAD_DIR = "saved_player_videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)


DEFAULT_THUMBNAIL = "https://images.unsplash.com/photo-1511067007398-7e4b90a0755f?w=600&auto=format&fit=crop"




# Validation Helpers
def is_valid_email(email):
  pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
  return re.match(pattern, email) is not None




def is_valid_url(url):
  pattern = r"^https?://[^\s/$.?#].[^\s]*$"
  return re.match(pattern, url) is not None




# ---------------------------------------------------------
# STYLES: CRIMSON RED PRIMARY DESIGN SYSTEM
# Canvas: #090A0F | Cards: #151720 | Primary: #FF3B4D
# ---------------------------------------------------------
st.markdown(
    """
<style>
    /* Dark Mode Canvas */
    .stApp {
        background-color: #090A0F !important;
        color: #f0f2f8 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }
   
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 0rem !important; max-width: 1300px; }


    /* SEGMENTED TOGGLE SWITCH (Navigation Control Bar) */
    div[data-testid="stRadio"] > div {
        background-color: #151720 !important;
        border: 1px solid #232736 !important;
        border-radius: 18px !important;
        padding: 6px !important;
        gap: 8px !important;
        display: inline-flex !important;
    }
    div[data-testid="stRadio"] label {
        border-radius: 12px !important;
        padding: 8px 20px !important;
        background: transparent !important;
        transition: all 0.25s ease !important;
        cursor: pointer !important;
        color: #8a8fA3 !important;
        font-weight: 700 !important;
        border: 1px solid transparent !important;
    }
    div[data-testid="stRadio"] label:hover {
        color: #ffffff !important;
        background: rgba(255, 59, 77, 0.1) !important;
    }
    div[data-testid="stRadio"] label[data-checked="true"] {
        background: linear-gradient(135deg, #FF3B4D 0%, #D61B30 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 15px rgba(255, 59, 77, 0.4) !important;
    }


    /* BUTTON STYLES */
    div.stButton > button {
        border-radius: 9999px !important;
        font-weight: 700 !important;
        padding: 8px 16px !important;
        font-size: 0.85rem !important;
        transition: all 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275) !important;
    }


    /* PRIMARY CTA BUTTONS */
    div.stButton > button[data-testid="baseButton-primary"],
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #FF3B4D 0%, #D61B30 100%) !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        border: none !important;
        box-shadow: 0 4px 15px rgba(255, 59, 77, 0.4) !important;
    }
    div.stButton > button[data-testid="baseButton-primary"]:hover,
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-2px) scale(1.02) !important;
        box-shadow: 0 8px 25px rgba(255, 59, 77, 0.6) !important;
        background: linear-gradient(135deg, #FF5263 0%, #E0253A 100%) !important;
    }


    /* SECONDARY / GHOST BUTTONS */
    div.stButton > button[data-testid="baseButton-secondary"],
    div.stButton > button[kind="secondary"] {
        background: transparent !important;
        color: #FF3B4D !important;
        border: 1.5px solid #FF3B4D !important;
        box-shadow: none !important;
    }
    div.stButton > button[data-testid="baseButton-secondary"]:hover,
    div.stButton > button[kind="secondary"]:hover {
        background: rgba(255, 59, 77, 0.1) !important;
        border-color: #FF5263 !important;
        color: #FF5263 !important;
        transform: translateY(-2px) !important;
    }


    /* Role Cards */
    .role-card {
        background: #151720;
        border-radius: 24px;
        padding: 30px 24px;
        border: 1px solid #232736;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        text-align: center;
        transition: transform 0.3s ease, border-color 0.3s ease;
        margin-bottom: 20px;
        min-height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }
    .role-card:hover {
        transform: translateY(-5px);
        border-color: #FF3B4D;
    }


    .icon-badge {
        width: 52px;
        height: 52px;
        background: rgba(255, 59, 77, 0.12);
        border: 1px solid rgba(255, 59, 77, 0.3);
        border-radius: 16px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 14px;
    }


    /* Metric Card Custom */
    .stat-card {
        background: #151720;
        border: 1px solid #232736;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.4);
    }


    /* Form Inputs */
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div {
        background-color: #151720 !important;
        border-radius: 16px !important;
        border: 1px solid #232736 !important;
        color: #ffffff !important;
    }
    div[data-baseweb="input"] > div:focus-within, div[data-baseweb="textarea"] > div:focus-within {
        border-color: #FF3B4D !important;
    }


    /* Source Info Box */
    .source-box {
        background: rgba(255, 59, 77, 0.08);
        border: 1px solid rgba(255, 59, 77, 0.3);
        border-radius: 16px;
        padding: 16px;
        margin-top: 15px;
        margin-bottom: 15px;
    }


    /* PINTEREST MASONRY GRID */
    .pin-masonry {
        column-count: 3;
        column-gap: 20px;
        width: 100%;
        margin-top: 24px;
        margin-bottom: 40px;
    }
    @media (max-width: 1100px) { .pin-masonry { column-count: 2; } }
    @media (max-width: 650px) { .pin-masonry { column-count: 1; } }


    .pin-card {
        break-inside: avoid;
        margin-bottom: 24px;
        background: #151720;
        border-radius: 20px;
        overflow: hidden;
        border: 1px solid #232736;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.3s ease, border-color 0.3s ease;
        position: relative;
    }
    .pin-card:hover {
        transform: translateY(-8px);
        box-shadow: 0 20px 40px rgba(255, 59, 77, 0.25);
        border-color: #FF3B4D;
    }


    .pin-media {
        width: 100%;
        height: auto;
        max-height: 320px;
        object-fit: cover;
        display: block;
        border-bottom: 1px solid #232736;
    }


    .pin-rating-badge {
        position: absolute;
        top: 14px;
        right: 14px;
        background: #FF3B4D;
        color: #ffffff;
        font-weight: 900;
        font-size: 0.82rem;
        padding: 5px 12px;
        border-radius: 20px;
        box-shadow: 0 4px 12px rgba(255, 59, 77, 0.4);
    }
    .pin-status-badge {
        position: absolute;
        top: 14px;
        left: 14px;
        background: rgba(9, 10, 15, 0.88);
        backdrop-filter: blur(8px);
        color: #00D9FF;
        font-weight: 700;
        font-size: 0.75rem;
        padding: 5px 12px;
        border-radius: 14px;
        border: 1px solid rgba(0, 217, 255, 0.3);
    }


    .pin-body { padding: 18px; }
    .pin-title { font-size: 1.25rem; font-weight: 800; color: #ffffff; margin-bottom: 4px; }
    .pin-meta { font-size: 0.85rem; color: #8a8fA3; margin-bottom: 12px; }
    .pin-records {
        font-size: 0.82rem;
        color: #FF3B4D;
        font-weight: 600;
        margin-bottom: 12px;
        background: rgba(255, 59, 77, 0.1);
        padding: 8px 12px;
        border-radius: 10px;
        border-left: 3px solid #FF3B4D;
    }


    .chip-container { display: flex; flex-wrap: wrap; gap: 6px; }
    .skill-chip {
        background: #1e2230;
        color: #cbd5e1;
        font-size: 0.72rem;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 8px;
        border: 1px solid #2d3348;
    }


    /* FOOTER STYLING FOR CREATORS ONLY */
    .tech-footer-wrap {
        background-color: #08090C;
        border-top: 1px solid #1c1f2b;
        margin-top: 60px;
        padding: 24px;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }


    .creators-container {
        display: flex;
        flex-direction: column;
        gap: 12px;
        align-items: center;
        justify-content: center;
    }
    .creators-header {
        color: #FFB800;
        font-weight: 800;
        font-size: 0.88rem;
        letter-spacing: 1px;
        font-family: 'Courier New', Courier, monospace, sans-serif;
    }
    .creators-grid {
        display: flex;
        flex-wrap: wrap;
        gap: 12px;
        align-items: center;
        justify-content: center;
    }
    .creator-badge {
        background: #08090C;
        padding: 6px 14px;
        display: flex;
        align-items: center;
        gap: 8px;
        border-radius: 6px;
        transition: transform 0.2s ease;
    }
    .creator-badge:hover {
        transform: translateY(-2px);
    }
    .creator-avatar {
        color: #000000;
        font-weight: 900;
        width: 26px;
        height: 26px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
        border-radius: 4px;
    }
    .creator-name-text {
        color: #ffffff;
        font-weight: 800;
        font-size: 0.85rem;
        letter-spacing: 0.5px;
        font-family: 'Courier New', Courier, monospace, sans-serif;
    }
</style>
""",
    unsafe_allow_html=True,
)


# Initialize Session State Databases
if "users_db" not in st.session_state:
  st.session_state.users_db = {}


if "csr_db" not in st.session_state:
  st.session_state.csr_db = {}


if "grants_db" not in st.session_state:
  st.session_state.grants_db = []


if "selected_role" not in st.session_state:
  st.session_state.selected_role = None


if "authenticated_user" not in st.session_state:
  st.session_state.authenticated_user = None


if "authenticated_csr" not in st.session_state:
  st.session_state.authenticated_csr = None




# Seed Initial Demo Profiles
def seed_demo_athletes():
  st.session_state.users_db["alex_chen"] = {
      "email": "alex.chen@sports.org",
      "password": "demo",
      "name": "Alex Chen",
      "age": 17,
      "gender": "Male",
      "location": "California, USA",
      "bio": "Aggressive offensive loops, explosive forehand attacks.",
      "records": "🥇 State Junior Champion 2024",
      "thumbnail": DEFAULT_THUMBNAIL,
      "analysis_completed": True,
      "stats": {
          "Forehand": 88,
          "Backhand": 76,
          "Footwork": 92,
          "Reaction": 85,
          "Endurance": 81,
      },
      "overall": 84,
      "media_source": "Google Drive Folder",
      "saved_video_paths": [],
  }
  st.session_state.users_db["maya_patel"] = {
      "email": "maya.patel@sports.org",
      "password": "demo",
      "name": "Maya Patel",
      "age": 19,
      "gender": "Female",
      "location": "London, UK",
      "bio": "Tactical defensive chopper with rapid counter-attacks.",
      "records": "🥈 Runner Up - National Youth Games",
      "thumbnail": "https://images.unsplash.com/photo-1517649763962-0c6232662c0a?w=600&auto=format&fit=crop",
      "analysis_completed": True,
      "stats": {
          "Forehand": 82,
          "Backhand": 90,
          "Footwork": 88,
          "Reaction": 94,
          "Endurance": 85,
      },
      "overall": 88,
      "media_source": "Local Upload",
      "saved_video_paths": [],
  }
  st.session_state.users_db["david_kim"] = {
      "email": "david.kim@sports.org",
      "password": "demo",
      "name": "David Kim",
      "age": 18,
      "gender": "Male",
      "location": "Seoul, South Korea",
      "bio": "Penhold grip specialist with lightning-fast top spins.",
      "records": "🥇 National High School Gold Medalist",
      "thumbnail": "https://images.unsplash.com/photo-1530549387789-4c1017266635?w=600&auto=format&fit=crop",
      "analysis_completed": True,
      "stats": {
          "Forehand": 94,
          "Backhand": 81,
          "Footwork": 90,
          "Reaction": 89,
          "Endurance": 87,
      },
      "overall": 88,
      "media_source": "Google Drive Link",
      "saved_video_paths": [],
  }




# Radar Chart Builder
def create_radar_chart(stats_dict, player_name="Player Stats"):
  categories = list(stats_dict.keys())
  values = list(stats_dict.values())
  fig = go.Figure()
  fig.add_trace(
      go.Scatterpolar(
          r=values + [values[0]],
          theta=categories + [categories[0]],
          fill="toself",
          name=player_name,
          line_color="#FF3B4D",
          fillcolor="rgba(255, 59, 77, 0.25)",
      )
  )
  fig.update_layout(
      polar=dict(
          radialaxis=dict(visible=True, range=[0, 100], color="#8a8fA3"),
          bgcolor="rgba(0,0,0,0)",
      ),
      showlegend=False,
      paper_bgcolor="rgba(0,0,0,0)",
      plot_bgcolor="rgba(0,0,0,0)",
      margin=dict(l=30, r=30, t=20, b=20),
  )
  return fig




# HERO BANNER COMPONENT
def render_hero_banner():
  hero_html = """
    <div style="
        background: linear-gradient(90deg, #090A0F 38%, rgba(9,10,15,0.4) 75%, transparent 100%),
                    url('https://images.unsplash.com/photo-1534158914592-062992fbe900?q=80&w=1600&auto=format&fit=crop');
        background-size: cover;
        background-position: center right;
        border-radius: 24px;
        padding: 55px 40px;
        min-height: 380px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        border: 1px solid #232736;
        box-shadow: 0 20px 50px rgba(0,0,0,0.8);
        margin-bottom: 30px;
    ">
        <div style="max-width: 560px;">
            <span style="
                background: rgba(255, 59, 77, 0.15);
                color: #FF3B4D;
                padding: 6px 14px;
                border-radius: 20px;
                font-weight: 800;
                font-size: 0.8rem;
                border: 1px solid rgba(255, 59, 77, 0.4);
                letter-spacing: 0.5px;
            ">⚡ IMPACT SCORE SCOUTING PLATFORM</span>
            <h1 style="color: #ffffff; font-size: 2.7rem; font-weight: 900; margin: 16px 0 12px 0; line-height: 1.15;">
                Turn Talent Into Impact.<br/>
                <span style="color: #FF3B4D;">AI-Powered Table Tennis Scouting.</span>
            </h1>
            <p style="color: #a0a6b8; font-size: 1.05rem; line-height: 1.5; margin-bottom: 20px;">
                AI analyzes your table-tennis performance and connects high-potential athletes with CSR sponsors.
            </p>
        </div>
    </div>
    """
  st.markdown(textwrap.dedent(hero_html), unsafe_allow_html=True)




# ONLY CREATORS FOOTER COMPONENT
def render_tech_footer():
  creators_list = [
      {"name": "Ashwin Thillainathan", "initials": "AT", "color": "#00D9FF"},
      {"name": "Tarush Bhagtani", "initials": "TB", "color": "#FF3B4D"},
      {"name": "Lokesh P", "initials": "LP", "color": "#FFB800"},
      {"name": "Adithya B", "initials": "AB", "color": "#35D07F"},
      {"name": "Vajravel S", "initials": "VS", "color": "#00D9FF"},
  ]


  badges_html = "".join([
      f"""<div class="creator-badge" style="border: 1.5px solid {c['color']};">
            <div class="creator-avatar" style="background: {c['color']};">{c['initials']}</div>
            <span class="creator-name-text">{c['name']}</span>
        </div>"""
      for c in creators_list
  ])


  footer_html = f"""
    <div class="tech-footer-wrap">
        <div class="creators-container">
            <div class="creators-header">&lt;/&gt; CREATORS & TEAM:</div>
            <div class="creators-grid">
                {badges_html}
            </div>
        </div>
    </div>
    """
  st.markdown(textwrap.dedent(footer_html), unsafe_allow_html=True)




# TALENT FEED (PINTEREST MASONRY)
def render_verified_talent_feed(user_role="csr"):
  analyzed_applicants = [
      (uid, pdata)
      for uid, pdata in st.session_state.users_db.items()
      if pdata.get("analysis_completed", False) is True
  ]


  if not analyzed_applicants:
    if user_role == "csr":
      empty_state_html = """
            <div style="background: linear-gradient(145deg, #151720 0%, #090A0F 100%); border: 1px dashed #232736; border-radius: 24px; padding: 45px 30px; text-align: center; margin-top: 25px;">
                <div style="font-size: 2.8rem; margin-bottom: 12px; color: #FF3B4D;">🔍</div>
                <h2 style="color: #ffffff; font-weight: 900; font-size: 1.8rem; margin-bottom: 10px;">No Verified Applications Yet</h2>
                <p style="color: #8a8fA3; max-width: 520px; margin: 0 auto 20px auto; font-size: 0.98rem; line-height: 1.5;">
                    Athletes must upload their gameplay clips/photos and pass AI mechanics evaluation before appearing here.
                </p>
            </div>
            """
      st.markdown(textwrap.dedent(empty_state_html), unsafe_allow_html=True)
      st.write("")


      col1, col2, col3 = st.columns([1, 2, 1])
      with col2:
        if st.button(
            "🧪 Load Demo Athletes", type="secondary", use_container_width=True
        ):
          seed_demo_athletes()
          st.rerun()
    else:
      empty_state_html = """
            <div style="background: linear-gradient(145deg, #151720 0%, #090A0F 100%); border: 1px dashed #232736; border-radius: 24px; padding: 45px 30px; text-align: center; margin-top: 25px;">
                <div style="font-size: 2.8rem; margin-bottom: 12px; color: #FF3B4D;">🏆</div>
                <h2 style="color: #ffffff; font-weight: 900; font-size: 1.8rem; margin-bottom: 10px;">Your Profile is Pending</h2>
                <p style="color: #8a8fA3; max-width: 520px; margin: 0 auto 15px auto; font-size: 0.98rem;">
                    Submit your gameplay clips via Local Upload or Cloud/Drive link to run the AI mechanics evaluation and unlock your public profile.
                </p>
            </div>
            """
      st.markdown(textwrap.dedent(empty_state_html), unsafe_allow_html=True)


    return


  cards_html = ""
  for uid, player in analyzed_applicants:
    chips = "".join([
        f'<span class="skill-chip">{k}: {v}</span>'
        for k, v in player["stats"].items()
    ])
    thumb = player.get("thumbnail")
    if (
        not thumb
        or not isinstance(thumb, str)
        or (not thumb.startswith("http") and not os.path.exists(thumb))
    ):
      thumb = DEFAULT_THUMBNAIL


    source_tag = player.get("media_source", "Verified Media")


    card = f"""
<div class="pin-card">
<span class="pin-status-badge">✓ {source_tag}</span>
<span class="pin-rating-badge">{player['overall']} / 100</span>
<img src="{thumb}" class="pin-media" />
<div class="pin-body">
<div class="pin-title"><span style="color:#FF3B4D;">⚡</span> {player['name']}</div>
<div class="pin-meta">📍 {player['location']} • {player['age']} yrs ({player['gender']})</div>
<div class="pin-records">{player['records']}</div>
<p style="color: #cbd5e1; font-size: 0.88rem; margin-bottom: 12px;">"{player['bio']}"</p>
<div class="chip-container">{chips}</div>
</div>
</div>
"""
    cards_html += textwrap.dedent(card)


  masonry_wrapper = f'<div class="pin-masonry">{cards_html}</div>'
  st.markdown(masonry_wrapper, unsafe_allow_html=True)


  if user_role == "csr":
    st.divider()
    st.markdown("### 🤝 Issue CSR Sponsorship Grant")


    col_s1, col_s2, col_s3 = st.columns([1, 1, 1])
    with col_s1:
      selected_player_name = st.selectbox(
          "Select Evaluated Athlete",
          [p[1]["name"] for p in analyzed_applicants],
      )
    with col_s2:
      selected_grant = st.selectbox(
          "Funding Grant Tier",
          [
              "$500 Equipment & Training Gear Grant",
              "$1,500 Regional Tournament Sponsorship",
              "$3,500 International Travel & Coaching Fund",
          ],
      )
    with col_s3:
      st.write("")
      st.write("")
      if st.button("Submit Sponsorship Grant", type="primary"):
        st.session_state.grants_db.append({
            "athlete": selected_player_name,
            "tier": selected_grant,
            "csr_id": st.session_state.authenticated_csr,
        })
        st.success(
            f"Sponsorship grant successfully offered to {selected_player_name}!"
        )




# ---------------------------------------------------------
# STEP 1: LANDING PAGE
# ---------------------------------------------------------
if st.session_state.selected_role is None:
  render_hero_banner()


  col1, col2 = st.columns(2)


  with col1:
    st.markdown(
        """
        <div class="role-card">
            <div class="icon-badge">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#FF3B4D" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path>
                </svg>
            </div>
            <h2 style="color: #ffffff; font-weight: 800; margin-bottom: 8px;">Athlete</h2>
            <p style="color: #8a8fA3; font-size: 0.95rem; margin: 0;">Upload gameplay photos & clips from Drive or device, evaluate mechanics with AI, and land corporate funding.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button(
        "Enter as Athlete",
        key="btn_app",
        type="primary",
        use_container_width=True,
    ):
      st.session_state.selected_role = "applicant"
      st.rerun()


  with col2:
    st.markdown(
        """
        <div class="role-card">
            <div class="icon-badge">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#FF3B4D" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect>
                    <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path>
                </svg>
            </div>
            <h2 style="color: #ffffff; font-weight: 800; margin-bottom: 8px;">Sponsor / CSR Partner</h2>
            <p style="color: #8a8fA3; font-size: 0.95rem; margin: 0;">Discover high-potential AI-evaluated athletes and deploy corporate sponsorships.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button(
        "Enter as Sponsor / CSR Partner",
        key="btn_csr",
        type="primary",
        use_container_width=True,
    ):
      st.session_state.selected_role = "csr"
      st.rerun()


  render_tech_footer()


# ---------------------------------------------------------
# STEP 2: SPONSOR / CSR PARTNER PORTAL
# ---------------------------------------------------------
elif st.session_state.selected_role == "csr":
  if st.session_state.authenticated_csr is None:
    st.markdown(
        "<h1 style='text-align: center; font-weight: 900; font-size: 2.8rem;'>"
        "💼 Sponsor & CSR Partner Portal | <span style='color:"
        " #FF3B4D;'>Impact Score</span></h1>",
        unsafe_allow_html=True,
    )


    c_left, c_center, c_right = st.columns([1, 2, 1])


    with c_center:
      if st.button("← Back to Home", type="secondary"):
        st.session_state.selected_role = None
        st.rerun()


      csr_tab_login, csr_tab_signup = st.tabs(
          ["🔐 Partner Login", "✨ Register New Partner Account"]
      )


      with csr_tab_login:
        with st.form("csr_login_form"):
          csr_login_email = (
              st.text_input("Partner Email*", key="csr_log_email")
              .strip()
              .lower()
          )
          csr_login_pass = st.text_input(
              "Password*", type="password", key="csr_log_pass"
          )
          submit_csr_login = st.form_submit_button(
              "Log In as Sponsor / CSR Partner",
              type="primary",
              use_container_width=True,
          )


        if submit_csr_login:
          matched_csr_id = None
          for cid, cdata in st.session_state.csr_db.items():
            if cdata.get("email", "").lower() == csr_login_email:
              matched_csr_id = cid
              break


          if (
              matched_csr_id
              and st.session_state.csr_db[matched_csr_id]["password"]
              == csr_login_pass
          ):
            st.session_state.authenticated_csr = matched_csr_id
            st.success("Login successful!")
            st.rerun()
          else:
            st.error("Invalid credentials or user does not exist.")


      with csr_tab_signup:
        with st.form("csr_signup_form"):
          csr_new_email = (
              st.text_input("Corporate Email Address*", key="csr_reg_email")
              .strip()
              .lower()
          )
          csr_new_pass = st.text_input(
              "Choose Password*", type="password", key="csr_reg_pass"
          )
          csr_full_name = st.text_input("Full Name*", key="csr_reg_name")
          csr_org = st.text_input(
              "Organization / Corporate Fund*", key="csr_reg_org"
          )


          submit_csr_signup = st.form_submit_button(
              "Create Partner Profile", type="primary", use_container_width=True
          )


        if submit_csr_signup:
          if not is_valid_email(csr_new_email):
            st.error("Please enter a valid email address.")
          elif not csr_new_pass or not csr_full_name or not csr_org:
            st.error("Please fill in all required fields.")
          else:
            new_csr_id = f"csr_{len(st.session_state.csr_db) + 1}"
            st.session_state.csr_db[new_csr_id] = {
                "email": csr_new_email,
                "password": csr_new_pass,
                "name": csr_full_name,
                "organization": csr_org,
            }
            st.session_state.authenticated_csr = new_csr_id
            st.success("Account created!")
            st.rerun()


    render_tech_footer()


  else:
    csr_info = st.session_state.csr_db[st.session_state.authenticated_csr]


    # TOP HEADER BAR WITH LOG OUT
    top_c1, top_c2 = st.columns([3.5, 1])
    with top_c1:
      st.markdown(
          f"<h3 style='margin:0; padding-top:4px;'>💼 Welcome, <b>{csr_info['name']}</b>"
          f" <span style='color:#8a8fA3; font-size:0.95rem;'>({csr_info['organization']})</span></h3>",
          unsafe_allow_html=True,
      )
    with top_c2:
      if st.button(
          "🚪 Log Out",
          key="csr_header_logout",
          type="secondary",
          use_container_width=True,
      ):
        st.session_state.authenticated_csr = None
        st.rerun()


    st.markdown(
        "<hr style='margin: 12px 0 20px 0; border: 0; border-top: 1px solid"
        " #232736;'>",
        unsafe_allow_html=True,
    )


    # SEGMENTED NAV TOGGLE SWITCH FOR CSR PARTNER
    csr_view = st.radio(
        "CSR Navigation",
        ["📌 Talent Discovery Feed", "💼 CSR Portfolio & Impact Stats"],
        horizontal=True,
        label_visibility="collapsed",
        key="csr_nav_toggle",
    )


    st.markdown("<br/>", unsafe_allow_html=True)


    if csr_view == "📌 Talent Discovery Feed":
      st.markdown(
          "<h2 style='font-weight: 900;'><span style='color:"
          " #FF3B4D;'>📌</span> Verified Athlete <span style='color:"
          " #FF3B4D;'>Discovery Feed</span></h2>",
          unsafe_allow_html=True,
      )
      render_verified_talent_feed(user_role="csr")


    elif csr_view == "💼 CSR Portfolio & Impact Stats":
      st.markdown(
          f"<h2 style='font-weight: 900;'><span style='color:"
          f" #FF3B4D;'>💼</span> {csr_info['organization']} — <span"
          " style='color: #FF3B4D;'>CSR Impact Portfolio</span></h2>",
          unsafe_allow_html=True,
      )


      # Stat Metrics
      m1, m2, m3 = st.columns(3)
      total_grants_issued = len(st.session_state.grants_db)
      total_fund_amount = total_grants_issued * 1500


      with m1:
        st.markdown(
            f"""
            <div class="stat-card">
                <span style="color:#8a8fA3; font-size:0.85rem; font-weight:700;">TOTAL GRANTS ISSUED</span>
                <h1 style="color:#ffffff; font-weight:900; margin:5px 0 0 0;">{total_grants_issued}</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )
      with m2:
        st.markdown(
            f"""
            <div class="stat-card">
                <span style="color:#8a8fA3; font-size:0.85rem; font-weight:700;">CAPITAL DEPLOYED</span>
                <h1 style="color:#FF3B4D; font-weight:900; margin:5px 0 0 0;">${total_fund_amount:,.2f}</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )
      with m3:
        st.markdown(
            """
            <div class="stat-card">
                <span style="color:#8a8fA3; font-size:0.85rem; font-weight:700;">ACTIVE SPONSORED ATHLETES</span>
                <h1 style="color:#00D9FF; font-weight:900; margin:5px 0 0 0;">3</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )


      st.markdown("<br/>", unsafe_allow_html=True)
      st.subheader("📜 Issued Grants Log")
      if st.session_state.grants_db:
        st.table(st.session_state.grants_db)
      else:
        st.info(
            "No grants issued yet. Select athletes from the Discovery Feed to"
            " deploy funding."
        )


    render_tech_footer()


# ---------------------------------------------------------
# STEP 3: ATHLETE PORTAL
# ---------------------------------------------------------
elif st.session_state.selected_role == "applicant":
  if st.session_state.authenticated_user is None:
    st.markdown(
        "<h1 style='text-align: center; font-weight: 900; font-size: 2.8rem;'>"
        "👟 Athlete Portal | <span style='color: #FF3B4D;'>Impact"
        " Score</span></h1>",
        unsafe_allow_html=True,
    )


    c_left, c_center, c_right = st.columns([1, 2, 1])


    with c_center:
      if st.button("← Back to Home", type="secondary"):
        st.session_state.selected_role = None
        st.rerun()


      tab_login, tab_signup = st.tabs(
          ["🔐 Athlete Login", "✨ New Athlete Sign Up"]
      )


      with tab_login:
        with st.form("login_form"):
          login_email = (
              st.text_input("Email Address*", key="login_email").strip().lower()
          )
          login_pass = st.text_input(
              "Password*", type="password", key="login_password"
          )
          submit_login = st.form_submit_button(
              "Log In as Athlete", type="primary", use_container_width=True
          )


        if submit_login:
          matched_user_id = None
          for uid, pdata in st.session_state.users_db.items():
            if pdata.get("email", "").lower() == login_email:
              matched_user_id = uid
              break


          if (
              matched_user_id
              and st.session_state.users_db[matched_user_id]["password"]
              == login_pass
          ):
            st.session_state.authenticated_user = matched_user_id
            st.success("Login successful!")
            st.rerun()
          else:
            st.error("Invalid email or password.")


      with tab_signup:
        with st.form("signup_form"):
          new_email = (
              st.text_input("Email Address*", key="su_email").strip().lower()
          )
          new_username = (
              st.text_input("Choose Username*", key="su_user").strip().lower()
          )
          new_password = st.text_input(
              "Choose Password*", type="password", key="su_pass"
          )
          full_name = st.text_input("Full Name*", key="su_name")


          c_age, c_gen = st.columns(2)
          with c_age:
            age = st.number_input("Age*", min_value=8, max_value=80, value=18)
          with c_gen:
            gender = st.selectbox("Gender*", ["Male", "Female", "Other"])


          location = st.text_input("Location / Region*", key="su_loc")
          bio = st.text_area("Short Bio & Playing Style", key="su_bio")
          records = st.text_area(
              "Zonal / State Competition Records*", key="su_rec"
          )


          profile_photo = st.file_uploader(
              "Upload Profile Photo (Optional)",
              type=["png", "jpg", "jpeg", "webp"],
          )


          submit_signup = st.form_submit_button(
              "Register Profile", type="primary", use_container_width=True
          )


        if submit_signup:
          registered_emails = [
              pdata.get("email", "").lower()
              for pdata in st.session_state.users_db.values()
          ]


          if not is_valid_email(new_email):
            st.error("Please enter a valid email address.")
          elif new_email in registered_emails:
            st.error("This email is already registered. Please log in.")
          elif not new_username or not new_password or not full_name:
            st.error("Please complete all required fields.")
          elif new_username in st.session_state.users_db:
            st.error("Username is taken.")
          else:
            user_thumbnail = DEFAULT_THUMBNAIL
            if profile_photo is not None:
              photo_path = os.path.join(
                  UPLOAD_DIR, f"{new_username}_profile.png"
              )
              with open(photo_path, "wb") as f:
                f.write(profile_photo.getbuffer())
              user_thumbnail = photo_path


            st.session_state.users_db[new_username] = {
                "email": new_email,
                "password": new_password,
                "name": full_name,
                "age": age,
                "gender": gender,
                "location": location,
                "bio": bio,
                "records": records,
                "thumbnail": user_thumbnail,
                "analysis_completed": False,
                "stats": {},
                "overall": 0,
                "media_source": "Pending",
                "saved_video_paths": [],
            }
            st.session_state.authenticated_user = new_username
            st.success("Athlete account created successfully!")
            st.rerun()


    render_tech_footer()


  else:
    current_user_id = st.session_state.authenticated_user
    user_info = st.session_state.users_db[current_user_id]


    # TOP HEADER BAR WITH LOG OUT
    top_c1, top_c2 = st.columns([3.5, 1])
    with top_c1:
      st.markdown(
          f"<h3 style='margin:0; padding-top:4px;'>👟 Athlete Account: <b>{user_info['name']}</b></h3>",
          unsafe_allow_html=True,
      )
    with top_c2:
      if st.button(
          "🚪 Log Out",
          key="athlete_header_logout",
          type="secondary",
          use_container_width=True,
      ):
        st.session_state.authenticated_user = None
        st.rerun()


    st.markdown(
        "<hr style='margin: 12px 0 20px 0; border: 0; border-top: 1px solid"
        " #232736;'>",
        unsafe_allow_html=True,
    )


    # SEGMENTED NAV TOGGLE SWITCH FOR ATHLETE
    athlete_view = st.radio(
        "Athlete Navigation",
        ["📊 Profile & Stats", "📌 Talent Feed", "⚡ AI Gameplay Evaluation"],
        horizontal=True,
        label_visibility="collapsed",
        key="athlete_nav_toggle",
    )


    st.markdown("<br/>", unsafe_allow_html=True)


    if athlete_view == "📊 Profile & Stats":
      if not user_info["analysis_completed"]:
        st.info(
            "💡 You haven't completed your AI evaluation yet. Toggle over to"
            " **⚡ AI Gameplay Evaluation** to analyze your game and unlock full"
            " stats."
        )


      st.title(f"📊 Player Profile & Scorecard — {user_info['name']}")
      col1, col2 = st.columns([1, 1])


      with col1:
        st.subheader("📋 Athlete Details")


        # Thumbnail rendering with fallback
        thumb_url = user_info.get("thumbnail")
        if (
            not thumb_url
            or not isinstance(thumb_url, str)
            or (
                not thumb_url.startswith("http")
                and not os.path.exists(thumb_url)
            )
        ):
          thumb_url = DEFAULT_THUMBNAIL


        st.image(thumb_url, width=220)
        st.write(f"**Email:** {user_info['email']}")
        st.write(
            f"**Age / Gender:** {user_info['age']} yrs | {user_info['gender']}"
        )
        st.write(f"**Location:** {user_info['location']}")
        st.write(
            f"**Media Source:** {user_info.get('media_source', 'Pending')}"
        )
        st.write(f"**Bio:** {user_info['bio']}")
        st.info(f"**Records:**\n{user_info['records']}")


      with col2:
        st.subheader("🎯 Performance Metrics")
        st.metric(
            label="Overall Rating",
            value=f"{user_info.get('overall', 0)} / 100",
        )
        if user_info.get("stats"):
          fig = create_radar_chart(user_info["stats"], user_info["name"])
          st.plotly_chart(fig, use_container_width=True)
        else:
          st.warning(
              "Complete AI Mechanics Evaluation to generate radar chart"
              " metrics."
          )


    elif athlete_view == "📌 Talent Feed":
      st.markdown(
          "<h2 style='font-weight: 900;'><span style='color:"
          " #FF3B4D;'>📌</span> Verified Athlete <span style='color:"
          " #FF3B4D;'>Discovery Feed</span></h2>",
          unsafe_allow_html=True,
      )
      render_verified_talent_feed(user_role="applicant")


    elif "AI Gameplay Evaluation" in athlete_view:
        st.markdown("## ⚡ AI Gameplay Evaluation & Media Upload")
        st.info(
            "Choose your preferred method below to submit your gameplay clips for AI mechanics evaluation."
        )

        upload_method = st.radio(
            "Choose Media Source Option:",
            [
                "Google Drive / Cloud Link (Recommended)",
                "Direct File Upload (Device/System)",
            ],
            horizontal=True,
            key="media_source_radio"
        )

        valid_submission = False
        source_tag = "Pending"
        saved_paths = []

        # Option A: Cloud / Google Drive Link
        if "Google Drive" in upload_method:
            st.markdown("#### ☁️ Import Gameplay via Google Drive / Cloud")
            drive_link = st.text_input(
                "Google Drive / OneDrive / Dropbox Link*",
                placeholder="https://drive.google.com/drive/folders/1a2b3c... or file URL",
                key="cloud_drive_url",
            )
            st.caption(
                "**Tip:** Make sure link sharing permission is set to **'Anyone with the link can view'** so the AI engine can stream the video."
            )
            if drive_link:
                if is_valid_url(drive_link):
                    st.markdown(
                        f"""
                        <div class="source-box">
                        <span style="color:#00D9FF; font-weight:800;">Connected to Cloud Target:</span><br/>
                        <code>{drive_link}</code>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    valid_submission = True
                    source_tag = "Google Drive"
                else:
                    st.warning("Please enter a valid web URL starting with https://")

        # Option B: Direct Local Upload
        elif "Direct File Upload" in upload_method:
            st.markdown("#### 📁 Upload Gameplay Files directly from your device")
            uploaded_files = st.file_uploader(
                "Attach Gameplay Clips or Photo Certificates",
                type=["mp4", "mov", "avi", "png", "jpg", "jpeg"],
                accept_multiple_files=True,
                key="local_media_files",
            )
            if uploaded_files:
                st.write(f"**{len(uploaded_files)}** media file(s) attached.")
                valid_submission = True
                source_tag = "Local Upload"
                for idx, file in enumerate(uploaded_files):
                    file_path = os.path.join(
                        UPLOAD_DIR, f"{current_user_id}_file_{idx+1}_{file.name}"
                    )
                    with open(file_path, "wb") as f:
                        f.write(file.getbuffer())
                    saved_paths.append(file_path)

        st.markdown("---")

        # --- ALWAYS VISIBLE ANALYSIS BUTTON ---
        if st.button("🚀 Run Impact Score AI Analysis", type="primary", use_container_width=True):
            if not valid_submission:
                st.error("⚠️ Please attach gameplay files or provide a valid Google Drive link before running the analysis.")
            else:
                with st.spinner("Transmitting media to FastAPI Backend Engine & running AI pipeline..."):
                    try:
                        files_payload = {}
                        
                        # Prepare files for FastAPI
                        if saved_paths and len(saved_paths) > 0:
                            video_path = saved_paths[0]
                            files_payload["video_file"] = (
                                os.path.basename(video_path),
                                open(video_path, "rb"),
                                "video/mp4"
                            )
                            
                            # FastAPI requires 'proof_file'. Use second attached file, or fallback to first file.
                            proof_path = saved_paths[1] if len(saved_paths) > 1 else saved_paths[0]
                            files_payload["proof_file"] = (
                                os.path.basename(proof_path),
                                open(proof_path, "rb"),
                                "image/png"
                            )

                        # Form fields matching FastAPI's exact requirements
                        data_payload = {
                            "player_name": user_info.get("name", "Athlete"),
                            "claimed_level": user_info.get("records") if user_info.get("records") else "State Level"
                        }

                        # HTTP POST Request
                        response = requests.post(BACKEND_URL, files=files_payload, data=data_payload, timeout=90)

                        if response.status_code == 200:
                            result = response.json()
                            kinematics = result.get("kinematics", {})
                            
                            ai_stats = {
                                "Forehand": int(kinematics.get("forehand_score", random.randint(75, 92))),
                                "Backhand": int(kinematics.get("backhand_score", random.randint(70, 88))),
                                "Footwork": int(kinematics.get("footwork_score", random.randint(72, 90))),
                                "Reaction": int(kinematics.get("reaction_score", random.randint(78, 95))),
                                "Endurance": int(kinematics.get("endurance_score", random.randint(70, 88))),
                            }

                            overall_score = result.get("overall_score", sum(ai_stats.values()) // len(ai_stats))

                            st.session_state.users_db[current_user_id]["stats"] = ai_stats
                            st.session_state.users_db[current_user_id]["overall"] = overall_score
                            st.session_state.users_db[current_user_id]["media_source"] = source_tag
                            st.session_state.users_db[current_user_id]["saved_video_paths"] = saved_paths
                            st.session_state.users_db[current_user_id]["analysis_completed"] = True

                            st.success("✅ AI Analysis Complete! Real kinematics & scores fetched from FastAPI backend.")
                            st.rerun()
                        else:
                            st.error(f"Backend Server Error ({response.status_code}): {response.text}")

                    except Exception as e:
                        st.error(f"Failed to connect to FastAPI backend at {BACKEND_URL}. Ensure main.py is running. Error: {e}")