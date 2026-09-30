import streamlit as st
from groq import Groq
import re
import base64
import requests
import os
import sqlite3
from datetime import datetime

# ---------------------------------------------------------
# Page Setup & Professional Exam Visual Theme
# ---------------------------------------------------------
st.set_page_config(
    page_title="Loksewa Agri Officer: Master Visual Engine",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Styling for Visuals, Cards, and Badges
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    .block-container { 
        padding-top: 1.5rem; 
        padding-bottom: 3.5rem; 
    }
    
    /* Top Banner */
    .hero-banner {
        background: linear-gradient(135deg, #14532d 0%, #15803d 50%, #16a34a 100%);
        border-radius: 12px;
        padding: 22px 28px;
        color: #ffffff;
        margin-bottom: 24px;
        box-shadow: 0 4px 14px rgba(20, 83, 45, 0.25);
    }
    .hero-banner h1 {
        color: #ffffff;
        font-weight: 800;
        font-size: 2.1rem;
        margin-bottom: 6px;
    }
    .hero-banner p {
        color: #dcfce7;
        font-size: 1.05rem;
        margin: 0;
    }
    
    /* Diagram Container */
    .diagram-card {
        background: #ffffff;
        border: 2px solid #cbd5e1;
        border-radius: 12px;
        padding: 22px;
        margin: 20px 0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }
    
    /* Full-Screen External Link Button */
    .open-window-btn {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: linear-gradient(135deg, #15803d 0%, #166534 100%);
        color: #ffffff !important;
        padding: 11px 22px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 700;
        font-size: 0.95rem;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 2px 8px rgba(21, 128, 61, 0.35);
    }
    .open-window-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(21, 128, 61, 0.45);
        color: #ffffff !important;
    }

    /* Monospace Blueprint Block */
    .ascii-box {
        background-color: #f8fafc;
        border: 1.5px solid #94a3b8;
        border-radius: 8px;
        padding: 16px;
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.88rem;
        line-height: 1.45;
        color: #0f172a;
        overflow-x: auto;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Internal SQLite Vault (Saves Files in System, Not on PC)
# ---------------------------------------------------------
DB_FILE = "loksewa_internal_vault.db"

def init_vault_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS vault (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            question TEXT,
            answer TEXT,
            mermaid_code TEXT,
            image_url TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_to_vault(question, answer, mermaid_code, image_url):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    c.execute(
        "INSERT INTO vault (timestamp, question, answer, mermaid_code, image_url) VALUES (?, ?, ?, ?, ?)",
        (now, question, answer, mermaid_code, image_url)
    )
    conn.commit()
    conn.close()

def get_all_vault_items():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, timestamp, question, answer, mermaid_code, image_url FROM vault ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def delete_vault_item(item_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM vault WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()

init_vault_db()

# ---------------------------------------------------------
# Configuration: Groq API Key & Auto Model Discovery
# ---------------------------------------------------------
api_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))

SYSTEM_PROMPT = """
You are a senior Nepalese Agriculture Officer, Loksewa answer evaluator, policy specialist, and technical examination answer architect.
Your mission is to produce a HIGH-SCORING, 10-MARK answer for the Nepal Public Service Commission (Gazetted 3rd Class Agriculture Officer) examination across all disciplines (Agricultural Extension, Agricultural Economics, Soil Science, Agronomy, Horticulture, and Plant Protection).

CRITICAL RULE 1: STRICT CATEGORICAL & CHRONOLOGICAL DIAGRAM ORDERING (NO RANDOM STRUCTURING)
Never arrange diagram steps arbitrarily. Group and order all diagrams according to logical technical dimensions:
1. PEST / DISEASE / WEED MANAGEMENT QUESTIONS:
   Order strictly by the IPM Safety & Toxicity Hierarchy (Least toxic/preventative -> Most toxic/last resort):
   Stage 1: Host Plant Resistance (Genetic tolerance, resistant rootstocks, certified seed)
   Stage 2: Cultural / Agronomic (Sanitation, solarization, crop rotation, trap crops, spacing)
   Stage 3: Physical & Mechanical (Hand-picking, yellow sticky traps, pheromone traps, light traps)
   Stage 4: Biological & Microbial (Parasitoids, predators, Trichoderma, Beauveria, Metarhizium, Bt)
   Stage 5: Biorational & Botanicals (Neem-based azadirachtin, bio-fungicides)
   Stage 6: Chemical Controls (Last Resort: Green-label only, ETL-based, strict Pre-Harvest Interval)

2. CROP PRODUCTION / HORTICULTURE / AGRONOMY QUESTIONS:
   Order strictly by Phenological / Operational Chronology:
   Stage 1: Site/Soil Selection & Land Preparation (Soil testing, pH correction, liming)
   Stage 2: Variety Selection & Sowing / Nursery Management (Breeder/Foundation seed, seedling hardening)
   Stage 3: Vegetative Husbandry (4R Nutrient stewardship, IPNM, irrigation scheduling, training/pruning)
   Stage 4: Reproductive / Canopy Protection (AESA scouting, pollination management, pest monitoring)
   Stage 5: Harvesting & Maturity Indexing (Early morning harvest, shade curing)
   Stage 6: Post-Harvest & Cold Chain (Pre-cooling, CFB sorting, ZECC/Cold store, digital marketing)

3. VALUE CHAIN & AGRIBUSINESS QUESTIONS:
   Order by Linear Flow:
   Input Supply -> Production -> Aggregation/Collection -> Processing/Grading -> Packaging/Storage -> Reefer Logistics -> Mandi Wholesale -> Retail/Consumer.

4. INSTITUTIONAL & GOVERNANCE QUESTIONS:
   Order by Federal Hierarchy & Coordination:
   Federal (MoALD / NARC / SQCC / PQPMC / DFTQC) -> Provincial (MoALD / AKC / Provincial Labs) -> Local (Palika Agriculture Section / Ward Extension) -> Farmers / Cooperatives / Private Sector.

CRITICAL RULE 2: POLICY / PLAN / PUBLICATION EMBEDDED AT THE SIDE OF EACH STAGE
Inside every subgraph or node, you MUST explicitly state the responsible Nepalese Policy, Act, or Institution:
- Constitution of Nepal (Article 36: Food Sovereignty; Article 51: State Policies)
- Food Hygiene and Quality Act, 2081 (खाद्य स्वच्छता तथा गुणस्तर ऐन, २०८१) [Traceability, SPS, Hygiene standards]
- Seeds Act 2045 (Amended 2079), Seeds Rules 2069, National Seed Vision (2013-2025)
- Pesticides Management Act 2076 & Plant Protection Act 2064 (Quarantine, Import permit, Banned list)
- Agriculture Development Strategy (ADS 2015-2035) [Governance, Productivity, Commercialization, Competitiveness]
- 16th Periodic Plan (2081/82 - 2085/86) [Structural transformation, cold-chain grid, commercial hubs]
- Subsidized Chemical Fertilizer Management Directives & Insurance Premium Subsidy Procedures
- 7th National Agricultural Census 2078 Data (4.13M holdings, 2.21M ha operated area, 0.55 ha avg holding)

CRITICAL RULE 3: DESCRIPTIVE MULTI-LINE NODE CAPSULES (NO ONE-WORD LABELS)
Every node must contain:
- Operational Title (Bold)
- Exact Technical Parameter (dosages, temperatures, thresholds, percentages, moisture levels)
- Implementing Agent & Quantified Impact
- Relevant Nepal Policy / Legal Article

CRITICAL RULE 4: VISUAL COLOR STYLING IN MERMAID
Apply distinct, professional fills for each stage to ensure high readability:
- Preventative / Cultural / Input stages: Light Green fills (`fill:#dcfce7,stroke:#16a34a`)
- Mechanical / Processing stages: Soft Blue fills (`fill:#e0f2fe,stroke:#0284c7`)
- Biological / Monitoring stages: Soft Amber/Yellow fills (`fill:#fef3c7,stroke:#d97706`)
- Chemical / Loss / Warning stages: Light Pink/Red fills (`fill:#fee2e2,stroke:#dc2626`)
- Final Output / Consumer stages: Emerald/Teal fills (`fill:#ccfbf1,stroke:#0d9488`)

10-MARK ANSWER ARCHITECTURE:
1. Technical Introduction with National Agricultural Census 2078 / MoALD Baseline Data
2. Primary Categorical & Ordered Mermaid Diagram (Multi-line descriptive capsules + Embedded Policies)
3. 45-Second Exam Hand-Drawn Blueprint (Clean ASCII multi-line box sketch for answer sheets)
4. Structured Technical & Policy Matrix
5. High-Yield Action Interventions (Technical terminology: GAP, SPS, IPNM, RBPR, AESA, Cold Chain Grid)
6. Strategic Conclusion (Linking Constitution Art 36/51 & 16th Periodic Plan)
"""

def get_working_groq_model(client: Groq) -> str:
    """Detects and selects the highest-performance available active model."""
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

def extract_mermaid_code(text: str) -> str:
    """Safely extracts the first mermaid code block."""
    pattern = r"```(?:mermaid|Mermaid)\s*([\s\S]*?)\s*```"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""

def generate_highres_image_url(mermaid_code: str) -> str:
    """Generates direct URL for full-screen view at scale=3 on a pure white canvas."""
    encoded = base64.b64encode(mermaid_code.encode("utf-8")).decode("ascii")
    return f"https://mermaid.ink/img/{encoded}?bgColor=white&scale=3"

# ---------------------------------------------------------
# Top Header Banner
# ---------------------------------------------------------
st.markdown("""
<div class="hero-banner">
    <h1>🌾 Loksewa Agri Officer: Master Visual & Policy Engine</h1>
    <p>Categorical & Chronological Diagrams • Direct Policy Integration • Full-Screen View • Internal Vault</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Main Tabs: Generator vs In-System Saved Vault
# ---------------------------------------------------------
tab_generator, tab_vault = st.tabs(["✍️ Answer & Visual Generator", "📚 In-System Revision Vault"])

# =========================================================
# TAB 1: GENERATOR
# =========================================================
with tab_generator:
    user_query = st.text_area(
        "Enter Loksewa Question / Syllabus Topic (10 Marks):",
        placeholder="Type any syllabus topic (e.g., Value Chain of Tomato, Citrus Decline Management, Seed Quality Certification, Law of Diminishing Returns, Post-Harvest Loss Reduction)...",
        height=110
    )

    if st.button("Generate Categorical Visual Answer", type="primary", use_container_width=True):
        if not api_key:
            st.error("⚠️ GROQ_API_KEY is not configured. Please add it to your Streamlit Cloud Settings -> Secrets.")
        elif not user_query.strip():
            st.warning("⚠️ Please enter a question or topic first.")
        else:
            client = Groq(api_key=api_key)
            active_model = get_working_groq_model(client)
            
            full_prompt = f"""
            Provide a complete, top-tier Loksewa Gazetted 3rd Class Agriculture Officer answer for:
            QUESTION: {user_query}
            WEIGHTAGE: 10 Marks
            
            MANDATORY COMPLIANCE:
            - The Mermaid diagram and ASCII blueprint MUST be strictly CATEGORICAL and CHRONOLOGICALLY ORDERED (e.g., Progress of sowing, IPM safety hierarchy, value chain sequence, or governance tier).
            - Every node must be a DESCRIPTIVE MINI-CARD containing technical standards, field agents, measurable impacts, and exact Nepal policies/Acts.
            - Include the 45-second ASCII blueprint for exam paper drawing, technical-policy matrix, and crisp action points.
            """
            
            with st.spinner(f"Engine ({active_model}) organizing categorical stages & linking Nepal policies..."):
                try:
                    completion = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": full_prompt}
                        ],
                        model=active_model,
                        temperature=0.2,
                        max_tokens=4096
                    )
                    
                    answer_text = completion.choices[0].message.content
                    mermaid_code = extract_mermaid_code(answer_text)
                    
                    st.session_state["current_question"] = user_query
                    st.session_state["current_answer"] = answer_text
                    st.session_state["current_mermaid"] = mermaid_code
                    st.session_state["current_img_url"] = generate_highres_image_url(mermaid_code) if mermaid_code else ""
                    
                except Exception as err:
                    st.error(f"Error communicating with Groq API: {str(err)}")

    # Result Section
    if "current_answer" in st.session_state:
        st.markdown("---")
        
        # Action Bar: Full Screen & Save to System
        col_act1, col_act2 = st.columns([1, 1])
        with col_act1:
            if st.session_state["current_img_url"]:
                st.markdown(
                    f'<a href="{st.session_state["current_img_url"]}" target="_blank" class="open-window-btn">'
                    f'🔍 Open Picture in Full Screen (New Window) ↗</a>',
                    unsafe_allow_html=True
                )
        with col_act2:
            if st.button("💾 Save to Revision Vault (Inside System)", use_container_width=True):
                save_to_vault(
                    st.session_state["current_question"],
                    st.session_state["current_answer"],
                    st.session_state["current_mermaid"],
                    st.session_state["current_img_url"]
                )
                st.success("✅ Successfully saved to your In-System Vault! You can review it anytime in the 'In-System Revision Vault' tab without downloading.")

        # Diagram Render Block
        if st.session_state["current_mermaid"]:
            st.markdown('<div class="diagram-card">', unsafe_allow_html=True)
            st.markdown("### 🖼️ Categorical & Chronological Visual Architecture")
            st.markdown(f"```mermaid\n{st.session_state['current_mermaid']}\n```")
            st.caption("Categorically structured with embedded technical standards and responsible policy frameworks.")
            st.markdown('</div>', unsafe_allow_html=True)

        # Full 10-Mark Answer Sheet
        st.markdown("### 📝 Complete 10-Mark Loksewa Examination Sheet")
        st.markdown(st.session_state["current_answer"])

# =========================================================
# TAB 2: IN-SYSTEM REVISION VAULT (Saved On Server)
# =========================================================
with tab_vault:
    st.subheader("📚 In-System Revision Vault")
    st.caption("All answers and diagrams saved here remain on the system server. No files are downloaded to your personal computer.")
    
    saved_items = get_all_vault_items()
    
    if not saved_items:
        st.info("Your vault is currently empty. Generate an answer in Tab 1 and click '💾 Save to Revision Vault'.")
    else:
        for item in saved_items:
            item_id, item_time, item_q, item_ans, item_mmd, item_url = item
            
            with st.expander(f"📌 {item_q} (Saved: {item_time})", expanded=False):
                col_v1, col_v2 = st.columns([3, 1])
                with col_v1:
                    if item_url:
                        st.markdown(
                            f'<a href="{item_url}" target="_blank" class="open-window-btn">'
                            f'🔍 Open Picture in Full Screen (New Window) ↗</a>',
                            unsafe_allow_html=True
                        )
                with col_v2:
                    if st.button("🗑️ Delete from Vault", key=f"del_{item_id}", use_container_width=True):
                        delete_vault_item(item_id)
                        st.rerun()

                if item_mmd:
                    st.markdown('<div class="diagram-card">', unsafe_allow_html=True)
                    st.markdown(f"```mermaid\n{item_mmd}\n```")
                    st.markdown('</div>', unsafe_allow_html=True)

                st.markdown(item_ans)
