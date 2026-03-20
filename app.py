import streamlit as st
import requests
try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Cura – Cognitive-Adaptive Medical Partner",
    page_icon="🩺",
    layout="wide",
)

# --- CUSTOM CSS ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Dark gradient background */
    .stApp {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        min-height: 100vh;
    }

    /* Main content area */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* Card-style containers */
    .cura-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 1.5rem;
        backdrop-filter: blur(12px);
        margin-bottom: 1rem;
    }

    /* Glow effect on buttons */
    .stButton > button {
        background: linear-gradient(90deg, #667eea, #764ba2) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6) !important;
    }

    /* Text inputs */
    .stTextInput > div > input, .stTextArea > div > textarea {
        background: rgba(255,255,255,0.08) !important;
        border: 1px solid rgba(255,255,255,0.2) !important;
        border-radius: 10px !important;
        color: #e0e0e0 !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(15, 12, 41, 0.8) !important;
        border-right: 1px solid rgba(255,255,255,0.1) !important;
    }

    /* Titles */
    h1, h2, h3 {
        color: #e0e0e0 !important;
    }

    /* Alert / info boxes */
    .stAlert {
        border-radius: 12px !important;
    }

    /* Divider */
    hr {
        border-color: rgba(255,255,255,0.15) !important;
    }

    /* Badge pill */
    .badge {
        display: inline-block;
        background: linear-gradient(90deg, #667eea, #764ba2);
        color: white;
        padding: 3px 12px;
        border-radius: 50px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-left: 8px;
        vertical-align: middle;
    }

    .gap-item {
        display: flex;
        align-items: center;
        gap: 8px;
        background: rgba(255, 82, 82, 0.10);
        border: 1px solid rgba(255, 82, 82, 0.3);
        border-radius: 10px;
        padding: 0.5rem 1rem;
        margin-bottom: 0.4rem;
        color: #ff8a80;
        font-weight: 500;
    }

    .step-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        color: #9e9e9e;
        margin-bottom: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)


# --- PUBMED HELPER ---
@st.cache_data(ttl=300)
def fetch_pubmed_articles(query: str, max_results: int = 3):
    """Search PubMed and return article summaries."""
    try:
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        search_params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": "relevance",
        }
        r = requests.get(search_url, params=search_params, timeout=8)
        ids = r.json()["esearchresult"]["idlist"]
        if not ids:
            return []

        summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        summary_params = {"db": "pubmed", "id": ",".join(ids), "retmode": "json"}
        s = requests.get(summary_url, params=summary_params, timeout=8)
        data = s.json()["result"]

        articles = []
        for uid in ids:
            item = data.get(uid, {})
            title = item.get("title", "No title")
            journal = item.get("fulljournalname", item.get("source", ""))
            pubdate = item.get("pubdate", "")
            articles.append({
                "title": title,
                "journal": journal,
                "pubdate": pubdate,
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{uid}/",
            })
        return articles
    except Exception:
        return []


# --- 1. HEADER ---
col_logo, col_title = st.columns([1, 9])
with col_logo:
    st.markdown("## 🩺")
with col_title:
    st.markdown("# Cura")
    st.markdown('<p style="color:#9e9e9e; margin-top:-12px;">Cognitive-Adaptive Medical Partner &nbsp;<span class="badge">MVP · Hackathon 2026</span></p>', unsafe_allow_html=True)

st.divider()


# --- 2. SESSION STATE INIT ---
if 'immunology_passed' not in st.session_state:
    st.session_state.immunology_passed = False
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []


# --- 3. SIDEBAR: COGNITIVE LOAD TRACKER ---
with st.sidebar:
    st.markdown("### 🧠 Cognitive Load Tracker")
    st.markdown('<p class="step-label">How are you feeling?</p>', unsafe_allow_html=True)

    energy = st.slider("Energy Level", 1, 10, 7, help="Rate your current energy from 1 (exhausted) to 10 (fully alert)")
    
    if energy <= 3:
        st.warning("⚡ Low energy detected. Consider a short break.")
    elif energy <= 6:
        st.info("🔶 Moderate load. Pace yourself.")
    else:
        st.success("✅ Great energy! Keep going.")

    st.divider()

    if st.button("😴 I'm feeling tired"):
        st.info("🎨 Triggering Palate Cleanser...")
        st.image(
            "https://images.unsplash.com/photo-1579783902614-a3fb3927b6a5?q=80&w=400",
            caption="5-minute Art Break — breathe, reset, refocus.",
            use_container_width=True
        )

    st.divider()
    st.markdown("### 📊 Progress")
    progress_val = 1.0 if st.session_state.immunology_passed else 0.0
    st.markdown("**Immunology Recall**")
    st.progress(progress_val)
    st.markdown("**Pathology: Cell Injury**")
    st.progress(0.0)

    st.divider()
    st.markdown("### 🔑 Gemini API Key")
    st.markdown('<p style="color:#9e9e9e;font-size:0.75rem;">Free key: <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:#90caf9;">aistudio.google.com</a></p>', unsafe_allow_html=True)
    gemini_key = st.text_input("API Key", type="password", placeholder="AIza...")
    if gemini_key:
        st.session_state['gemini_key'] = gemini_key


# --- 4. BRIDGE PROTOCOL (GATEKEEPER) ---
if not st.session_state.immunology_passed:
    st.markdown('<div class="cura-card">', unsafe_allow_html=True)
    st.markdown("### 🔒 Bridge Protocol")
    st.warning("**Topic Locked:** Complete the Immunology Recall Quiz to unlock Pathology.")
    
    st.markdown('<div class="step-label">Step 1 of 2 — Immunology Recall</div>', unsafe_allow_html=True)
    st.markdown("#### 💬 Cura asks:")
    st.markdown("> *What are the **4 cardinal signs of acute inflammation**? (Use the Latin terms)*")
    
    answer = st.text_input("Your answer:", placeholder="e.g. rubor, calor, tumor, dolor")
    
    if st.button("🚀 Submit Recall Quiz"):
        keywords = ["rubor", "calor", "tumor", "dolor"]
        if all(word in answer.lower() for word in keywords):
            st.success("✅ Bridge Protocol Passed! Pathology is now unlocked.")
            st.balloons()
            st.session_state.immunology_passed = True
            st.rerun()
        else:
            missing = [k for k in keywords if k not in answer.lower()]
            st.error(f"❌ Knowledge Gap Detected. Missing: **{', '.join(missing)}**. Review Immunology before moving forward.")
    
    st.markdown("</div>", unsafe_allow_html=True)

else:
    # --- 5. PATHOLOGY MODULE ---
    st.markdown('<div class="cura-card">', unsafe_allow_html=True)
    st.success("🔓 Immunology Recall Complete — Pathology Unlocked")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="cura-card">', unsafe_allow_html=True)
    st.markdown("### 🧬 New Topic: Cell Injury (Pathology)")
    st.markdown('<div class="step-label">Step 2 of 2 — Knowledge Gap Analysis</div>', unsafe_allow_html=True)

    st.markdown("#### 💬 Cura asks:")
    st.markdown("> *What do you already know about **Cell Necrosis vs. Apoptosis**? Share what you recall from your lecture.*")

    user_input = st.text_area(
        "Your response:",
        height=160,
        placeholder="e.g. Necrosis involves ATP depletion and inflammation, while apoptosis is programmed cell death..."
    )

    # Lecture high-yield points
    lecture_points = {
        "ATP depletion": "ATP depletion leads to failure of the Na⁺/K⁺ pump → cell swelling → necrosis.",
        "Mitochondrial damage": "Mitochondrial damage releases cytochrome c, triggering apoptosis cascade.",
        "Membrane permeability": "Increased membrane permeability is key in necrosis — enzymes leak out causing inflammation.",
        "Inflammation": "Necrosis triggers inflammation; apoptosis does NOT (it is immunologically silent).",
    }

    if st.button("🔍 Identify Gaps"):
        if not user_input.strip():
            st.warning("Please enter your response before analyzing gaps.")
        else:
            missing_points = {k: v for k, v in lecture_points.items() if k.lower() not in user_input.lower()}
            covered = [k for k in lecture_points if k.lower() in user_input.lower()]

            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("##### ✅ What You Know")
                if covered:
                    for c in covered:
                        st.markdown(f'<div style="background:rgba(78,205,196,0.1);border:1px solid rgba(78,205,196,0.3);border-radius:10px;padding:0.5rem 1rem;margin-bottom:0.4rem;color:#80cbc4;font-weight:500;">✔ {c}</div>', unsafe_allow_html=True)
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
                st.markdown("#### 💬 Cura says:")
                st.markdown("> *Perfect. You have the full foundation. Let's move to **Clinical Cases**. 🏥*")
            else:
                st.markdown("#### 💬 Cura says:")
                st.markdown(f"> *Good start! You've got the basics, but you missed **{len(missing_points)}** high-yield point(s) from the lecture. Review them above, then try again.*")

                # --- REAL PUBMED REFERENCES ---
                st.markdown("---")
                st.markdown("#### 📚 PubMed References")
                gap_terms = " ".join(missing_points.keys())
                query = f"cell necrosis apoptosis {gap_terms}"
                with st.spinner("Searching PubMed..."):
                    articles = fetch_pubmed_articles(query)
                if articles:
                    for art in articles:
                        st.markdown(
                            f'<div class="cura-card" style="padding:0.8rem 1.2rem;">'
                            f'<a href="{art["url"]}" target="_blank" style="color:#90caf9;font-weight:600;text-decoration:none;">'
                            f'🔗 {art["title"]}</a><br>'
                            f'<span style="color:#9e9e9e;font-size:0.8rem;">{art["journal"]} · {art["pubdate"]}</span>'
                            f'</div>',
                            unsafe_allow_html=True
                        )
                else:
                    st.caption("⚠️ PubMed'e bağlanılamadı. İnternet bağlantınızı kontrol edin.")

    st.markdown("</div>", unsafe_allow_html=True)


# --- 6. AI CHAT SECTION ---
st.divider()
st.markdown("""
<div class="cura-card">
    <h3>💬 Chat with Cura AI</h3>
    <p style="color:#9e9e9e;margin-top:-8px;">Ask Cura anything about medicine, pathology, or your studies.</p>
</div>
""", unsafe_allow_html=True)

gemini_key = st.session_state.get('gemini_key', '')

if not gemini_key:
    st.info("🔑 Enter your free Gemini API key in the sidebar to activate Cura AI Chat.")
elif not GENAI_AVAILABLE:
    st.error("⚠️ google-generativeai package not installed. Run: pip install google-generativeai")
else:
    # Display chat history
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"], avatar="🩺" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])

    # Chat input
    user_question = st.chat_input("Ask Cura a medical question...")

    if user_question:
        # Show user message
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_question)
        st.session_state.chat_history.append({"role": "user", "content": user_question})

        # Generate Gemini response
        with st.chat_message("assistant", avatar="🩺"):
            with st.spinner("Cura is thinking..."):
                try:
                    genai.configure(api_key=gemini_key)
                    model = genai.GenerativeModel(
                        model_name="gemini-1.5-flash",
                        system_instruction=(
                            "You are Cura, a Cognitive-Adaptive Medical Partner. "
                            "You help medical students learn pathology, immunology, and clinical medicine. "
                            "Be concise, educational, and encouraging. Use bullet points when helpful. "
                            "Always cite when a concept is high-yield for exams. "
                            "If asked about something non-medical, gently redirect to medicine."
                        )
                    )
                    # Build history for context
                    history = []
                    for m in st.session_state.chat_history[:-1]:
                        history.append({"role": m["role"], "parts": [m["content"]]})
                    chat = model.start_chat(history=history)
                    response = chat.send_message(user_question)
                    reply = response.text
                except Exception as e:
                    reply = f"❌ Error: {e}. Please check your API key."
            st.markdown(reply)
        st.session_state.chat_history.append({"role": "assistant", "content": reply})

    if st.session_state.chat_history:
        if st.button("🗑️ Clear Chat"):
            st.session_state.chat_history = []
            st.rerun()
