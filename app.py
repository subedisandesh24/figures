import streamlit as st
from groq import Groq
import re
import base64
import requests
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

# Custom High-Contrast, Distinguished Card Styling
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
    
    /* Visual Frame Cards */
    .fig-frame {
        background: #ffffff;
        border: 2px solid #cbd5e1;
        border-radius: 14px;
        padding: 20px;
        margin: 20px 0;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.05);
    }
    .fig-title {
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

    /* Monospace Blueprint Box */
    .blueprint-box {
        background-color: #f8fafc;
        border: 1.5px dashed #0284c7;
        border-radius: 10px;
        padding: 16px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.88rem;
        line-height: 1.5;
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
# Fail-Safe Context-Adaptive System Prompt
# ---------------------------------------------------------
DYNAMIC_CONTEXT_SYSTEM_PROMPT = """
You are the Chief Examination Answer Architect and Senior Agriculture Specialist for the Nepal Public Service Commission (Gazetted 3rd Class Agriculture Officer).

ABSOLUTE MANDATE: ZERO PRESET OR RECYCLED BOILERPLATE!
Every question must be analyzed contextually. NEVER force-fit unrelated laws. Adapt dynamically to the specific discipline.

1. CONTEXTUAL POLICY CITATION (SUBSTANCE ONLY):
Cite ONLY the specific acts, standards, or guidelines governing that domain and state WHAT the policy actually mandates (e.g., Food Hygiene & Quality Act 2081 Sec 14 for MRL/traceability, Seeds Act 2045 Sec 16 for Truthful Labeling, Plant Protection Act 2064 for PRA/quarantine, Subsidized Fertilizer Directives for nutrient quotas).

2. STRICT MERMAID RULES (PREVENT ALL PARSER CRASHES):
- NODE IDENTIFIERS MUST START WITH LETTERS: Never use raw numbers as IDs like 1, 2, 3! ALWAYS write N1, N2, N3, or A1, A2, B1.
- MAKE TOPICS BOLD: The very first line inside every node MUST be bold using **Topic Title**.
- ABSOLUTELY NEVER USE <br> OR <br/> TAGS: Write real newlines inside strings.
- Format every node as:
  N1["`**1. Bold Topic Title**
  • Technical Standard: xyz
  • Impact: abc
  • Policy Mandate: exact clause`"]
- NEVER use rounded parenthesis node shapes like N1(...).
- ALWAYS end classDef lines with a semicolon (;).

3. MANDATORY: EXTENSIVE DEPTH IN SWOT & MATRICES (>5 POINTS EACH):
- For SWOT Analysis: You MUST provide MORE THAN 5 POINTS (at least 6-7 distinct, highly technical, substantive points) in EACH of the 4 quadrants:
  * Strengths (6+ points): Concrete Nepali agro-climatic, genetic, or institutional assets.
  * Weaknesses (6+ points): Specific structural, input, yield gap, and infrastructure deficits.
  * Opportunities (6+ points): Commercialization, export, processing, and digital horizons.
  * Threats (6+ points): Climate vulnerabilities, vector outbreaks, market volatility, and SPS import competition.
- For 2x2 Decision Matrix / Comparison Matrix:
  * MUST contain MORE THAN 5 DISTINCT CRITERIA ROWS (at least 6-7 rows comparing Technical Parameters, Field Protocols, Implementing Agencies, Measurable KPIs, Legal Acts, and Risk Mitigations).
- For Primary Mermaid Diagram:
  * MUST contain at least 5-6 sequentially connected nodes with bold headings and theme colors.

CATALOG OF 30 DYNAMIC VISUAL ARCHETYPES:
[Flowchart, Cycle Diagram, Cause–Effect Diagram, Fishbone (Ishikawa), Problem Tree, Solution Tree / Objective Tree, Pyramid Diagram, Venn Diagram, Mind Map, Concept Map, Tree Diagram, Input–Output Model, Value Chain Diagram, SWOT Analysis, 2×2 Matrix, Timeline, Decision Tree, Comparison Matrix, Resource Flow Diagram, Infographic, Bar Graph Blueprint, Line Graph Blueprint, Pie Chart Blueprint, Scatter Plot, Spider/Radar Diagram, Process Diagram, Hierarchy Diagram, Network Diagram, Funnel Diagram, Circular Flow Diagram]

MANDATORY 10-MARK STRUCTURE:
1. EXECUTIVE SNAPSHOT:
   - Precise 2-line technical definition.
   - Commodity/Topic-specific baseline data from Nepal Agricultural Census 2078 or latest MoALD reports.
2. FIGURE 1: PRIMARY CONTEXTUAL MERMAID DIAGRAM:
   - Strict category/chronological order (5-6 nodes).
   - Every node has a BOLD TOPIC on the first line.
   - Zero <br> tags.
   - Node IDs start with letters (N1, N2...).
   - Embedded substantive policy mandates.
3. FIGURE 2: EXTENSIVE SWOT ANALYSIS / 2x2 DECISION MATRIX (MORE THAN 5 POINTS PER CATEGORY):
   - At least 6-7 deep, technical bullet points per quadrant/dimension.
4. FIGURE 3: 45-SECOND EXAM HAND-DRAWN BLUEPRINT:
   - Clean ASCII sketch matching the exact topic for immediate answer-sheet reproduction.
5. FIGURE 4: COMPREHENSIVE POLICY & TECHNICAL MATRIX:
   - Structured table connecting figure nodes to exact technical parameters and what the relevant law specifically mandates (6+ rows).
"""

# ---------------------------------------------------------
# Robust Helper Functions & Auto-Sanitizer
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
    """
    Bulletproof Mermaid Sanitizer:
    1. Eradicates all <br> tags
    2. Replaces broken classDef definitions with verified, semicolon-terminated classes
    3. Converts digit-starting node IDs (1, 2) to (N1, N2) without look-behind errors
    4. Formats nodes as Markdown strings ["`**Title**\n• ...`"]
    """
    if not code:
        return ""
    
    # 1. Total eradication of <br> tags
    code = re.sub(r'(?:<br\s*/?>|&lt;br\s*/?&gt;)', '\n', code, flags=re.IGNORECASE)
    code = re.sub(r'</?(?:b|strong)>', '**', code, flags=re.IGNORECASE)
    code = re.sub(r'<[^>]+>', '', code)
    
    # 2. Normalize quotes and superscripts
    code = code.replace("‘", "'").replace("’", "'").replace('“', "'").replace('”', "'")
    superscripts = {"⁰":"0", "¹":"1", "²":"2", "³":"3", "⁴":"4", "⁵":"5", "⁶":"6", "⁷":"7", "⁸":"8", "⁹":"9", "⁻":"-", "⁺":"+"}
    for k, v in superscripts.items():
        code = code.replace(k, v)
    code = code.replace("ha-1", "/ha").replace("kg-1", "/kg")
    
    lines = [l.strip() for l in code.split("\n") if l.strip()]
    if not lines:
        return ""
    
    # Ensure declaration
    first_line = lines[0].lower()
    if not (first_line.startswith("flowchart") or first_line.startswith("graph")):
        lines.insert(0, "flowchart TD")
        
    cleaned_lines = []
    
    # Remove any broken classDef lines from model
    core_lines = [l for l in lines if not l.startswith("classDef")]
    
    # Inject guaranteed clean color definitions with terminating semicolons
    cleaned_lines.append(core_lines[0])
    cleaned_lines.append("    classDef cGreen fill:#ecfdf5,stroke:#059669,stroke-width:2px,color:#065f46;")
    cleaned_lines.append("    classDef cBlue fill:#eff6ff,stroke:#2563eb,stroke-width:2px,color:#1e40af;")
    cleaned_lines.append("    classDef cAmber fill:#fffbeb,stroke:#d97706,stroke-width:2px,color:#92400e;")
    cleaned_lines.append("    classDef cRed fill:#fef2f2,stroke:#dc2626,stroke-width:2px,color:#991b1b;")
    cleaned_lines.append("    classDef cPurple fill:#faf5ff,stroke:#9333ea,stroke-width:2px,color:#6b21a8;")
    
    for line in core_lines[1:]:
        stripped = line.strip()
        if any(stripped.startswith(p) for p in ["flowchart", "graph", "subgraph", "end", "style", "class ", "%%"]):
            cleaned_lines.append(line)
            continue
        
        # FIX 1: Prefix numeric IDs (e.g. 1[...], 1 --> 2) with 'N' using standard capturing group (NO LOOK-BEHIND)
        line = re.sub(
            r'(^|[\s;,(\[{])(\d+[A-Za-z0-9_]*)(?=\s*(?:\[|\(|:::|-->|---|==>|-\.->|--\w+-->|;|\n|$))',
            r'\1N\2',
            line
        )
        
        # FIX 2: Format nodes into clean Markdown strings ["`...`"]
        def format_markdown_node(match):
            node_id = match.group(1)
            raw_text = match.group(2).strip()
            
            # Clean outer quotes/backticks
            if raw_text.startswith('`') and raw_text.endswith('`'):
                raw_text = raw_text[1:-1].strip()
            if (raw_text.startswith('"') and raw_text.endswith('"')) or (raw_text.startswith("'") and raw_text.endswith("'")):
                raw_text = raw_text[1:-1].strip()
                
            raw_text = raw_text.replace('"', "'")
            raw_text = re.sub(r'(?:<br\s*/?>|&lt;br\s*/?&gt;)', '\n', raw_text, flags=re.IGNORECASE)
            return f'{node_id}["`{raw_text}`"]'

        line = re.sub(r'\b([A-Za-z0-9_]+)\((.*?)\)(?=\s*(?:-->|---|==>|-\.->|--\w+-->|;|\n|:::|$))', format_markdown_node, line)
        line = re.sub(r'\b([A-Za-z0-9_]+)\[(?!`)(.*?)\](?=\s*(?:-->|---|==>|-\.->|--\w+-->|;|\n|:::|$))', format_markdown_node, line)
        
        cleaned_lines.append(line)
        
    final_mermaid = "\n".join(cleaned_lines)
    final_mermaid = re.sub(r'(?:<br\s*/?>|&lt;br\s*/?&gt;)', '\n', final_mermaid, flags=re.IGNORECASE)
    return final_mermaid

def sanitize_markdown_text(text: str) -> str:
    """Removes stray <br> tags from the answer sheet text."""
    if not text:
        return ""
    return re.sub(r'(?:<br\s*/?>|&lt;br\s*/?&gt;)', '\n', text, flags=re.IGNORECASE)

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
    <p>Zero-Error Mermaid Architecture • >5 Points per Matrix/SWOT • Bold Topics • In-System Vault</p>
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
            1. FIGURE 1 (PRIMARY MERMAID): 5-6 sequentially connected nodes with bold titles, attractive colors, and NO <br> tags. Node IDs must start with letters (N1, N2...).
            2. FIGURE 2 (SWOT / 2x2 DECISION MATRIX): You MUST provide MORE THAN 5 POINTS (at least 6-7 distinct, substantive points) in each quadrant/dimension!
            3. FIGURE 3 (ASCII BLUEPRINT): Clean 45-second drawing for exam answer sheet.
            4. FIGURE 4 (POLICY & TECHNICAL MATRIX): Table with at least 6-7 rows specifying exact technical standards and substantive legal mandates.
            5. CONTEXTUAL POLICY CITATION: Cite ONLY the acts and guidelines that legally apply to this specific subject matter and state what they mandate.
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
                    raw_mermaid = extract_mermaid_code(clean_answer)
                    clean_mermaid = sanitize_mermaid_code(raw_mermaid)
                    
                    st.session_state["current_question"] = user_query
                    st.session_state["current_answer"] = clean_answer
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
            if st.session_state.get("current_img_url"):
                st.markdown(
                    f'<a href="{st.session_state["current_img_url"]}" target="_blank" class="open-window-btn">'
                    f'🔍 Open Figure 1 in Full Screen (New Window) ↗</a>',
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

        # Diagram Render Block (High-Res Image with Native Fallback)
        if st.session_state.get("current_mermaid"):
            st.markdown('<div class="fig-frame">', unsafe_allow_html=True)
            st.markdown('<div class="fig-title">🎨 Figure 1: Primary Sequential Architecture (Bold Titles & Theme Colors)</div>', unsafe_allow_html=True)
            
            mermaid_code = st.session_state["current_mermaid"]
            img_url = st.session_state.get("current_img_url", "")
            
            # Primary: Server-side rendered high-resolution PNG image
            rendered_via_image = False
            if img_url:
                try:
                    res = requests.get(img_url, timeout=7)
                    if res.status_code == 200 and len(res.content) > 800:
                        st.image(res.content, use_container_width=True, caption="Figure 1: Primary Sequential Flow (High-Res Vector Canvas)")
                        rendered_via_image = True
                except Exception:
                    rendered_via_image = False
            
            # Secondary Fail-Safe: Native Markdown Mermaid
            if not rendered_via_image:
                st.markdown(f"```mermaid\n{mermaid_code}\n```")
                
            st.caption("Bold topic headings, attractive color coding, zero HTML tags, with substantive legal mandates embedded.")
            st.markdown('</div>', unsafe_allow_html=True)

        # Full Visual-Dominant Exam Sheet Display
        st.markdown("### 📋 Complete 10-Mark Contextual Answer Sheet")
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
                    st.markdown('<div class="fig-frame">', unsafe_allow_html=True)
                    rendered_vault_img = False
                    if item_url:
                        try:
                            v_res = requests.get(item_url, timeout=5)
                            if v_res.status_code == 200 and len(v_res.content) > 800:
                                st.image(v_res.content, use_container_width=True)
                                rendered_vault_img = True
                        except Exception:
                            rendered_vault_img = False
                    if not rendered_vault_img:
                        st.markdown(f"```mermaid\n{item_mmd}\n```")
                    st.markdown('</div>', unsafe_allow_html=True)

                st.markdown(item_ans)
