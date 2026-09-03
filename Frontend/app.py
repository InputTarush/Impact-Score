import base64
import os
import random
import re
import time
import requests
import plotly.graph_objects as go
import streamlit as st

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
SAMPLE_VIDEO_1 = "https://vjs.zencdn.net/v/oceans.mp4"
SAMPLE_VIDEO_2 = "https://www.w3schools.com/html/mov_bbb.mp4"

COMPETITION_LEVEL_OPTIONS = [
    "National Level",
    "State Level",
    "District Level",
    "Zonal Level",
    "None",
]


# Convert Local File Paths or Remote URLs to Browser-Ready Image Sources
def get_image_data_uri(file_path_or_url):
    if not file_path_or_url:
        return DEFAULT_THUMBNAIL
    if isinstance(file_path_or_url, str) and (
        file_path_or_url.startswith("http://")
        or file_path_or_url.startswith("https://")
        or file_path_or_url.startswith("data:image")
    ):
        return file_path_or_url

    if isinstance(file_path_or_url, str) and os.path.exists(file_path_or_url):
        try:
            ext = file_path_or_url.split(".")[-1].lower()
            mime_type = "image/jpeg" if ext in ["jpg", "jpeg"] else f"image/{ext}"
            with open(file_path_or_url, "rb") as img_file:
                encoded = base64.b64encode(img_file.read()).decode("utf-8")
            return f"data:{mime_type};base64,{encoded}"
        except Exception:
            return DEFAULT_THUMBNAIL

    return DEFAULT_THUMBNAIL


# HTML Sanitizer Helper
def clean_html(html_str):
    return "\n".join([line.strip() for line in html_str.splitlines() if line.strip()])


def render_html(html_str):
    st.markdown(clean_html(html_str), unsafe_allow_html=True)


# Validation Helpers
def is_valid_email(email):
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None


def is_valid_url(url):
    pattern = r"^https?://[^\s/$.?#].[^\s]*$"
    return re.match(pattern, url) is not None


# Radar Chart Builder
def create_styled_radar_chart(stats_dict, player_name="Player Stats"):
    categories = list(stats_dict.keys())
    values = list(stats_dict.values())

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill="toself",
            name=player_name,
            line=dict(color="#FF3B4D", width=3),
            fillcolor="rgba(255, 59, 77, 0.25)",
            marker=dict(size=6, color="#FF3B4D"),
        )
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                color="#8a8fA3",
                gridcolor="rgba(30, 41, 59, 0.8)",
                tickfont=dict(size=10, color="#8a8fA3"),
            ),
            angularaxis=dict(
                color="#ffffff",
                gridcolor="rgba(30, 41, 59, 0.8)",
                tickfont=dict(size=12, color="#ffffff", family="Arial"),
            ),
            bgcolor="rgba(0,0,0,0)",
        ),
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=30, r=30, t=30, b=30),
    )
    return fig


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

if "just_passed_video_eval" not in st.session_state:
    st.session_state.just_passed_video_eval = False

if "csr_selected_athlete_id" not in st.session_state:
    st.session_state.csr_selected_athlete_id = None


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
        "records": "State Level (🥇 State Junior Champion 2024)",
        "record_proof_path": None,
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
        "saved_video_paths": [
            {"title": "Forehand Loop Drive Analysis", "url": SAMPLE_VIDEO_1, "date": "2026-01-15"}
        ],
    }
    st.session_state.users_db["maya_patel"] = {
        "email": "maya.patel@sports.org",
        "password": "demo",
        "name": "Maya Patel",
        "age": 19,
        "gender": "Female",
        "location": "London, UK",
        "bio": "Tactical defensive chopper with rapid counter-attacks.",
        "records": "National Level (🥈 Runner Up - National Youth Games)",
        "record_proof_path": None,
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
        "saved_video_paths": [
            {"title": "Backhand Chop & Defense Rally", "url": SAMPLE_VIDEO_2, "date": "2026-02-18"}
        ],
    }


# HERO BANNER COMPONENT
def render_hero_banner():
    hero_html = """
    <div style="
        background: linear-gradient(90deg, #080d1a 38%, rgba(8,13,26,0.4) 75%, transparent 100%), 
                    url('https://images.unsplash.com/photo-1534158914592-062992fbe900?q=80&w=1600&auto=format&fit=crop');
        background-size: cover;
        background-position: center right;
        border-radius: 24px;
        padding: 55px 40px;
        min-height: 380px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        border: 1px solid #1e293b;
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
    render_html(hero_html)


# FOOTER COMPONENT
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
    render_html(footer_html)


# VIDEO LIBRARY DISPLAY HELPER (Supports Local Files & Web Links)
def render_video_library_player(videos_list):
    if not videos_list:
        render_html("""
        <div style="background: #0a0f1d; border: 1px dashed #1e293b; border-radius: 16px; padding: 30px; text-align: center;">
            <div style="font-size: 2rem; color: #8a8fA3; margin-bottom: 8px;">📹</div>
            <p style="color: #8a8fA3; margin: 0; font-size: 0.9rem;">No video clips available in this library yet.</p>
        </div>
        """)
        return

    for idx, vid in enumerate(videos_list):
        vid_title = vid.get("title", f"Gameplay Clip #{idx+1}") if isinstance(vid, dict) else f"Gameplay Clip #{idx+1}"
        vid_src = vid.get("url") if isinstance(vid, dict) else vid
        vid_date = vid.get("date", "Recorded Clip") if isinstance(vid, dict) else "Recorded Clip"

        render_html(f"""
        <div style="background: #0a0f1d; border: 1px solid #1e293b; border-radius: 14px; padding: 12px 16px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <b style="color: #ffffff; font-size: 0.92rem;">🎬 {vid_title}</b>
                <span style="color: #8a8fA3; font-size: 0.78rem;">📅 {vid_date}</span>
            </div>
        </div>
        """)
        try:
            if isinstance(vid_src, str) and os.path.exists(vid_src):
                st.video(vid_src)
            elif isinstance(vid_src, str) and (vid_src.startswith("http://") or vid_src.startswith("https://")):
                st.video(vid_src)
            else:
                st.info(f"📹 Video Link/Path: {vid_src}")
        except Exception as e:
            st.error(f"Unable to play media stream: {e}")


# TALENT FEED & CLICKABLE ATHLETE INSPECTOR WITH DRAGGABLE FILTERS
def render_verified_talent_feed(user_role="csr"):
    raw_applicants = [
        (uid, pdata)
        for uid, pdata in st.session_state.users_db.items()
        if pdata.get("analysis_completed", False) is True
    ]

    if not raw_applicants:
        if user_role == "csr":
            empty_state_html = """
            <div style="background: linear-gradient(145deg, #101728 0%, #0a0f1d 100%); border: 1px dashed #1e293b; border-radius: 24px; padding: 45px 30px; text-align: center; margin-top: 25px;">
                <div style="font-size: 2.8rem; margin-bottom: 12px; color: #FF3B4D;">🔍</div>
                <h2 style="color: #ffffff; font-weight: 900; font-size: 1.8rem; margin-bottom: 10px;">No Verified Applications Yet</h2>
                <p style="color: #8a8fA3; max-width: 520px; margin: 0 auto 20px auto; font-size: 0.98rem; line-height: 1.5;">
                    Athletes must upload their gameplay clip and pass AI mechanics evaluation before appearing here.
                </p>
            </div>
            """
            render_html(empty_state_html)
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
            <div style="background: linear-gradient(145deg, #101728 0%, #0a0f1d 100%); border: 1px dashed #1e293b; border-radius: 24px; padding: 45px 30px; text-align: center; margin-top: 25px;">
                <div style="font-size: 2.8rem; margin-bottom: 12px; color: #FF3B4D;">🏆</div>
                <h2 style="color: #ffffff; font-weight: 900; font-size: 1.8rem; margin-bottom: 10px;">Your Profile is Pending</h2>
                <p style="color: #8a8fA3; max-width: 520px; margin: 0 auto 15px auto; font-size: 0.98rem;">
                    Submit your gameplay clip via Local Upload or Cloud/Drive link to run the AI mechanics evaluation and unlock your public profile.
                </p>
            </div>
            """
            render_html(empty_state_html)

        return

    # CSR DETAILED ATHLETE PROFILE OVERLAY / MODAL
    if user_role == "csr" and st.session_state.csr_selected_athlete_id:
        selected_uid = st.session_state.csr_selected_athlete_id
        player = st.session_state.users_db.get(selected_uid)

        if player:
            if st.button("← Back to Discovery Feed", type="secondary"):
                st.session_state.csr_selected_athlete_id = None
                st.rerun()

            st.markdown("<br/>", unsafe_allow_html=True)
            thumb_src = get_image_data_uri(player.get("thumbnail"))
            vids = player.get("saved_video_paths", [])

            render_html(f"""
            <div style="background: linear-gradient(135deg, #101728 0%, #0a0f1d 100%); border: 1px solid #FF3B4D; border-radius: 24px; padding: 30px; margin-bottom: 30px; box-shadow: 0 15px 40px rgba(255, 59, 77, 0.25);">
                <div style="display: flex; gap: 24px; align-items: center; flex-wrap: wrap;">
                    <img src="{thumb_src}" style="width: 130px; height: 130px; object-fit: cover; border-radius: 20px; border: 2px solid #FF3B4D;" />
                    <div style="flex: 1;">
                        <span style="background: rgba(53, 208, 127, 0.15); color: #35D07F; padding: 4px 12px; border-radius: 20px; font-weight: 800; font-size: 0.78rem; border: 1px solid rgba(53, 208, 127, 0.4);">✓ VERIFIED ATHLETE (PASSED AI EVALUATION)</span>
                        <h1 style="color: #ffffff; font-weight: 900; margin: 8px 0 4px 0;">{player['name']}</h1>
                        <div style="color: #8a8fA3; font-size: 0.95rem; margin-bottom: 8px;">
                            📍 {player['location']} • {player['age']} Yrs ({player['gender']}) • Overall Impact Rating: <b style="color:#FF3B4D;">{player['overall']} / 100</b>
                        </div>
                        <p style="color: #cbd5e1; font-size: 0.95rem; margin: 0;">"{player['bio']}"</p>
                    </div>
                </div>
            </div>
            """)

            col_det1, col_det2 = st.columns([1.1, 1.3], gap="large")

            with col_det1:
                st.subheader("📊 AI Skill Breakdown & Radar")
                if player.get("stats"):
                    fig = create_styled_radar_chart(player["stats"], player["name"])
                    st.plotly_chart(fig, use_container_width=True)

                st.markdown("---")
                st.subheader("🤝 Grant Funding Allocation")
                selected_grant = st.selectbox(
                    "Funding Tier",
                    [
                        "₹50,000 Equipment & Training Gear Grant",
                        "₹1,50,000 Regional Tournament Sponsorship",
                        "₹3,50,000 International Travel & Coaching Fund",
                    ],
                    key="modal_grant_select",
                )
                if st.button("🚀 Issue Grant to Athlete", type="primary", use_container_width=True):
                    st.session_state.grants_db.append({
                        "athlete": player["name"],
                        "tier": selected_grant,
                        "csr_id": st.session_state.authenticated_csr,
                    })
                    st.success(f"Grant successfully offered to {player['name']}!")

            with col_det2:
                st.subheader(f"📹 {player['name']}'s Video Library ({len(vids)} Clips)")
                render_video_library_player(vids)

            return

    # DRAGGABLE FILTER SYSTEM FOR CSR PARTNERS
    analyzed_applicants = raw_applicants
    if user_role == "csr":
        with st.expander("🎛️ Filter Athletes by Rating, Age, Gender & Stroke Skills", expanded=True):
            f_col1, f_col2, f_col3 = st.columns(3)

            with f_col1:
                st.markdown("<b style='color:#FF3B4D;'>🎯 Core Demographics & Impact</b>", unsafe_allow_html=True)
                impact_range = st.slider("⚡ Impact Rating (Dragger)", 0, 100, (0, 100), key="filter_impact")
                age_range = st.slider("🎂 Age System (Dragger)", 8, 80, (8, 80), key="filter_age")
                selected_genders = st.multiselect(
                    "👤 Gender System",
                    ["Male", "Female", "Other"],
                    default=["Male", "Female", "Other"],
                    key="filter_gender",
                )

            with f_col2:
                st.markdown("<b style='color:#FF3B4D;'>🏓 Stroke Category Draggers</b>", unsafe_allow_html=True)
                min_forehand = st.slider("Min Forehand Rating", 0, 100, 0, key="filter_forehand")
                min_backhand = st.slider("Min Backhand Rating", 0, 100, 0, key="filter_backhand")

            with f_col3:
                st.markdown("<b style='color:#FF3B4D;'>🏃 Athletic & Physical Draggers</b>", unsafe_allow_html=True)
                min_footwork = st.slider("Min Footwork Rating", 0, 100, 0, key="filter_footwork")
                min_reaction = st.slider("Min Reaction Rating", 0, 100, 0, key="filter_reaction")
                min_endurance = st.slider("Min Endurance Rating", 0, 100, 0, key="filter_endurance")

        # Apply Filtering Logic
        filtered_applicants = []
        for uid, pdata in raw_applicants:
            overall = pdata.get("overall", 0)
            age = pdata.get("age", 0)
            gender = pdata.get("gender", "Other")
            stats = pdata.get("stats", {})

            forehand = stats.get("Forehand", 0)
            backhand = stats.get("Backhand", 0)
            footwork = stats.get("Footwork", 0)
            reaction = stats.get("Reaction", 0)
            endurance = stats.get("Endurance", 0)

            if (
                impact_range[0] <= overall <= impact_range[1]
                and age_range[0] <= age <= age_range[1]
                and gender in selected_genders
                and forehand >= min_forehand
                and backhand >= min_backhand
                and footwork >= min_footwork
                and reaction >= min_reaction
                and endurance >= min_endurance
            ):
                filtered_applicants.append((uid, pdata))

        analyzed_applicants = filtered_applicants

        if not analyzed_applicants:
            st.warning("⚠️ No athletes match your specified filter criteria. Please adjust the dragger range sliders or gender options.")
            return

    # CLICKABLE ATHLETE GRID (DISCOVERY FEED)
    col_grid = st.columns(3)

    for idx, (uid, player) in enumerate(analyzed_applicants):
        target_col = col_grid[idx % 3]
        with target_col:
            thumb_src = get_image_data_uri(player.get("thumbnail"))
            vids_count = len(player.get("saved_video_paths", []))
            record_badge = f"🥇 {player.get('records', 'Verified Record')}" if player.get('records') else "🥇 Record Verified"

            chips = "".join([
                f'<span class="skill-chip">{k}: {v}</span>'
                for k, v in list(player["stats"].items())[:3]
            ])

            card_html = f"""
            <div class="pin-card">
                <span class="pin-status-badge">✓ {vids_count} Video Verified</span>
                <span class="pin-rating-badge">{player['overall']} / 100</span>
                <img src="{thumb_src}" class="pin-media" />
                <div class="pin-body">
                    <div class="pin-title"><span style="color:#FF3B4D;">⚡</span> {player['name']}</div>
                    <div class="pin-meta">📍 {player['location']} • {player['age']} yrs ({player['gender']})</div>
                    <div class="pin-records">{record_badge}</div>
                    <p style="color: #cbd5e1; font-size: 0.85rem; margin-bottom: 10px; line-height: 1.4;">"{player['bio']}"</p>
                    <div class="chip-container">{chips}</div>
                </div>
            </div>
            """
            render_html(card_html)

            if user_role == "csr":
                if st.button(
                    f"📹 View Profile & Videos ({player['name']})",
                    key=f"btn_inspect_{uid}",
                    type="primary",
                    use_container_width=True,
                ):
                    st.session_state.csr_selected_athlete_id = uid
                    st.rerun()


# STYLES: DARK SLATE BLUE DESIGN SYSTEM WITH ATHLETE ENHANCEMENTS
st.markdown(
    """
<style>
    /* Dark Mode Canvas */
    .stApp {
        background-color: #080d1a !important;
        color: #f0f2f8 !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    }
    
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 1.5rem !important; padding-bottom: 0rem !important; max-width: 1300px; }

    /* SEGMENTED TOGGLE SWITCH (Navigation Control Bar) */
    div[data-testid="stRadio"] > div {
        background-color: #101728 !important;
        border: 1px solid #1e293b !important;
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
        background: #101728;
        border-radius: 24px;
        padding: 30px 24px;
        border: 1px solid #1e293b;
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
        background: #101728;
        border: 1px solid #1e293b;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.4);
    }

    /* Form Inputs & Select Boxes */
    div[data-baseweb="input"] > div, 
    div[data-baseweb="textarea"] > div,
    div[data-baseweb="select"] > div {
        background-color: #0a0f1d !important;
        border-radius: 16px !important;
        border: 1px solid #1e293b !important;
        color: #ffffff !important;
    }
    div[data-baseweb="input"] > div:focus-within, 
    div[data-baseweb="textarea"] > div:focus-within,
    div[data-baseweb="select"] > div:focus-within {
        border-color: #FF3B4D !important;
    }

    /* ATHLETE CARD GRID */
    .pin-card {
        background: #101728;
        border-radius: 20px;
        overflow: hidden;
        border: 1px solid #1e293b;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
        transition: transform 0.3s ease, box-shadow 0.3s ease, border-color 0.3s ease;
        position: relative;
        margin-bottom: 16px;
    }
    .pin-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 20px 40px rgba(255, 59, 77, 0.25);
        border-color: #FF3B4D;
    }

    .pin-media {
        width: 100%;
        height: 200px;
        object-fit: cover;
        display: block;
        border-bottom: 1px solid #1e293b;
    }

    .pin-rating-badge {
        position: absolute;
        top: 12px;
        right: 12px;
        background: #FF3B4D;
        color: #ffffff;
        font-weight: 900;
        font-size: 0.8rem;
        padding: 4px 10px;
        border-radius: 20px;
        box-shadow: 0 4px 12px rgba(255, 59, 77, 0.4);
    }
    .pin-status-badge {
        position: absolute;
        top: 12px;
        left: 12px;
        background: rgba(10, 15, 29, 0.88);
        backdrop-filter: blur(8px);
        color: #35D07F;
        font-weight: 700;
        font-size: 0.72rem;
        padding: 4px 10px;
        border-radius: 12px;
        border: 1px solid rgba(53, 208, 127, 0.4);
    }

    .pin-body { padding: 16px; }
    .pin-title { font-size: 1.15rem; font-weight: 800; color: #ffffff; margin-bottom: 2px; }
    .pin-meta { font-size: 0.82rem; color: #8a8fA3; margin-bottom: 10px; }
    .pin-records {
        font-size: 0.8rem;
        color: #FF3B4D;
        font-weight: 600;
        margin-bottom: 10px;
        background: rgba(255, 59, 77, 0.1);
        padding: 6px 10px;
        border-radius: 8px;
        border-left: 3px solid #FF3B4D;
    }

    .chip-container { display: flex; flex-wrap: wrap; gap: 6px; }
    .skill-chip {
        background: #0a0f1d;
        color: #cbd5e1;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 6px;
        border: 1px solid #1e293b;
    }

    /* ATHLETE PORTAL SPECIFIC UI ENHANCEMENTS */
    .athlete-hero-card {
        background: linear-gradient(135deg, #101728 0%, #0a0f1d 100%);
        border: 1px solid #1e293b;
        border-radius: 20px;
        padding: 24px;
        box-shadow: 0 10px 30px rgba(0,0,0,0.4);
        margin-bottom: 16px;
    }

    .overall-score-box {
        background: linear-gradient(135deg, #FF3B4D 0%, #D61B30 100%);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 8px 25px rgba(255, 59, 77, 0.4);
    }
    .overall-score-number {
        font-size: 3.2rem;
        font-weight: 900;
        color: #ffffff;
        line-height: 1;
    }

    .upload-card-option {
        background: #0a0f1d;
        border: 1.5px solid #1e293b;
        border-radius: 16px;
        padding: 18px;
        transition: all 0.25s ease;
    }
    .upload-card-option:hover {
        border-color: #FF3B4D;
    }

    .stat-metric-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: #0a0f1d;
        border: 1px solid #1e293b;
        border-radius: 12px;
        padding: 10px 16px;
        margin-bottom: 8px;
    }

    /* FOOTER STYLING FOR CREATORS ONLY */
    .tech-footer-wrap {
        background-color: #050811;
        border-top: 1px solid #1e293b;
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
        background: #0a0f1d;
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

# ---------------------------------------------------------
# STEP 1: LANDING PAGE
# ---------------------------------------------------------
if st.session_state.selected_role is None:
    render_hero_banner()

    col1, col2 = st.columns(2)

    with col1:
        render_html("""
        <div class="role-card">
            <div class="icon-badge">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#FF3B4D" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"></path>
                </svg>
            </div>
            <h2 style="color: #ffffff; font-weight: 800; margin-bottom: 8px;">Athlete</h2>
            <p style="color: #8a8fA3; font-size: 0.95rem; margin: 0;">Upload competition records & a gameplay clip, evaluate mechanics with AI, and land corporate funding.</p>
        </div>
        """)
        if st.button(
            "Enter as Athlete",
            key="btn_app",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.selected_role = "applicant"
            st.rerun()

    with col2:
        render_html("""
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
        """)
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
        render_html(
            "<h1 style='text-align: center; font-weight: 900; font-size: 2.8rem;'>"
            "💼 Sponsor & CSR Partner Portal | <span style='color:"
            " #FF3B4D;'>Impact Score</span></h1>"
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

        top_c1, top_c2 = st.columns([3.5, 1])
        with top_c1:
            render_html(
                f"<h3 style='margin:0; padding-top:4px;'>💼 Welcome, <b>{csr_info['name']}</b>"
                f" <span style='color:#8a8fA3; font-size:0.95rem;'>({csr_info['organization']})</span></h3>"
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

        render_html(
            "<hr style='margin: 12px 0 20px 0; border: 0; border-top: 1px solid"
            " #1e293b;'>"
        )

        csr_view = st.radio(
            "CSR Navigation",
            ["📌 Talent Discovery Feed", "💼 CSR Portfolio & Impact Stats"],
            horizontal=True,
            label_visibility="collapsed",
            key="csr_nav_toggle",
        )

        st.markdown("<br/>", unsafe_allow_html=True)

        if csr_view == "📌 Talent Discovery Feed":
            if not st.session_state.csr_selected_athlete_id:
                render_html(
                    "<h2 style='font-weight: 900;'><span style='color:"
                    " #FF3B4D;'>📌</span> Verified Athlete <span style='color:"
                    " #FF3B4D;'>Discovery Feed</span></h2>"
                )
            render_verified_talent_feed(user_role="csr")

        elif csr_view == "💼 CSR Portfolio & Impact Stats":
            render_html(
                f"<h2 style='font-weight: 900;'><span style='color:"
                f" #FF3B4D;'>💼</span> {csr_info['organization']} — <span"
                " style='color: #FF3B4D;'>CSR Impact Portfolio</span></h2>"
            )

            m1, m2, m3 = st.columns(3)
            total_grants_issued = len(st.session_state.grants_db)
            total_fund_amount = total_grants_issued * 150000

            with m1:
                render_html(f"""
                <div class="stat-card">
                    <span style="color:#8a8fA3; font-size:0.85rem; font-weight:700;">TOTAL GRANTS ISSUED</span>
                    <h1 style="color:#ffffff; font-weight:900; margin:5px 0 0 0;">{total_grants_issued}</h1>
                </div>
                """)
            with m2:
                render_html(f"""
                <div class="stat-card">
                    <span style="color:#8a8fA3; font-size:0.85rem; font-weight:700;">CAPITAL DEPLOYED</span>
                    <h1 style="color:#FF3B4D; font-weight:900; margin:5px 0 0 0;">₹{total_fund_amount:,.2f}</h1>
                </div>
                """)
            with m3:
                render_html("""
                <div class="stat-card">
                    <span style="color:#8a8fA3; font-size:0.85rem; font-weight:700;">ACTIVE SPONSORED ATHLETES</span>
                    <h1 style="color:#00D9FF; font-weight:900; margin:5px 0 0 0;">2</h1>
                </div>
                """)

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
        render_html(
            "<h1 style='text-align: center; font-weight: 900; font-size: 2.8rem;'>"
            "👟 Athlete Portal | <span style='color: #FF3B4D;'>Impact"
            " Score</span></h1>"
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

                    # --- COMPETITION RECORDS LEVEL SELECT BOX ---
                    competition_level = st.selectbox(
                        "Competition Records Level*",
                        COMPETITION_LEVEL_OPTIONS,
                        index=4,
                        key="su_rec_level",
                    )

                    record_details = st.text_input(
                        "Specific Honors / Achievements (Optional)",
                        key="su_rec_detail",
                        placeholder="e.g. 🥇 State Champion 2024, Semi-finalist",
                    )

                    record_proof_file = st.file_uploader(
                        "Competition Record / Certificate Proof",
                        type=["pdf", "png", "jpg", "jpeg", "webp"],
                        key="su_record_file",
                        help="Upload certificate, award photo, or tournament standing proof (Optional).",
                    )

                    profile_photo = st.file_uploader(
                        "Upload Profile Photo (Optional)",
                        type=["png", "jpg", "jpeg", "webp"],
                        key="su_photo_file",
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
                            ext = profile_photo.name.split(".")[-1].lower()
                            photo_path = os.path.join(
                                UPLOAD_DIR, f"{new_username}_profile.{ext}"
                            )
                            with open(photo_path, "wb") as f:
                                f.write(profile_photo.getbuffer())
                            user_thumbnail = photo_path

                        record_file_path = None
                        if record_proof_file is not None:
                            ext = record_proof_file.name.split(".")[-1].lower()
                            record_file_path = os.path.join(
                                UPLOAD_DIR, f"{new_username}_record_proof.{ext}"
                            )
                            with open(record_file_path, "wb") as f:
                                f.write(record_proof_file.getbuffer())

                        # Combine Selected Level and Optional Text
                        if competition_level != "None":
                            formatted_record = (
                                f"{competition_level} ({record_details})"
                                if record_details
                                else competition_level
                            )
                        else:
                            formatted_record = record_details if record_details else "None"

                        st.session_state.users_db[new_username] = {
                            "email": new_email,
                            "password": new_password,
                            "name": full_name,
                            "age": age,
                            "gender": gender,
                            "location": location,
                            "bio": bio,
                            "records": formatted_record,
                            "record_proof_path": record_file_path,
                            "thumbnail": user_thumbnail,
                            "analysis_completed": False,
                            "stats": {},
                            "overall": 0,
                            "media_source": "Pending",
                            "saved_video_paths": [],
                        }
                        st.session_state.authenticated_user = new_username
                        st.success("Athlete account registered successfully!")
                        st.rerun()

        render_tech_footer()

    else:
        current_user_id = st.session_state.authenticated_user
        user_info = st.session_state.users_db[current_user_id]

        if st.session_state.just_passed_video_eval:
            st.toast("🎉 Gameplay video uploaded and verified successfully!", icon="✅")
            st.session_state.just_passed_video_eval = False

        top_c1, top_c2 = st.columns([3.5, 1])
        with top_c1:
            render_html(f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                <span style="font-size: 1.8rem;">👟</span>
                <div>
                    <h2 style="margin: 0; font-weight: 900; color: #ffffff;">{user_info['name']}</h2>
                    <span style="color: #8a8fA3; font-size: 0.88rem;">Athlete Control Center & Performance Hub</span>
                </div>
            </div>
            """)
        with top_c2:
            if st.button(
                "🚪 Log Out",
                key="athlete_header_logout",
                type="secondary",
                use_container_width=True,
            ):
                st.session_state.authenticated_user = None
                st.rerun()

        render_html(
            "<hr style='margin: 8px 0 20px 0; border: 0; border-top: 1px solid"
            " #1e293b;'>"
        )

        athlete_view = st.radio(
            "Athlete Navigation",
            [
                "📊 Profile & Analytics",
                "✏️ Edit Profile",
                "⚡ AI Gameplay Evaluation",
                "📹 Video Library",
                "📌 Discovery Feed",
            ],
            horizontal=True,
            label_visibility="collapsed",
            key="athlete_nav_toggle",
        )

        st.markdown("<br/>", unsafe_allow_html=True)

        # TAB 1: PROFILE & ANALYTICS
        if athlete_view == "📊 Profile & Analytics":
            if user_info.get("analysis_completed"):
                render_html(f"""
                <div style="background: rgba(53, 208, 127, 0.12); border: 1px solid rgba(53, 208, 127, 0.4); border-radius: 16px; padding: 16px; margin-bottom: 20px; display: flex; align-items: center; gap: 14px;">
                    <span style="font-size: 1.6rem;">🎉</span>
                    <div>
                        <b style="color: #35D07F; font-size: 0.98rem;">Video Evaluation Passed!</b>
                        <p style="color: #cbd5e1; font-size: 0.88rem; margin: 2px 0 0 0;">
                            Your gameplay video has been verified and analyzed. Your profile is now live for CSR sponsors in the Discovery Feed via <b>{user_info.get('media_source', 'Verified Upload')}</b>.
                        </p>
                    </div>
                </div>
                """)
            else:
                render_html("""
                <div style="background: rgba(0, 217, 255, 0.08); border: 1px solid rgba(0, 217, 255, 0.3); border-radius: 16px; padding: 16px; margin-bottom: 20px; display: flex; align-items: center; gap: 12px;">
                    <span style="font-size: 1.5rem;">💡</span>
                    <span style="color: #cbd5e1; font-size: 0.92rem;">
                        <b>Evaluation Pending:</b> Head over to <b>⚡ AI Gameplay Evaluation</b> to submit a gameplay clip and activate full skill analytics.
                    </span>
                </div>
                """)

            col_profile, col_radar, col_scores = st.columns([1.1, 1.3, 1.1], gap="medium")

            with col_profile:
                thumb_src = get_image_data_uri(user_info.get("thumbnail"))
                has_proof = "✓ Verified Certificate Uploaded" if user_info.get("record_proof_path") else "No Certificate Attached"

                render_html(f"""
                <div class="athlete-hero-card">
                    <div style="position: relative; text-align: center; margin-bottom: 18px;">
                        <img src="{thumb_src}" style="width: 100%; max-height: 220px; object-fit: cover; border-radius: 16px; border: 1px solid #1e293b;" />
                    </div>
                    <h3 style="color: #ffffff; font-weight: 800; margin: 0 0 6px 0;">{user_info['name']}</h3>
                    <div style="color: #8a8fA3; font-size: 0.88rem; margin-bottom: 16px;">
                        📍 {user_info.get('location', 'Global')} • {user_info.get('age', 'N/A')} Yrs ({user_info.get('gender', 'N/A')})
                    </div>
                    
                    <div style="background: #0a0f1d; border-radius: 12px; padding: 14px; border: 1px solid #1e293b; margin-bottom: 16px;">
                        <span style="color: #FF3B4D; font-weight: 800; font-size: 0.78rem; letter-spacing: 0.5px;">BIOGRAPHY & STYLE</span>
                        <p style="color: #cbd5e1; font-size: 0.88rem; margin: 6px 0 0 0; line-height: 1.4;">
                            "{user_info.get('bio', 'No bio provided.')}"
                        </p>
                    </div>

                    <div style="background: rgba(255, 59, 77, 0.08); border-left: 3px solid #FF3B4D; border-radius: 8px; padding: 12px;">
                        <span style="color: #ffffff; font-weight: 700; font-size: 0.82rem;">🥇 TRACK RECORD & HONORS</span>
                        <p style="color: #a0a6b8; font-size: 0.85rem; margin: 4px 0 4px 0;">
                            {user_info.get('records') if user_info.get('records') else 'No competition records logged.'}
                        </p>
                        <span style="color: #00D9FF; font-size: 0.75rem; font-weight: 700;">{has_proof}</span>
                    </div>
                </div>
                """)

            with col_radar:
                if user_info.get("stats"):
                    render_html("""
                    <div style="background: #101728; border: 1px solid #1e293b; border-radius: 20px; padding: 20px; height: 100%;">
                        <h4 style="color: #ffffff; font-weight: 800; margin: 0 0 10px 0; text-align: center;">📊 Mechanics Distribution</h4>
                    """)
                    fig = create_styled_radar_chart(
                        user_info["stats"], user_info["name"]
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    render_html("</div>")
                else:
                    render_html("""
                    <div style="background: #101728; border: 1px solid #1e293b; border-radius: 20px; padding: 30px 20px; text-align: center; height: 100%;">
                        <h4 style="color: #ffffff; font-weight: 800; margin: 0 0 10px 0;">📊 Mechanics Distribution</h4>
                        <p style="color: #8a8fA3; font-size: 0.9rem; margin-top: 20px;">
                            Complete your video evaluation to generate your mechanics radar chart.
                        </p>
                    </div>
                    """)

            with col_scores:
                render_html("""
                <div style="background: #101728; border: 1px solid #1e293b; border-radius: 20px; padding: 22px; height: 100%;">
                    <h4 style="color: #ffffff; font-weight: 800; margin: 0 0 16px 0;">🎯 Performance Overview</h4>
                """)

                overall_score = user_info.get("overall", 0)
                render_html(f"""
                <div class="overall-score-box" style="margin-bottom: 20px;">
                    <span style="color: rgba(255,255,255,0.8); font-size: 0.75rem; font-weight: 800; letter-spacing: 1px;">IMPACT SCORE</span>
                    <div class="overall-score-number">{overall_score}</div>
                    <span style="color: rgba(255,255,255,0.9); font-size: 0.82rem; font-weight: 700;">OUT OF 100</span>
                </div>
                """)

                if user_info.get("stats"):
                    for key, val in user_info["stats"].items():
                        render_html(f"""
                        <div class="stat-metric-row">
                            <span style="color: #cbd5e1; font-weight: 700; font-size: 0.85rem;">{key}</span>
                            <span style="color: #FF3B4D; font-weight: 900; font-size: 0.95rem;">{val} / 100</span>
                        </div>
                        """)
                else:
                    st.caption("No stroke breakdown stats generated yet.")

                render_html("</div>")

        # TAB 2: EDIT PROFILE
        elif athlete_view == "✏️ Edit Profile":
            render_html("""
            <div style="background: linear-gradient(135deg, #101728 0%, #0a0f1d 100%); border: 1px solid #1e293b; border-radius: 20px; padding: 24px; margin-bottom: 24px;">
                <h2 style="color: #ffffff; font-weight: 900; margin: 0 0 8px 0;">✏️ Edit Athlete Profile</h2>
                <p style="color: #8a8fA3; margin: 0; font-size: 0.95rem;">
                    Update your personal details, bio, achievements, competition level, and profile media.
                </p>
            </div>
            """)

            existing_record = user_info.get("records", "")
            default_level_idx = 4
            for idx, lvl in enumerate(COMPETITION_LEVEL_OPTIONS):
                if lvl != "None" and lvl in existing_record:
                    default_level_idx = idx
                    break

            with st.form("edit_profile_form"):
                col_e1, col_e2 = st.columns(2)

                with col_e1:
                    edit_name = st.text_input("Full Name*", value=user_info.get("name", ""), key="ep_name")
                    edit_email = st.text_input("Email Address*", value=user_info.get("email", ""), key="ep_email")
                    edit_age = st.number_input("Age*", min_value=8, max_value=80, value=int(user_info.get("age", 18)), key="ep_age")
                    gender_options = ["Male", "Female", "Other"]
                    curr_gender = user_info.get("gender", "Male")
                    edit_gender = st.selectbox(
                        "Gender*",
                        gender_options,
                        index=gender_options.index(curr_gender) if curr_gender in gender_options else 0,
                        key="ep_gender",
                    )

                with col_e2:
                    edit_location = st.text_input("Location / Region*", value=user_info.get("location", ""), key="ep_loc")
                    edit_comp_level = st.selectbox(
                        "Competition Records Level*",
                        COMPETITION_LEVEL_OPTIONS,
                        index=default_level_idx,
                        key="ep_rec_level",
                    )
                    edit_rec_details = st.text_input(
                        "Specific Honors / Achievements",
                        value=existing_record,
                        key="ep_rec_detail",
                        placeholder="e.g. 🥇 State Champion 2024",
                    )

                edit_bio = st.text_area("Short Bio & Playing Style", value=user_info.get("bio", ""), key="ep_bio")

                st.markdown("---")
                col_f1, col_f2 = st.columns(2)

                with col_f1:
                    st.write("📷 **Profile Photo**")
                    curr_photo_path = user_info.get("thumbnail")
                    if curr_photo_path:
                        st.image(get_image_data_uri(curr_photo_path), width=100)
                    edit_photo = st.file_uploader("Replace Profile Photo", type=["png", "jpg", "jpeg", "webp"], key="ep_photo_file")

                with col_f2:
                    st.write("📄 **Certificate / Proof Document**")
                    if user_info.get("record_proof_path"):
                        st.caption("✓ File currently attached")
                    else:
                        st.caption("No proof attached")
                    edit_proof = st.file_uploader("Upload New Record Proof", type=["pdf", "png", "jpg", "jpeg", "webp"], key="ep_proof_file")

                save_profile = st.form_submit_button("💾 Save Changes", type="primary", use_container_width=True)

            if save_profile:
                if not is_valid_email(edit_email):
                    st.error("Please enter a valid email address.")
                elif not edit_name:
                    st.error("Full name cannot be empty.")
                else:
                    user_info["name"] = edit_name
                    user_info["email"] = edit_email
                    user_info["age"] = edit_age
                    user_info["gender"] = edit_gender
                    user_info["location"] = edit_location
                    user_info["bio"] = edit_bio

                    if edit_comp_level != "None":
                        if edit_rec_details and edit_comp_level not in edit_rec_details:
                            user_info["records"] = f"{edit_comp_level} ({edit_rec_details})"
                        else:
                            user_info["records"] = edit_rec_details if edit_rec_details else edit_comp_level
                    else:
                        user_info["records"] = edit_rec_details if edit_rec_details else "None"

                    if edit_photo is not None:
                        ext = edit_photo.name.split(".")[-1].lower()
                        photo_path = os.path.join(UPLOAD_DIR, f"{current_user_id}_profile.{ext}")
                        with open(photo_path, "wb") as f:
                            f.write(edit_photo.getbuffer())
                        user_info["thumbnail"] = photo_path

                    if edit_proof is not None:
                        ext = edit_proof.name.split(".")[-1].lower()
                        proof_path = os.path.join(UPLOAD_DIR, f"{current_user_id}_record_proof.{ext}")
                        with open(proof_path, "wb") as f:
                            f.write(edit_proof.getbuffer())
                        user_info["record_proof_path"] = proof_path

                    st.session_state.users_db[current_user_id] = user_info
                    st.success("✅ Profile updated successfully!")
                    st.rerun()

        # TAB 3: AI GAMEPLAY EVALUATION
        elif athlete_view == "⚡ AI Gameplay Evaluation":
            if user_info.get("analysis_completed"):
                st.success(
                    "✅ **Video Evaluation Passed!** You have uploaded your"
                    " gameplay video and completed the AI evaluation. Submitting a new"
                    " video below will update your profile."
                )

            render_html("""
            <div style="background: linear-gradient(135deg, #101728 0%, #0a0f1d 100%); border: 1px solid #1e293b; border-radius: 20px; padding: 24px; margin-bottom: 24px;">
                <h2 style="color: #ffffff; font-weight: 900; margin: 0 0 8px 0;">⚡ AI Mechanics Analysis Engine</h2>
                <p style="color: #8a8fA3; margin: 0; font-size: 0.95rem;">
                    Submit a gameplay clip (rallies, serves, footwork). Our CV evaluation engine measures stroke velocity, form, recovery time, and consistency.
                </p>
            </div>
            """)

            upload_method = st.radio(
                "Select Submission Mode:",
                [
                    "☁️ Google Drive / Cloud Directory (Recommended)",
                    "💻 Upload Video File From Device",
                ],
                horizontal=True,
            )

            valid_submission = False
            source_tag = ""
            existing_vids = user_info.get("saved_video_paths", [])
            saved_paths = existing_vids.copy()

            st.markdown("<br/>", unsafe_allow_html=True)

            if "☁️ Google Drive" in upload_method:
                render_html("""
                <div class="upload-card-option">
                    <h4 style="color: #ffffff; font-weight: 800; margin: 0 0 6px 0;">☁️ Cloud Folder / Drive Link</h4>
                    <p style="color: #8a8fA3; font-size: 0.85rem; margin-bottom: 14px;">Paste a public link containing match footage or stroke practice video.</p>
                </div>
                """)

                drive_link = st.text_input(
                    "Cloud Directory Link*",
                    placeholder="https://drive.google.com/drive/folders/...",
                    key="athlete_drive_url",
                )

                if drive_link:
                    if is_valid_url(drive_link):
                        render_html(f"""
                        <div style="background: rgba(0, 217, 255, 0.1); border: 1px solid rgba(0, 217, 255, 0.3); border-radius: 12px; padding: 12px; margin-top: 10px;">
                            <span style="color: #00D9FF; font-size: 0.85rem; font-weight: 700;">✓ Connected Target:</span> 
                            <code style="color: #ffffff;">{drive_link}</code>
                        </div>
                        """)
                        valid_submission = True
                        source_tag = "Google Drive"
                        today = time.strftime("%Y-%m-%d")
                        saved_paths = [
                            {"title": "Drive Submission Clip", "url": drive_link, "date": today}
                        ]
                    else:
                        st.warning("Please enter a valid HTTP/HTTPS web URL.")

            else:
                render_html("""
                <div class="upload-card-option">
                    <h4 style="color: #ffffff; font-weight: 800; margin: 0 0 6px 0;">💻 Direct Video File Upload</h4>
                    <p style="color: #8a8fA3; font-size: 0.85rem; margin-bottom: 14px;">Upload a video clip showcasing your strokes or gameplay.</p>
                </div>
                """)

                uploaded_files = st.file_uploader(
                    "Attach Gameplay Clip (MP4, MOV, AVI)",
                    type=["mp4", "mov", "avi", "webm"],
                    accept_multiple_files=True,
                    key="athlete_local_files",
                )

                if uploaded_files:
                    st.write(
                        f"📁 **{len(uploaded_files)} / 1** minimum file attached."
                    )
                    if len(uploaded_files) >= 1:
                        valid_submission = True
                        source_tag = "Local Upload"
                        saved_paths = []
                        today = time.strftime("%Y-%m-%d")

                        for idx, file in enumerate(uploaded_files):
                            ext = file.name.split(".")[-1].lower() if "." in file.name else "mp4"
                            file_path = os.path.join(
                                UPLOAD_DIR, f"{current_user_id}_eval_{idx+1}_{int(time.time())}.{ext}"
                            )
                            with open(file_path, "wb") as f:
                                f.write(file.getbuffer())

                            saved_paths.append({
                                "title": f"Gameplay Clip ({file.name})",
                                "url": file_path,
                                "date": today,
                            })
                    else:
                        st.warning(
                            "Please attach at least 1 video clip to complete qualification."
                        )

            st.markdown("<br/>", unsafe_allow_html=True)
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])

            with col_btn2:
                if st.button(
                    "🚀 Launch AI Mechanics Evaluation",
                    type="primary",
                    use_container_width=True,
                ):
                    if not valid_submission:
                        st.error(
                            "Please attach at least 1 gameplay clip or a valid Drive URL."
                        )
                    else:
                        progress_text = "Connecting to AI Vision & Ollama Backend Engine..."
                        my_bar = st.progress(10, text=progress_text)

                        BACKEND_URL = "http://127.0.0.1:8001/analyze_applicant"
                        
                        try:
                            # Prepare Form Data for FastAPI
                            form_data = {
                                "player_name": user_info.get("name", current_user_id),
                                "claimed_level": user_info.get("records", "State Level"),
                            }

                            files_payload = None

                            # If a local video was uploaded, attach it to the HTTP request
                            if source_tag == "Local Upload" and saved_paths:
                                local_video_file_path = saved_paths[0]["url"]
                                if os.path.exists(local_video_file_path):
                                    files_payload = {
                                        "video_file": (
                                            os.path.basename(local_video_file_path),
                                            open(local_video_file_path, "rb"),
                                            "video/mp4",
                                        )
                                    }

                            my_bar.progress(30, text="Running OpenCV motion tracking & frame analysis...")

                            # POST request to FastAPI backend (main.py)
                            response = requests.post(
                                BACKEND_URL,
                                data=form_data,
                                files=files_payload,
                                timeout=120.0
                            )

                            # Close open file handle if used
                            if files_payload and "video_file" in files_payload:
                                files_payload["video_file"][1].close()

                            if response.status_code == 200:
                                api_result = response.json()
                                my_bar.progress(90, text="Generating Qwen LLM coaching commentary...")

                                kinematics = api_result.get("kinematics", {})
                                llm_eval = api_result.get("llm_evaluation", {})

                                # Extract real metrics calculated by OpenCV
                                ai_stats = {
                                    "Forehand": kinematics.get("forehand_score", 80),
                                    "Backhand": kinematics.get("backhand_score", 78),
                                    "Footwork": kinematics.get("footwork_score", 80),
                                    "Reaction": kinematics.get("reaction_score", 82),
                                    "Endurance": kinematics.get("endurance_score", 80),
                                }
                                overall_score = api_result.get("overall_score", 80)
                                llm_commentary = llm_eval.get("summary", "Analysis completed.")

                                # Update session state with genuine backend data
                                st.session_state.users_db[current_user_id]["stats"] = ai_stats
                                st.session_state.users_db[current_user_id]["overall"] = overall_score
                                st.session_state.users_db[current_user_id]["media_source"] = source_tag
                                st.session_state.users_db[current_user_id]["saved_video_paths"] = saved_paths
                                st.session_state.users_db[current_user_id]["analysis_completed"] = True
                                st.session_state.users_db[current_user_id]["ai_commentary"] = llm_commentary

                                my_bar.progress(100, text="Analysis Complete!")
                                st.session_state.just_passed_video_eval = True

                                st.balloons()
                                st.rerun()
                            else:
                                st.error(f"Backend API Error ({response.status_code}): {response.text}")

                        except requests.exceptions.ConnectionError:
                            st.error(
                                "❌ Could not connect to backend server at http://127.0.0.1:8001. "
                                "Ensure `python main.py` or `uvicorn main:app --port 8001` is running in VS Code!"
                            )
                        except Exception as e:
                            st.error(f"An unexpected error occurred during evaluation: {e}")

        # TAB 4: VIDEO LIBRARY
        elif athlete_view == "📹 Video Library":
            render_html("""
            <div style="background: linear-gradient(135deg, #101728 0%, #0a0f1d 100%); border: 1px solid #1e293b; border-radius: 20px; padding: 24px; margin-bottom: 24px;">
                <h2 style="color: #ffffff; font-weight: 900; margin: 0 0 8px 0;">📹 My Gameplay Video Library</h2>
                <p style="color: #8a8fA3; margin: 0; font-size: 0.95rem;">
                    Store, stream, and manage your match recordings and training footage. CSR sponsors can view these videos directly on your scout profile.
                </p>
            </div>
            """)

            vids = user_info.get("saved_video_paths", [])

            c_lib1, c_lib2 = st.columns([2, 1], gap="large")

            with c_lib1:
                st.subheader(f"📺 Saved & Playable Gameplay Clips ({len(vids)})")
                render_video_library_player(vids)

            with c_lib2:
                st.subheader("➕ Upload New Gameplay Video")
                with st.form("add_video_form"):
                    new_vid_title = st.text_input("Video Title*", placeholder="e.g. Forehand Smash Practice")
                    new_vid_url = st.text_input("Video URL / Stream Link", placeholder="https://...")
                    uploaded_vid_file = st.file_uploader("Or Upload Video File (MP4, MOV, WEBM)", type=["mp4", "mov", "avi", "webm"])

                    add_vid_submit = st.form_submit_button("Save To Video Library", type="primary", use_container_width=True)

                if add_vid_submit:
                    if not new_vid_title:
                        st.error("Please enter a title for your video.")
                    else:
                        vid_source = None
                        if uploaded_vid_file is not None:
                            ext = uploaded_vid_file.name.split(".")[-1].lower() if "." in uploaded_vid_file.name else "mp4"
                            file_path = os.path.join(
                                UPLOAD_DIR, f"{current_user_id}_lib_{len(vids)+1}_{int(time.time())}.{ext}"
                            )
                            with open(file_path, "wb") as f:
                                f.write(uploaded_vid_file.getbuffer())
                            vid_source = file_path
                        elif new_vid_url and is_valid_url(new_vid_url):
                            vid_source = new_vid_url

                        if vid_source:
                            new_clip = {
                                "title": new_vid_title,
                                "url": vid_source,
                                "date": time.strftime("%Y-%m-%d"),
                            }
                            if "saved_video_paths" not in st.session_state.users_db[current_user_id]:
                                st.session_state.users_db[current_user_id]["saved_video_paths"] = []

                            st.session_state.users_db[current_user_id]["saved_video_paths"].append(new_clip)
                            st.success("Video clip added to your library!")
                            st.rerun()
                        else:
                            st.error("Please provide a video file or a valid URL.")

        # TAB 5: DISCOVERY FEED
        elif athlete_view == "📌 Discovery Feed":
            render_html(
                "<h2 style='font-weight: 900;'><span style='color:"
                " #FF3B4D;'>📌</span> Verified Athlete <span style='color:"
                " #FF3B4D;'>Community Feed</span></h2>"
            )
            render_verified_talent_feed(user_role="applicant")

        render_tech_footer()