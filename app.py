import streamlit as st
from groq import Groq
import re
import os
import sqlite3
from datetime import datetime

# ---------------------------------------------------------
# Page Setup: Clean & Attractive Visual Workspace
# ---------------------------------------------------------
st.set_page_config(
    page_title="Loksewa Agri Visual Master Engine",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom High-Contrast, Eye-Catching Dashboard Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@500;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .block-container { 
        padding-top: 1.5rem; 
        padding-bottom: 3.5rem; 
    }
    
    /* Top Hero Infographic Banner */
    .hero-banner {
        background: linear-gradient(135deg, #064e3b 0%, #047857 50%, #059669 100%);
        border-radius: 14px;
        padding: 22px 28px;
        color: #ffffff;
        margin-bottom: 24px;
        box-shadow: 0 8px 20px rgba(6, 78, 59, 0.25);
    }
    .hero-banner h1 {
        color: #ffffff;
        font-weight: 800;
        font-size: 2.1rem;
        margin-bottom: 6px;
    }
    .hero-banner p {
        color: #a7f3d0;
        font-size: 1.05rem;
        margin: 0;
        font-weight: 500;
    }
    
    /* Action Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Internal SQLite Vault (Saves in System, Not on PC)
# ---------------------------------------------------------
DB_FILE = "loksewa_visual_vault.db"

def init_vault_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS visual_vault (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            question TEXT,
            answer TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_to_vault(question, answer):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute(
        "INSERT INTO visual_vault (timestamp, question, answer) VALUES (?, ?, ?)",
        (now, question, answer)
    )
    conn.commit()
    conn.close()

def get_all_vault_items():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, timestamp, question, answer FROM visual_vault ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def delete_vault_item(item_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM visual_vault WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

init_vault_db()

# ---------------------------------------------------------
# Configuration: Groq API Key & Auto Model Discovery
# ---------------------------------------------------------
api_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))

# ---------------------------------------------------------
# Fail-Safe Context-Adaptive System Prompt
# ---------------------------------------------------------
DYNAMIC_CONTEXT_SYSTEM_PROMPT = """
You are the Chief Examination Answer Architect and Senior Agriculture Specialist for the Nepal Public Service Commission (Gazetted 3rd Class Agriculture Officer).

ABSOLUTE MANDATE: ZERO PRESET OR RECYCLED BOILERPLATE!
Every question must be analyzed contextually. NEVER force-fit unrelated laws. Adapt dynamically to the specific discipline.

CRITICAL INSTRUCTION - NO MERMAID CODE BLOCKS:
Do NOT output ```mermaid code blocks. Present all visual models using clean, formatted Markdown visual structures, high-contrast tables, bulleted frameworks, and ASCII blueprints.

1. CONTEXTUAL POLICY CITATION (SUBSTANCE ONLY):
Cite ONLY the specific acts, standards, or guidelines governing that domain and state WHAT the policy actually mandates:
- Food Hygiene & Quality Act 2081 (Sec. 14 for MRL/traceability & seizure powers)
- Seeds Act 2045 (Amended 2079, Sec. 16 for Truthful Labeling, min 85% germination & 98% purity)
- Plant Protection Act 2064 & Pesticides Management Act 2076 (Sec. 8 banned list & strict PHI)
- 16th Periodic Plan (2081/82 - 2085/86: 4.5% sector growth, 50 cold corridors, <12% post-harvest loss)
- Agriculture Development Strategy (ADS 2015-2035: Productivity & Commercialization pillars)
- Constitution of Nepal (Art. 36: Food Sovereignty; Art. 51: State agricultural policies)

2. MANDATORY: EXTENSIVE DEPTH IN SWOT & MATRICES (>5 POINTS EACH):
- For SWOT Analysis: You MUST provide MORE THAN 5 POINTS (at least 6-7 distinct, highly technical points) in EACH of the 4 quadrants:
  * Strengths (6+ points): Concrete Nepali agro-climatic, genetic, or institutional assets.
  * Weaknesses (6+ points): Specific structural, input, yield gap, and infrastructure deficits.
  * Opportunities (6+ points): Commercialization, export, processing, and digital horizons.
  * Threats (6+ points): Climate vulnerabilities, vector outbreaks, market volatility, and SPS competition.
- For 2x2 Decision Matrix / Analytical Comparison:
  * MUST contain MORE THAN 5 DISTINCT CRITERIA (at least 6-7 rows comparing Technical Parameters, Field Protocols, Implementing Agencies, Measurable KPIs, Legal Acts, and Risk Mitigations).

3. ABSOLUTELY ZERO <br> TAGS:
Never write <br> or <br/> tags anywhere in the output. Use standard markdown line breaks.

MANDATORY 10-MARK STRUCTURE:
1. EXECUTIVE SNAPSHOT:
   - Precise 2-line technical definition.
   - Commodity/Topic-specific baseline data from Nepal Agricultural Census 2078 or latest MoALD reports.
2. FIGURE 1: PRIMARY SEQUENTIAL FLOW ARCHITECTURE:
   - Present a clean, structured linear step-by-step visual pipeline using bold headings and bulleted standards (5-6 sequential phases).
3. FIGURE 2: EXTENSIVE SWOT ANALYSIS (>5 POINTS PER QUADRANT):
   - 6+ Strengths, 6+ Weaknesses, 6+ Opportunities, 6+ Threats.
4. FIGURE 3: 2x2 DECISION MATRIX / ANALYTICAL COMPARISON:
   - A structured comparative matrix with 6+ distinct technical and operational criteria.
5. FIGURE 4: 45-SECOND EXAM HAND-DRAWN BLUEPRINT:
   - A clean ASCII box diagram that candidates can sketch with pen/pencil in 45 seconds on their paper.
6. FIGURE 5: SUBSTANTIVE POLICY & TECHNICAL MATRIX:
   - Table with 6+ rows connecting each phase to exact technical standards and substantive legal mandates.
"""

# ---------------------------------------------------------
# Robust Helper Functions
# ---------------------------------------------------------
def get_working_groq_model(client: Groq) -> str:
    priority_order = [
        "openai/gpt-oss-120b",
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-20b",
        "llama-3.1-8b-instant"
    ]
    try:
        active_models = client.models.list()
        active_ids = {m.id for m in active_models.data}
        for candidate in priority_order:
            if candidate in active_ids:
                return candidate
        for m in active_ids:
            if "whisper" not in m and "guard" not in m:
                return m
    except Exception:
        pass
    return "openai/gpt-oss-120b"

def sanitize_markdown_text(text: str) -> str:
    """Removes stray <br> tags and any unwanted raw mermaid blocks."""
    if not text:
        return ""
    # Strip <br> tags
    text = re.sub(r'(?:<br\s*/?>|&lt;br\s*/?&gt;)', '\n', text, flags=re.IGNORECASE)
    # Strip any stray mermaid blocks if generated
    text = re.sub(r'```(?:mermaid|Mermaid)[\s\S]*?```', '', text)
    return text.strip()

# ---------------------------------------------------------
# Top Header Banner
# ---------------------------------------------------------
st.markdown("""
<div class="hero-banner">
    <h1>🌱 Loksewa Agri Officer: Master Visual Engine</h1>
    <p>Contextual Policy Mandates • Extensive SWOT (>5 Points) • 2x2 Decision Matrix • In-System Vault</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Working Tabs
# ---------------------------------------------------------
tab_generator, tab_vault = st.tabs(["📊 Dynamic Visual Generator", "📚 In-System Revision Vault"])

# =========================================================
# TAB 1: DYNAMIC VISUAL GENERATOR
# =========================================================
with tab_generator:
    user_query = st.text_area(
        "Enter Loksewa Question / Syllabus Topic (10 Marks):",
        placeholder="Type any syllabus topic (e.g., Training and Pruning Systems in Deciduous Fruit Trees, Biological Nitrogen Fixation, Law of Diminishing Returns, Citrus Decline Management)...",
        height=110
    )

    if st.button("Generate Context-Specific Visual Answer", type="primary", use_container_width=True):
        if not api_key:
            st.error("⚠️ GROQ_API_KEY is not set. Please add it to your Streamlit Cloud Settings -> Secrets.")
        elif not user_query.strip():
            st.warning("⚠️ Please enter a question or topic first.")
        else:
            client = Groq(api_key=api_key)
            active_model = get_working_groq_model(client)
            
            full_prompt = f"""
            Analyze the following question and synthesize an entirely context-specific 10-mark Loksewa answer:
            QUESTION: {user_query}
            WEIGHTAGE: 10 Marks
            
            CRITICAL EXECUTION MANDATES:
            1. DO NOT GENERATE MERMAID CODE BLOCKS. Present visuals using clean Markdown flow architecture, tables, and ASCII blueprints.
            2. FIGURE 1 (SEQUENTIAL FLOW): 5-6 sequential stages with bold titles and exact technical standards.
            3. FIGURE 2 (SWOT ANALYSIS): Provide MORE THAN 5 POINTS (at least 6-7 distinct, highly technical points) in EACH of the 4 quadrants!
            4. FIGURE 3 (2x2 DECISION MATRIX): Table with at least 6-7 criteria rows comparing technical, financial, and policy dimensions.
            5. FIGURE 4 (ASCII BLUEPRINT): Clean 45-second drawing for exam answer sheet.
            6. FIGURE 5 (POLICY & TECHNICAL MATRIX): Table with at least 6-7 rows specifying exact technical standards and substantive legal mandates.
            7. CONTEXTUAL POLICY CITATION: Cite ONLY the acts and guidelines that legally apply to this specific subject matter and state what they mandate.
            """
            
            with st.spinner(f"Analyzing subject context and synthesizing tailored visual architecture with ({active_model})..."):
                try:
                    completion = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": DYNAMIC_CONTEXT_SYSTEM_PROMPT},
                            {"role": "user", "content": full_prompt}
                        ],
                        model=active_model,
                        temperature=0.2,
                        max_tokens=4096
                    )
                    
                    raw_answer = completion.choices[0].message.content
                    clean_answer = sanitize_markdown_text(raw_answer)
                    
                    st.session_state["current_question"] = user_query
                    st.session_state["current_answer"] = clean_answer
                    
                except Exception as err:
                    st.error(f"Error communicating with Groq API: {str(err)}")

    # Result Section
    if "current_answer" in st.session_state:
        st.markdown("---")
        
        # Save to System Vault Action Button
        if st.button("💾 Save to Revision Vault (Inside System)", use_container_width=True):
            save_to_vault(
                st.session_state["current_question"],
                st.session_state["current_answer"]
            )
            st.success("✅ Successfully saved to your internal vault! You can study it anytime in the 'In-System Revision Vault' tab.")

        # Full Visual-Dominant Exam Sheet Display
        st.markdown(st.session_state["current_answer"])

# =========================================================
# TAB 2: IN-SYSTEM REVISION VAULT (Saved On Server)
# =========================================================
with tab_vault:
    st.subheader("📚 In-System Revision Vault")
    st.caption("Saved answers remain stored inside the server database. No files are downloaded to your personal computer.")
    
    saved_items = get_all_vault_items()
    
    if not saved_items:
        st.info("Your vault is currently empty. Generate a visual answer in Tab 1 and click '💾 Save to Revision Vault'.")
    else:
        for item in saved_items:
            item_id, item_time, item_q, item_ans = item
            
            with st.expander(f"📌 {item_q} (Saved: {item_time})", expanded=False):
                if st.button("🗑️ Delete from Vault", key=f"del_{item_id}", use_container_width=True):
                    delete_vault_item(item_id)
                    st.rerun()

                st.markdown(item_ans)
