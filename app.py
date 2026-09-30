import streamlit as st
from groq import Groq
import re
import base64
import requests
import os
import sqlite3
from datetime import datetime

# ---------------------------------------------------------
# Page Setup: Eye-Catchy, Clean Visual Dashboard
# ---------------------------------------------------------
st.set_page_config(
    page_title="Loksewa Agri Visual Master Engine",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom High-Contrast, Eye-Catchy Dashboard Styling
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
        padding: 24px 30px;
        color: #ffffff;
        margin-bottom: 24px;
        box-shadow: 0 8px 20px rgba(6, 78, 59, 0.25);
    }
    .hero-banner h1 {
        color: #ffffff;
        font-weight: 800;
        font-size: 2.2rem;
        margin-bottom: 6px;
    }
    .hero-banner p {
        color: #a7f3d0;
        font-size: 1.05rem;
        margin: 0;
        font-weight: 500;
    }
    
    /* Visual Frame Card */
    .diagram-frame {
        background: #ffffff;
        border: 2px solid #cbd5e1;
        border-radius: 14px;
        padding: 22px;
        margin: 22px 0;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
    }
    .diagram-title {
        font-weight: 800;
        font-size: 1.15rem;
        color: #065f46;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Full-Screen Button Link */
    .open-window-btn {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: linear-gradient(135deg, #059669 0%, #047857 100%);
        color: #ffffff !important;
        padding: 11px 22px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 700;
        font-size: 0.95rem;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 2px 8px rgba(5, 150, 105, 0.35);
    }
    .open-window-btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(5, 150, 105, 0.45);
        color: #ffffff !important;
    }

    /* Quick Exam Blueprint Box */
    .exam-blueprint {
        background-color: #f8fafc;
        border: 1.5px dashed #64748b;
        border-radius: 8px;
        padding: 16px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.88rem;
        line-height: 1.45;
        color: #0f172a;
        overflow-x: auto;
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
        "INSERT INTO visual_vault (timestamp, question, answer, mermaid_code, image_url) VALUES (?, ?, ?, ?, ?)",
        (now, question, answer, mermaid_code, image_url)
    )
    conn.commit()
    conn.close()

def get_all_vault_items():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, timestamp, question, answer, mermaid_code, image_url FROM visual_vault ORDER BY id DESC")
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
# Visual-Dominant Master System Prompt
# ---------------------------------------------------------
VISUAL_MASTER_SYSTEM_PROMPT = """
You are the Chief Examination Answer Architect and Senior Agriculture Specialist for the Nepal Public Service Commission (Gazetted 3rd Class Agriculture Officer).

CORE PHILOSOPHY: THE DIAGRAM IS THE ANSWER!
- Minimize long textual essays. 85% of all technical information, standards, procedures, and legal provisions MUST be presented directly INSIDE THE FIGURES AND DIAGRAMS.
- An evaluator should be able to read ONLY the diagrams and matrices and award full 10 marks without reading long prose.
- Make every visual eye-catching, structured, and color-coded.

CATALOG OF 30 DYNAMIC VISUAL ARCHETYPES:
[Flowchart, Cycle Diagram, Cause–Effect Diagram, Fishbone (Ishikawa), Problem Tree, Solution Tree / Objective Tree, Pyramid Diagram, Venn Diagram, Mind Map, Concept Map, Tree Diagram, Input–Output Model, Value Chain Diagram, SWOT Analysis, 2×2 Matrix, Timeline, Decision Tree, Comparison Matrix, Resource Flow Diagram, Infographic, Bar Graph Blueprint, Line Graph Blueprint, Pie Chart Blueprint, Scatter Plot, Spider/Radar Diagram, Process Diagram, Hierarchy Diagram, Network Diagram, Funnel Diagram, Circular Flow Diagram]

MANDATORY ANSWER STRUCTURE (10 MARKS):
1. EXECUTIVE SNAPSHOT (Short Box):
   - Definition in 2 sentences.
   - Core Baseline Statistics: 7th Agricultural Census 2078 (4.13M holdings, 2.21M ha operated area, 0.55 ha avg holding) or relevant MoALD data.

2. PRIMARY COMPREHENSIVE MERMAID VISUAL (MANDATORY & VALID):
   - Choose the most fitting model from the 30-archetype catalog (e.g., Value Chain, Fishbone, Problem-Solution Tree, Sequential Process, or Safety Hierarchy).
   - STRICT CHRONOLOGICAL OR CATEGORICAL ORDERING:
     * Agronomy/Horticulture: Land Prep -> Sowing/Nursery -> Vegetative/IPNM -> Canopy/AESA -> Harvest -> Cold Chain.
     * Plant Protection: Host Resistance -> Cultural -> Mechanical -> Biological -> Biorational -> Chemical (Last Resort).
     * Value Chain: Input -> Production -> Aggregation -> Processing -> Cold Storage -> Logistics -> Wholesale -> Retail.
     * Governance: Federal -> Provincial -> Local (Palika) -> Cooperatives/Farmers.
   - MULTI-LINE DESCRIPTIVE CARDS: Every node must contain:
     * Operational Title (Bold)
     * Technical Standards (exact dosages, temperatures, moisture %, thresholds)
     * Institutional Implementing Agency
     * Measurable Impact
     * Exact Nepal Act / Policy clause in brackets (e.g., [Act: Food Hygiene & Quality Act 2081, Sec. 12])
   - VIBRANT COLOR CODING: You MUST apply style rules to nodes:
     * Green nodes (Inputs, sustainable practices): style NodeID fill:#dcfce7,stroke:#16a34a,stroke-width:2px
     * Blue nodes (Logistics, technology, processing): style NodeID fill:#e0f2fe,stroke:#0284c7,stroke-width:2px
     * Amber nodes (Thresholds, inspections, monitoring): style NodeID fill:#fef3c7,stroke:#d97706,stroke-width:2px
     * Red/Pink nodes (Hazards, chemical last-resort, loss): style NodeID fill:#fee2e2,stroke:#dc2626,stroke-width:2px
     * Purple nodes (Governance, policies, acts): style NodeID fill:#f3e8ff,stroke:#9333ea,stroke-width:2px

3. SECONDARY ANALYTICAL VISUAL (2x2 Matrix, SWOT, Pyramid, Radar, or Graph Blueprint):
   - Provide a secondary visual model (e.g., a Comparative 2x2 Matrix, a Decision Tree, or a labeled Graph Blueprint with X/Y axes and threshold curves).

4. 45-SECOND EXAM-HALL HAND-DRAWN BLUEPRINT:
   - Provide an ASCII box sketch with clear technical labels and arrows that the candidate can draw with a pen in 45 seconds on their paper.

5. HIGH-DENSITY POLICY & INDICATOR LEDGER:
   - A structured matrix linking each step of the figure to: (1) Technical Standard, (2) Key Performance Indicator, (3) Nepal Legal Act/Policy Clause.

STRICT MERMAID SYNTAX RULES (ZERO ERRORS):
- ALWAYS format node IDs with double quotes: NodeID["<b>Title</b><br/>• Standard: ...<br/>• <i>[Policy: Act Name]</i>"]
- NEVER use rounded parentheses NodeID(...) because nested parens like '(apple rootstock)' crash the Mermaid parser!
- NEVER use curly quotes (' ‘ ’ “ ” ') or unicode superscripts (ha⁻¹ -> write /ha).
"""

# ---------------------------------------------------------
# Dynamic Model Discovery & Sanitization Functions
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

def extract_mermaid_code(text: str) -> str:
    pattern = r"```(?:mermaid|Mermaid)\s*([\s\S]*?)\s*```"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""

def sanitize_mermaid_code(code: str) -> str:
    """Sanitizes Mermaid code to prevent parser crashes."""
    if not code:
        return ""
    code = code.replace("‘", "'").replace("’", "'").replace("“", "'").replace("”", "'")
    superscripts = {"⁰":"0", "¹":"1", "²":"2", "³":"3", "⁴":"4", "⁵":"5", "⁶":"6", "⁷":"7", "⁸":"8", "⁹":"9", "⁻":"-", "⁺":"+"}
    for k, v in superscripts.items():
        code = code.replace(k, v)
    code = code.replace("ha-1", "/ha").replace("kg-1", "/kg")
    
    cleaned_lines = []
    for line in code.split("\n"):
        stripped = line.strip()
        if any(stripped.startswith(p) for p in ["graph ", "flowchart ", "classDef ", "style ", "subgraph ", "end", "%%"]):
            cleaned_lines.append(line)
            continue
        
        # Replace Node(nested (parens)) with Node["nested (parens)"]
        def fix_parens(match):
            node_id = match.group(1)
            content = match.group(2).strip()
            if content.startswith('"') and content.endswith('"'):
                return f'{node_id}[{content}]'
            content = content.replace('"', "'")
            return f'{node_id}["{content}"]'

        line = re.sub(r'\b([A-Za-z0-9_]+)\(([\s\S]*?)\)(?=\s*(?:-->|---|==>|-\.->|--\w+-->|;|\n|$))', fix_parens, line)
        
        # Ensure brackets have quotes: Node[content] -> Node["content"]
        def fix_brackets(match):
            node_id = match.group(1)
            content = match.group(2).strip()
            if content.startswith('"') and content.endswith('"'):
                return f'{node_id}[{content}]'
            content = content.replace('"', "'")
            return f'{node_id}["{content}"]'

        line = re.sub(r'\b([A-Za-z0-9_]+)\[(?!")(.*?)\](?=\s*(?:-->|---|==>|-\.->|--\w+-->|;|\n|$))', fix_brackets, line)
        cleaned_lines.append(line)
        
    return "\n".join(cleaned_lines)

def generate_highres_image_url(mermaid_code: str) -> str:
    """Generates direct URL for full-screen view at scale=3 on a pure white canvas."""
    encoded = base64.b64encode(mermaid_code.encode("utf-8")).decode("ascii")
    return f"https://mermaid.ink/img/{encoded}?bgColor=white&scale=3"

# ---------------------------------------------------------
# Top Header Banner
# ---------------------------------------------------------
st.markdown("""
<div class="hero-banner">
    <h1>🌱 Loksewa Agri Officer: Master Visual Engine</h1>
    <p>30 Dynamic Visual Archetypes • Descriptive Node Capsules • Vibrant Color Coding • Direct Policy Embedded</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Working Tabs
# ---------------------------------------------------------
tab_generator, tab_vault = st.tabs(["📊 Visual Answer Generator", "📚 In-System Revision Vault"])

# =========================================================
# TAB 1: VISUAL ANSWER GENERATOR
# =========================================================
with tab_generator:
    user_query = st.text_area(
        "Enter Loksewa Question / Syllabus Topic (10 Marks):",
        placeholder="Type any syllabus topic (e.g., Value Chain in Agriculture, Law of Diminishing Marginal Returns, Post-Harvest Loss Management, Citrus Decline, Tomato Tunnel Cultivation, Plant Quarantine)...",
        height=110
    )

    if st.button("Generate Visual-First Answer", type="primary", use_container_width=True):
        if not api_key:
            st.error("⚠️ GROQ_API_KEY is not set. Please add it to your Streamlit Cloud Settings -> Secrets.")
        elif not user_query.strip():
            st.warning("⚠️ Please enter a question or topic first.")
        else:
            client = Groq(api_key=api_key)
            active_model = get_working_groq_model(client)
            
            full_prompt = f"""
            Provide a complete, top-tier Loksewa Gazetted 3rd Class Agriculture Officer answer for:
            QUESTION: {user_query}
            WEIGHTAGE: 10 Marks
            
            CRITICAL INSTRUCTION:
            - THE ANSWER MUST BE ENTIRELY READABLE AND DERIVABLE DIRECTLY FROM THE FIGURES!
            - Avoid lengthy text narratives.
            - Provide a Primary Descriptive Mermaid Diagram using vibrant color styling (green, blue, amber, red, purple).
            - Dynamically select the best models from the 30-archetype catalog (Flowchart, Value Chain, Fishbone, Problem Tree, 2x2 Matrix, Hierarchy, etc.).
            - Provide a Secondary Analytical Visual (2x2 Matrix, SWOT, or Graph Blueprint).
            - Provide the 45-second ASCII Exam Blueprint and Policy Ledger.
            """
            
            with st.spinner(f"Designing color-coded visual architecture using engine ({active_model})..."):
                try:
                    completion = client.chat.completions.create(
                        messages=[
                            {"role": "system", "content": VISUAL_MASTER_SYSTEM_PROMPT},
                            {"role": "user", "content": full_prompt}
                        ],
                        model=active_model,
                        temperature=0.2,
                        max_tokens=4096
                    )
                    
                    answer_text = completion.choices[0].message.content
                    raw_mermaid = extract_mermaid_code(answer_text)
                    clean_mermaid = sanitize_mermaid_code(raw_mermaid)
                    
                    st.session_state["current_question"] = user_query
                    st.session_state["current_answer"] = answer_text
                    st.session_state["current_mermaid"] = clean_mermaid
                    st.session_state["current_img_url"] = generate_highres_image_url(clean_mermaid) if clean_mermaid else ""
                    
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
                st.success("✅ Saved to internal vault! You can study it anytime in the 'In-System Revision Vault' tab.")

        # Diagram Render Block
        if st.session_state["current_mermaid"]:
            st.markdown('<div class="diagram-frame">', unsafe_allow_html=True)
            st.markdown('<div class="diagram-title">🎨 Primary Visual Architecture (Complete Answer In-Figure)</div>', unsafe_allow_html=True)
            st.markdown(f"```mermaid\n{st.session_state['current_mermaid']}\n```")
            st.caption("Color-coded by stage: Green (Input/Bio), Blue (Tech/Transit), Amber (Thresholds), Red (Pest/Loss), Purple (Policy/Acts).")
            st.markdown('</div>', unsafe_allow_html=True)

        # Full Visual-Dominant Exam Sheet Display
        st.markdown("### 📋 Complete 10-Mark Visual Answer Sheet")
        st.markdown(st.session_state["current_answer"])

# =========================================================
# TAB 2: IN-SYSTEM REVISION VAULT (Saved On Server)
# =========================================================
with tab_vault:
    st.subheader("📚 In-System Revision Vault")
    st.caption("Saved answers and diagrams remain stored inside the server database. No files are downloaded to your personal computer.")
    
    saved_items = get_all_vault_items()
    
    if not saved_items:
        st.info("Your vault is currently empty. Generate a visual answer in Tab 1 and click '💾 Save to Revision Vault'.")
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
                    st.markdown('<div class="diagram-frame">', unsafe_allow_html=True)
                    st.markdown(f"```mermaid\n{item_mmd}\n```")
                    st.markdown('</div>', unsafe_allow_html=True)

                st.markdown(item_ans)
