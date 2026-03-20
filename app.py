import streamlit as st
import requests
import time as time_module
import random
from datetime import date

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# ─── PAGE CONFIG ──────────────────────────────────────────
st.set_page_config(
    page_title="Cura – Cognitive-Adaptive Medical Partner",
    page_icon="🩺",
    layout="wide",
)

# ─── CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: linear-gradient(135deg, #0f0c29, #302b63, #24243e); min-height: 100vh; }
    .block-container { padding-top: 2rem; padding-bottom: 2rem; }
    .cura-card {
        background: rgba(255,255,255,0.05);
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 16px; padding: 1.5rem;
        backdrop-filter: blur(12px); margin-bottom: 1rem;
    }
    .stButton > button {
        background: linear-gradient(90deg, #667eea, #764ba2) !important;
        color: white !important; border: none !important;
        border-radius: 10px !important; padding: 0.5rem 1.5rem !important;
        font-weight: 600 !important; transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102,126,234,0.4) !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(102,126,234,0.6) !important;
    }
    .stTextInput > div > input, .stTextArea > div > textarea {
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 10px !important; color: #e0e0e0 !important;
    }
    [data-testid="stSidebar"] {
        background: rgba(15,12,41,0.85) !important;
        border-right: 1px solid rgba(255,255,255,0.1) !important;
    }
    h1, h2, h3 { color: #e0e0e0 !important; }
    .stAlert { border-radius: 12px !important; }
    hr { border-color: rgba(255,255,255,0.15) !important; }
    .badge {
        display: inline-block;
        background: linear-gradient(90deg, #667eea, #764ba2);
        color: white; padding: 3px 12px; border-radius: 50px;
        font-size: 0.75rem; font-weight: 600; margin-left: 8px; vertical-align: middle;
    }
    .gap-item {
        display: flex; align-items: center; gap: 8px;
        background: rgba(255,82,82,0.10); border: 1px solid rgba(255,82,82,0.3);
        border-radius: 10px; padding: 0.5rem 1rem; margin-bottom: 0.4rem;
        color: #ff8a80; font-weight: 500;
    }
    .step-label {
        font-size: 0.75rem; text-transform: uppercase;
        letter-spacing: 1.5px; color: #9e9e9e; margin-bottom: 0.25rem;
    }
    .streak-badge {
        background: linear-gradient(90deg, #f7971e, #ffd200);
        color: #1a1a1a; padding: 4px 14px; border-radius: 50px;
        font-weight: 700; font-size: 0.85rem; display: inline-block; margin-top: 4px;
    }
    .leaderboard-row {
        display: flex; justify-content: space-between; align-items: center;
        background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08);
        border-radius: 10px; padding: 0.5rem 1rem; margin-bottom: 0.4rem; color: #e0e0e0;
    }
    .rank-1 { border-left: 3px solid #ffd700; }
    .rank-2 { border-left: 3px solid #c0c0c0; }
    .rank-3 { border-left: 3px solid #cd7f32; }
    .user-row { background: rgba(102,126,234,0.15) !important; border-color: rgba(102,126,234,0.5) !important; }
    .pomodoro-display {
        font-size: 2.2rem; font-weight: 700; color: #90caf9; text-align: center; margin: 0.5rem 0;
    }
    .vignette-card {
        background: rgba(102,126,234,0.08); border: 1px solid rgba(102,126,234,0.3);
        border-radius: 14px; padding: 1.2rem 1.5rem; margin-bottom: 1rem;
    }
    .stat-card {
        text-align: center; padding: 1.2rem; background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# ─── STATIC DATA ──────────────────────────────────────────
MOCK_LEADERBOARD = [
    {"name": "Ahmed K.",   "flag": "🇸🇦", "pts": 3240, "streak": 45},
    {"name": "Fatima A.",  "flag": "🇦🇪", "pts": 2980, "streak": 38},
    {"name": "Omar H.",    "flag": "🇪🇬", "pts": 2760, "streak": 32},
    {"name": "Chen W.",    "flag": "🇨🇳", "pts": 2540, "streak": 28},
    {"name": "Priya M.",   "flag": "🇮🇳", "pts": 2310, "streak": 22},
    {"name": "Lena K.",    "flag": "🇩🇪", "pts": 2100, "streak": 19},
    {"name": "Carlos R.",  "flag": "🇧🇷", "pts": 1870, "streak": 15},
    {"name": "Aisha T.",   "flag": "🇲🇦", "pts": 1650, "streak": 12},
]

VIGNETTES = [
    {
        "case": "A 55-year-old male presents with crushing chest pain radiating to the left arm, diaphoresis, and nausea for 2 hours. ECG shows ST elevation in leads II, III, and aVF.",
        "question": "What is the most likely diagnosis?",
        "options": ["Pericarditis", "Inferior STEMI", "Aortic Dissection", "GERD"],
        "answer": 1,
        "explanation": "ST elevation in inferior leads (II, III, aVF) = Inferior STEMI → RCA occlusion. High-yield! ⭐"
    },
    {
        "case": "A 28-year-old female presents with a butterfly rash, joint pain, fatigue, ANA+, anti-dsDNA+, low complement, and proteinuria.",
        "question": "Which organ system is most at risk for serious injury?",
        "options": ["Liver", "Kidney (Lupus Nephritis)", "Lung (Pleuritis)", "Heart (Endocarditis)"],
        "answer": 1,
        "explanation": "Proteinuria + active SLE = Lupus Nephritis. Most dangerous SLE complication. Anti-dsDNA correlates with disease activity. ⭐"
    },
    {
        "case": "A 45-year-old malnourished alcoholic presents with confusion, ophthalmoplegia, and ataxia.",
        "question": "What is the FIRST treatment to give?",
        "options": ["IV Glucose", "IV Thiamine (B1)", "IV Folate", "Naloxone"],
        "answer": 1,
        "explanation": "Wernicke's encephalopathy: ALWAYS give thiamine BEFORE glucose. Glucose without thiamine can precipitate/worsen Wernicke's! ⭐⭐"
    },
    {
        "case": "A 67-year-old female: sudden 'worst headache of my life'. CT head negative. LP: xanthochromia.",
        "question": "What is the diagnosis?",
        "options": ["Migraine", "Subarachnoid Hemorrhage", "Meningitis", "Tension Headache"],
        "answer": 1,
        "explanation": "Thunderclap headache + negative CT + xanthochromia on LP = Subarachnoid Hemorrhage (SAH). CT is 98% sensitive within 6h but LP confirms. ⭐⭐"
    },
    {
        "case": "A 3-year-old boy: painless abdominal mass, does NOT cross the midline. Imaging: large intrarenal mass with rim of normal renal tissue.",
        "question": "Most likely diagnosis?",
        "options": ["Neuroblastoma", "Wilms Tumor (Nephroblastoma)", "Renal Cell Carcinoma", "Hepatoblastoma"],
        "answer": 1,
        "explanation": "Wilms Tumor: most common renal malignancy in children. Does NOT cross midline (Neuroblastoma does + arises from adrenal). ⭐"
    },
]

HOBBY_CONTENT = {
    "Art": {
        "emoji": "🎨",
        "title": "Art Break",
        "content": "**Did you know?** Botticelli's *Birth of Venus* (1484) was one of the first large-scale non-religious nudes since antiquity. Vasari described it as 'surpassing all praise.'",
        "image": "https://images.unsplash.com/photo-1579783902614-a3fb3927b6a5?q=80&w=600",
    },
    "Photography": {
        "emoji": "📷",
        "title": "Photography Tip",
        "content": "**Rule of Thirds:** Divide your frame into 9 segments. Place your subject at intersections of the lines — not dead center — for a more dynamic, professional composition.",
        "image": "https://images.unsplash.com/photo-1452587925148-ce544e77e70d?q=80&w=600",
    },
    "History": {
        "emoji": "📜",
        "title": "History Snapshot",
        "content": "**Black Death (1347–51)** killed 30–60% of Europeans. The plague paradoxically accelerated the end of feudalism — surviving peasants suddenly had unprecedented labor bargaining power.",
        "image": "https://images.unsplash.com/photo-1599940824399-b87987ceb72a?q=80&w=600",
    },
    "Music": {
        "emoji": "🎵",
        "title": "Music Moment",
        "content": "Music activates the same **dopamine reward pathways** as food and exercise. Minor keys don't always mean sadness — Flamenco uses minor scales to express passionate joy.",
        "image": "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?q=80&w=600",
    },
    "Cinema": {
        "emoji": "🎬",
        "title": "Film Break",
        "content": "For *Barry Lyndon* (1975), Kubrick used **NASA-modified lenses** to shoot scenes lit only by candlelight. The resulting look remains cinematographically unmatched.",
        "image": "https://images.unsplash.com/photo-1536440136628-849c177e76a1?q=80&w=600",
    },
    "Nature": {
        "emoji": "🌿",
        "title": "Nature Moment",
        "content": "Trees communicate via the **'Wood Wide Web'** — an underground fungal network. Older 'mother trees' actively send nutrients to their seedlings through these fungal channels.",
        "image": "https://images.unsplash.com/photo-1448375240586-882707db888b?q=80&w=600",
    },
}

LECTURE_RESOURCES = [
    {"title": "Lecture Material 1", "url": "https://share.google/jYmQZh8L9493SusA1"},
    {"title": "Lecture Material 2", "url": "https://share.google/yf2U4fjq6vzzQE7cW"},
]

PATHOLOGY_POINTS = {
    "ATP depletion": "ATP depletion → Na⁺/K⁺ pump failure → cell swelling → necrosis.",
    "Mitochondrial damage": "Mitochondrial damage releases cytochrome c → apoptosis cascade.",
    "Membrane permeability": "Increased membrane permeability is key in necrosis — enzymes leak causing inflammation.",
    "Inflammation": "Necrosis triggers inflammation; apoptosis does NOT (immunologically silent).",
}

# ─── SESSION STATE ─────────────────────────────────────────
defaults = {
    "immunology_passed": False,
    "pathology_passed": False,
    "chat_history": [],
    "points": 0,
    "streak": 1,
    "pomodoro_start": None,
    "pomodoro_work_mins": 25,
    "pomodoro_break_mins": 5,
    "pomodoro_mode": "idle",
    "hobby_interests": ["Art"],
    "duel_idx": None,
    "duel_answered": False,
    "duel_score": 0,
    "duel_total": 0,
    "gemini_key": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─── PUBMED HELPER ─────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch_pubmed_articles(query: str, max_results: int = 3):
    try:
        r = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={"db": "pubmed", "term": query, "retmax": max_results, "retmode": "json", "sort": "relevance"},
            timeout=8,
        )
        ids = r.json()["esearchresult"]["idlist"]
        if not ids:
            return []
        s = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi",
            params={"db": "pubmed", "id": ",".join(ids), "retmode": "json"},
            timeout=8,
        )
        data = s.json()["result"]
        return [
            {
                "title": data[uid].get("title", "No title"),
                "journal": data[uid].get("fulljournalname", data[uid].get("source", "")),
                "pubdate": data[uid].get("pubdate", ""),
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
            }
            for uid in ids
        ]
    except Exception:
        return []

# ─── HEADER ────────────────────────────────────────────────
col_logo, col_title = st.columns([1, 9])
with col_logo:
    st.markdown("## 🩺")
with col_title:
    st.markdown("# Cura")
    st.markdown(
        '<p style="color:#9e9e9e; margin-top:-12px;">Cognitive-Adaptive Medical Partner &nbsp;'
        '<span class="badge">MVP · Hackathon 2026</span></p>',
        unsafe_allow_html=True,
    )
st.divider()

# ─── SIDEBAR ───────────────────────────────────────────────
with st.sidebar:
    # Stats
    user_pts = st.session_state.points
    user_rank = sum(1 for e in MOCK_LEADERBOARD if e["pts"] > user_pts) + 1
    st.markdown(
        f'<div style="text-align:center;margin-bottom:1rem;">'
        f'<div style="font-size:1.8rem;">🏆</div>'
        f'<div style="font-size:1.5rem;font-weight:700;color:#ffd200;">{user_pts} pts</div>'
        f'<div class="streak-badge">🔥 {st.session_state.streak}-day streak</div>'
        f'<div style="color:#9e9e9e;font-size:0.8rem;margin-top:4px;">Global Rank #{user_rank}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    # Cognitive Load
    st.markdown("### 🧠 Cognitive Load")
    energy = st.slider("Energy Level", 1, 10, 7)
    if energy <= 3:
        st.warning("⚡ Low energy! Take a break.")
    elif energy <= 6:
        st.info("🔶 Moderate — pace yourself.")
    else:
        st.success("✅ Great energy!")

    st.divider()

    # ── Pomodoro Timer ──
    st.markdown("### ⏱️ Pomodoro Timer")

    if st.session_state.pomodoro_mode == "idle":
        w = st.slider("Work (min)", 10, 50, st.session_state.pomodoro_work_mins, key="w_slider")
        b = st.slider("Break (min)", 2, 15, st.session_state.pomodoro_break_mins, key="b_slider")
        st.session_state.pomodoro_work_mins = w
        st.session_state.pomodoro_break_mins = b
        if st.button("▶️ Start Focus Session"):
            st.session_state.pomodoro_start = time_module.time()
            st.session_state.pomodoro_mode = "work"
            st.rerun()
    else:
        elapsed = time_module.time() - st.session_state.pomodoro_start
        if st.session_state.pomodoro_mode == "work":
            total = st.session_state.pomodoro_work_mins * 60
            remaining = max(0, total - elapsed)
            if remaining == 0:
                st.session_state.pomodoro_mode = "break"
                st.session_state.pomodoro_start = time_module.time()
                st.rerun()
            mins, secs = int(remaining // 60), int(remaining % 60)
            st.markdown(f'<div class="pomodoro-display">🍅 {mins:02d}:{secs:02d}</div>', unsafe_allow_html=True)
            st.caption("Focus session in progress… Refresh to update.")
        else:
            total = st.session_state.pomodoro_break_mins * 60
            remaining = max(0, total - elapsed)
            if remaining == 0:
                st.session_state.pomodoro_mode = "idle"
                st.session_state.points += 50
                st.rerun()
            mins, secs = int(remaining // 60), int(remaining % 60)
            st.markdown(f'<div class="pomodoro-display">☕ {mins:02d}:{secs:02d}</div>', unsafe_allow_html=True)
            st.caption("Break time! Enjoy your palate cleanser ↓")
            hobbies = st.session_state.hobby_interests
            if hobbies:
                h = random.choice(hobbies)
                content = HOBBY_CONTENT.get(h, HOBBY_CONTENT["Art"])
                st.markdown(f"**{content['emoji']} {content['title']}**")
                st.markdown(content["content"])
                st.image(content["image"], use_container_width=True)

        if st.button("⏹️ Stop Timer"):
            st.session_state.pomodoro_mode = "idle"
            st.session_state.pomodoro_start = None
            st.rerun()

        if st.button("🔄 Refresh Timer"):
            st.rerun()

    st.divider()

    # Hobby Interests
    st.markdown("### 🎭 Break Interests")
    all_hobbies = list(HOBBY_CONTENT.keys())
    selected = st.multiselect("Shown during breaks:", all_hobbies, default=st.session_state.hobby_interests)
    if selected:
        st.session_state.hobby_interests = selected

    st.divider()

    # Progress
    st.markdown("### 📊 Learning Progress")
    st.markdown("**Immunology Recall**")
    st.progress(1.0 if st.session_state.immunology_passed else 0.0)
    st.markdown("**Pathology: Cell Injury**")
    st.progress(1.0 if st.session_state.pathology_passed else 0.0)

    st.divider()

    # Gemini Key
    st.markdown("### 🔑 Gemini API Key")
    st.markdown(
        '<p style="color:#9e9e9e;font-size:0.75rem;">Free key: '
        '<a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:#90caf9;">'
        'aistudio.google.com</a></p>',
        unsafe_allow_html=True,
    )
    gk = st.text_input("API Key", type="password", placeholder="AIza...", value=st.session_state.gemini_key)
    if gk:
        st.session_state.gemini_key = gk

# ─── MAIN TABS ─────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🧠  Learning Path", "🏟️  Medical Arena", "💬  Chat with Cura"])

# ══════════════════════════════════════════════════════════
# TAB 1 — LEARNING PATH
# ══════════════════════════════════════════════════════════
with tab1:
    # Step 1: Bridge Protocol
    if not st.session_state.immunology_passed:
        st.markdown('<div class="cura-card">', unsafe_allow_html=True)
        st.markdown("### 🔒 Bridge Protocol — Day 1")
        st.warning("**Topic Locked:** Pass the Immunology Recall Quiz to unlock Pathology.")
        st.markdown('<div class="step-label">Step 1 of 2 — Immunology Recall</div>', unsafe_allow_html=True)
        st.markdown("#### 💬 Cura asks:")
        st.markdown("> *What are the **4 cardinal signs of acute inflammation**? (Latin terms)*")

        answer = st.text_input("Your answer:", placeholder="e.g. rubor, calor, tumor, dolor", key="immuno_ans")
        if st.button("🚀 Submit Recall Quiz"):
            keywords = ["rubor", "calor", "tumor", "dolor"]
            if all(w in answer.lower() for w in keywords):
                st.success("✅ Bridge Protocol Passed! Pathology is now unlocked.")
                st.balloons()
                st.session_state.immunology_passed = True
                st.session_state.points += 100
                st.session_state.streak += 1
                st.rerun()
            else:
                missing = [k for k in keywords if k not in answer.lower()]
                st.error(f"❌ Missing: **{', '.join(missing)}**. Review before moving forward.")
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        # Unlocked banner
        st.markdown('<div class="cura-card">', unsafe_allow_html=True)
        st.success("🔓 Immunology Recall Complete — Pathology Unlocked (+100 pts)")
        st.markdown("</div>", unsafe_allow_html=True)

        # Step 2: Knowledge Gap Analysis
        st.markdown('<div class="cura-card">', unsafe_allow_html=True)
        st.markdown("### 🧬 Topic: Cell Injury (Pathology)")
        st.markdown('<div class="step-label">Step 2 of 2 — Active Knowledge Gap Analysis</div>', unsafe_allow_html=True)
        st.markdown("#### 💬 Cura asks:")
        st.markdown("> *What do you already know about **Cell Necrosis vs. Apoptosis**? Share what you recall from your lecture.*")

        user_input = st.text_area(
            "Your response:", height=160,
            placeholder="e.g. Necrosis involves ATP depletion and inflammation, while apoptosis is programmed death...",
            key="patho_input",
        )

        if st.button("🔍 Identify Gaps"):
            if not user_input.strip():
                st.warning("Please enter your response before analyzing.")
            else:
                missing_points = {k: v for k, v in PATHOLOGY_POINTS.items() if k.lower() not in user_input.lower()}
                covered = [k for k in PATHOLOGY_POINTS if k.lower() in user_input.lower()]

                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("##### ✅ What You Know")
                    if covered:
                        for c in covered:
                            st.markdown(
                                f'<div style="background:rgba(78,205,196,0.1);border:1px solid rgba(78,205,196,0.3);'
                                f'border-radius:10px;padding:0.5rem 1rem;margin-bottom:0.4rem;color:#80cbc4;font-weight:500;">✔ {c}</div>',
                                unsafe_allow_html=True,
                            )
                    else:
                        st.markdown("*None of the high-yield points detected yet.*")

                with col_b:
                    st.markdown("##### 🔴 Knowledge Gaps")
                    if missing_points:
                        for gap, explanation in missing_points.items():
                            st.markdown(f'<div class="gap-item">🔴 <b>{gap}</b></div>', unsafe_allow_html=True)
                            st.caption(f"💡 {explanation}")
                    else:
                        st.success("🎉 No gaps found! You've covered all high-yield points.")

                if not missing_points:
                    st.balloons()
                    st.session_state.pathology_passed = True
                    st.session_state.points += 150
                    st.markdown("#### 💬 Cura says:")
                    st.markdown("> *Perfect. You have the full foundation. Let's move to **Clinical Cases**. 🏥*")
                else:
                    st.markdown("#### 💬 Cura says:")
                    st.markdown(
                        f"> *Good start! You missed **{len(missing_points)}** high-yield point(s). "
                        f"Review them above, then try again.*"
                    )
                    st.markdown("---")

                    col_res, col_pub = st.columns(2)
                    with col_res:
                        st.markdown("#### 📚 Lecture Resources")
                        for res in LECTURE_RESOURCES:
                            st.markdown(
                                f'<div class="cura-card" style="padding:0.8rem 1.2rem;">'
                                f'<a href="{res["url"]}" target="_blank" style="color:#90caf9;font-weight:600;text-decoration:none;">'
                                f'🔗 {res["title"]}</a></div>',
                                unsafe_allow_html=True,
                            )
                    with col_pub:
                        st.markdown("#### 🔬 PubMed Evidence")
                        gap_query = "cell necrosis apoptosis " + " ".join(missing_points.keys())
                        with st.spinner("Searching PubMed…"):
                            articles = fetch_pubmed_articles(gap_query)
                        if articles:
                            for art in articles:
                                st.markdown(
                                    f'<div class="cura-card" style="padding:0.8rem 1.2rem;">'
                                    f'<a href="{art["url"]}" target="_blank" style="color:#90caf9;font-weight:600;text-decoration:none;">'
                                    f'🔗 {art["title"]}</a><br>'
                                    f'<span style="color:#9e9e9e;font-size:0.78rem;">{art["journal"]} · {art["pubdate"]}</span>'
                                    f'</div>',
                                    unsafe_allow_html=True,
                                )
                        else:
                            st.caption("⚠️ PubMed unreachable. Check your connection.")

        st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════
# TAB 2 — MEDICAL ARENA
# ══════════════════════════════════════════════════════════
with tab2:
    # Stats Row
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f'<div class="stat-card"><div style="font-size:2rem;">🔥</div>'
            f'<div style="font-size:1.8rem;font-weight:700;color:#ffd200;">{st.session_state.streak}</div>'
            f'<div style="color:#9e9e9e;">Day Streak</div></div>',
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f'<div class="stat-card"><div style="font-size:2rem;">⭐</div>'
            f'<div style="font-size:1.8rem;font-weight:700;color:#90caf9;">{st.session_state.points}</div>'
            f'<div style="color:#9e9e9e;">Total Points</div></div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="stat-card"><div style="font-size:2rem;">🏅</div>'
            f'<div style="font-size:1.8rem;font-weight:700;color:#ce93d8;">#{user_rank}</div>'
            f'<div style="color:#9e9e9e;">Global Rank</div></div>',
            unsafe_allow_html=True,
        )

    st.divider()

    col_lb, col_duel = st.columns([1, 1])

    # ── Leaderboard ──
    with col_lb:
        st.markdown("### 🥇 Global Leaderboard")
        combined = [dict(e) for e in MOCK_LEADERBOARD]
        combined.append({
            "name": "You ⭐", "flag": "🧑‍⚕️",
            "pts": st.session_state.points, "streak": st.session_state.streak,
            "is_user": True,
        })
        combined.sort(key=lambda x: x["pts"], reverse=True)

        rank_icons = {1: "🥇", 2: "🥈", 3: "🥉"}
        rank_styles = {1: "rank-1", 2: "rank-2", 3: "rank-3"}

        for i, entry in enumerate(combined[:9]):
            rank = i + 1
            icon  = rank_icons.get(rank, f"#{rank}")
            style = rank_styles.get(rank, "")
            extra = "user-row" if entry.get("is_user") else ""
            st.markdown(
                f'<div class="leaderboard-row {style} {extra}">'
                f'<span>{icon} {entry["flag"]} {entry["name"]}</span>'
                f'<span style="color:#ffd200;font-weight:600;">{entry["pts"]} pts</span>'
                f'<span style="color:#ff8a80;font-size:0.85rem;">🔥 {entry["streak"]}d</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    # ── Clinical Vignette Duel ──
    with col_duel:
        st.markdown("### ⚔️ Clinical Vignette Duel")
        sc, tot = st.session_state.duel_score, st.session_state.duel_total
        accuracy = f"{int(sc/tot*100)}%" if tot > 0 else "—"
        st.markdown(
            f'<div style="display:flex;gap:1.5rem;margin-bottom:1rem;">'
            f'<span style="color:#90caf9;">✅ Score: <b>{sc}/{tot}</b></span>'
            f'<span style="color:#ffd200;">🎯 Accuracy: <b>{accuracy}</b></span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        if st.session_state.duel_idx is None:
            st.markdown("Test your diagnostic speed with real clinical vignettes!")
            if st.button("🎯 Start Duel"):
                st.session_state.duel_idx = random.randint(0, len(VIGNETTES) - 1)
                st.session_state.duel_answered = False
                st.rerun()
        else:
            v = VIGNETTES[st.session_state.duel_idx]
            st.markdown(
                f'<div class="vignette-card">'
                f'<p style="color:#e0e0e0;line-height:1.6;">{v["case"]}</p>'
                f'<p style="color:#90caf9;font-weight:600;margin-top:0.8rem;">❓ {v["question"]}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )

            if not st.session_state.duel_answered:
                for i, opt in enumerate(v["options"]):
                    if st.button(opt, key=f"vopt_{i}"):
                        st.session_state.duel_total += 1
                        st.session_state.duel_answered = True
                        if i == v["answer"]:
                            st.session_state.duel_score += 1
                            st.session_state.points += 75
                            st.success(f"✅ Correct! +75 pts")
                        else:
                            st.error(f"❌ Incorrect.")
                        st.rerun()
            else:
                st.info(f"💡 **Explanation:** {v['explanation']}")
                if st.button("➡️ Next Case"):
                    st.session_state.duel_idx = random.randint(0, len(VIGNETTES) - 1)
                    st.session_state.duel_answered = False
                    st.rerun()
                if st.button("⏹️ End Duel"):
                    st.session_state.duel_idx = None
                    st.rerun()


# ══════════════════════════════════════════════════════════
# TAB 3 — CHAT WITH CURA AI
# ══════════════════════════════════════════════════════════
with tab3:
    st.markdown(
        '<div class="cura-card">'
        '<h3>💬 Chat with Cura AI</h3>'
        '<p style="color:#9e9e9e;margin-top:-8px;">Ask anything about medicine, pathology, or your studies.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    gemini_key = st.session_state.get("gemini_key", "")

    if not gemini_key:
        st.info("🔑 Enter your free Gemini API key in the sidebar to activate Cura AI.")
    elif not GENAI_AVAILABLE:
        st.error("⚠️ google-generativeai not installed. Run: pip3 install google-generativeai")
    else:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"], avatar="🩺" if msg["role"] == "assistant" else "👤"):
                st.markdown(msg["content"])

        user_q = st.chat_input("Ask Cura a medical question…")
        if user_q:
            with st.chat_message("user", avatar="👤"):
                st.markdown(user_q)
            st.session_state.chat_history.append({"role": "user", "content": user_q})

            with st.chat_message("assistant", avatar="🩺"):
                with st.spinner("Cura is thinking…"):
                    try:
                        genai.configure(api_key=gemini_key)
                        model = genai.GenerativeModel(
                            model_name="gemini-1.5-flash",
                            system_instruction=(
                                "You are Cura, a Cognitive-Adaptive Medical Partner for medical students. "
                                "Help with pathology, immunology, pharmacology, and clinical medicine. "
                                "Be concise and educational. Use bullet points. "
                                "Flag high-yield exam points with ⭐. "
                                "Cite PubMed / clinical guidelines when relevant. "
                                "If asked something non-medical, gently redirect to medicine."
                            ),
                        )
                        history = [
                            {"role": m["role"], "parts": [m["content"]]}
                            for m in st.session_state.chat_history[:-1]
                        ]
                        chat = model.start_chat(history=history)
                        reply = chat.send_message(user_q).text
                    except Exception as e:
                        reply = f"❌ Error: {e}. Check your API key."
                st.markdown(reply)
            st.session_state.chat_history.append({"role": "assistant", "content": reply})

        if st.session_state.chat_history:
            if st.button("🗑️ Clear Chat"):
                st.session_state.chat_history = []
                st.rerun()
