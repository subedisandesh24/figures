import streamlit as st
from groq import Groq
import re
import base64
import requests
import os
import sqlite3
from datetime import datetime

# ---------------------------------------------------------
# Page Setup: Clean & High-Contrast Visual Interface
# ---------------------------------------------------------
st.set_page_config(
    page_title="Loksewa Agri Visual Master Engine",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom High-Contrast Dashboard Styling
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
# Fully Dynamic Context-Adaptive System Prompt
# ---------------------------------------------------------
DYNAMIC_CONTEXT_SYSTEM_PROMPT = """
You are the Chief Examination Answer Architect and Senior Agriculture Specialist for the Nepal Public Service Commission (Gazetted 3rd Class Agriculture Officer).

ABSOLUTE MANDATE: ZERO PRESET OR RECYCLED ANSWERS!
Every question must be analyzed from first principles. NEVER force-fit unrelated laws, generic four-stage pipelines, or repetitive boilerplate. The answer, technical parameters, and policy citations must be 100% contextual to the exact topic asked.

1. CONTEXTUAL POLICY & REGULATORY MAPPING (CITE ONLY WHAT ACTUALLY APPLIES):
Dynamically identify and cite ONLY the specific legal, policy, and institutional frameworks that govern the topic:
- If Horticultural Production / Tunnels / Pruning: Cite Fruit Development Decade Guidelines, Nursery Standards, PMAMP Protected Horticulture Subsidy Norms, Plastic Tunnel Support Schemes. (DO NOT cite Seeds Act or Quarantine unless relevant).
- If Soil Health / Fertilizer / IPNM: Cite Subsidized Chemical Fertilizer Management Directives, Agricultural Lime Subsidy Guidelines, Soil Health Card Directives, ADS Soil Target. (DO NOT cite Food Hygiene Act).
- If Plant Protection / Disease / Pesticides: Cite Plant Protection Act 2064, Pesticides Management Act 2076 (Sec. 8 banned list), PQPMC biocontrol protocols, Maximum Residue Limits (MRL).
- If Seed Quality / Varieties: Cite Seeds Act 2045 (Amended 2079, Sec. 16 Truthful Labeling), Seeds Rules 2069, National Seed Vision (2013-2025), SQCC Certification Standards.
- If Agricultural Economics / Farm Management: Cite Law of Diminishing Returns principles, Farm Budgeting standards, Minimum Support Price (MSP) directives, Agriculture Insurance Premium Subsidy Procedures.
- If Extension / ICT / Governance: Cite Local Government Operation Act 2074 (Palika agriculture jurisdiction), Digital Nepal Framework (Agri-component), Intergovernmental Coordination Act 2077.
- If Post-Harvest / Food Safety / Value Chain: Cite Food Hygiene and Quality Act 2081 (Sec. 14 Traceability), SPS regulations, 16th Periodic Plan cold-chain corridors.

ALWAYS STATE WHAT THE POLICY ACTUALLY MANDATES:
Never just name the law. Explicitly write its specific section, quantitative ceiling, subsidy rate, or technical requirement in the context of the question.

2. DYNAMIC VISUAL ARCHITECTURE (THE DIAGRAM IS THE ANSWER):
Choose the visual type from the 30-archetype catalog that represents the intrinsic logic of the topic:
- Production/Agronomy: Chronological phenological flow (Land prep -> Seed/Nursery -> Husbandry -> Harvest -> Storage).
- Plant Protection: IPM hierarchy (Host resistance -> Cultural -> Mechanical -> Biological -> Biorational -> Chemical).
- Economics: Production Curves (TP, AP, MP stages), 2x2 Resource Optimization Matrix, Value Chain margin breakdown.
- Pathology: Disease Triangle, Inoculum cycle, Surveillance-Forecasting loop.
- Seed Tech: Generation Multiplication Chain (Breeder -> Foundation -> Certified 1 & 2 -> Improved).
- Governance: Multi-Tier Jurisdiction Matrix (Federal policy -> Provincial research/labs -> Local extension).

STRICT MERMAID SYNTAX RULES (ZERO PARSER ERRORS):
1. ABSOLUTELY NEVER USE HTML TAGS (<br>, <b>, <i>, <span>). Use \\n for line breaks inside double-quoted strings.
2. ALWAYS format nodes strictly as: NodeID["Title\\n- Technical Standard\\n- Operational Agent\\n- Contextual Policy Provision"].
3. NEVER use rounded parenthesis node shapes like NodeID(...) because nested parentheses crash the parser.
4. Color-code nodes contextually (Green for sustainable/inputs, Blue for tech/logistics, Amber for thresholds/monitoring, Red for pests/losses, Purple for governance).

CATALOG OF 30 DYNAMIC VISUAL ARCHETYPES:
[Flowchart, Cycle Diagram, Cause–Effect Diagram, Fishbone (Ishikawa), Problem Tree, Solution Tree / Objective Tree, Pyramid Diagram, Venn Diagram, Mind Map, Concept Map, Tree Diagram, Input–Output Model, Value Chain Diagram, SWOT Analysis, 2×2 Matrix, Timeline, Decision Tree, Comparison Matrix, Resource Flow Diagram, Infographic, Bar Graph Blueprint, Line Graph Blueprint, Pie Chart Blueprint, Scatter Plot, Spider/Radar Diagram, Process Diagram, Hierarchy Diagram, Network Diagram, Funnel Diagram, Circular Flow Diagram]

MANDATORY 10-MARK STRUCTURE:
1. EXECUTIVE SNAPSHOT:
   - Precise 2-line technical definition.
   - Commodity/Topic-specific baseline data from Nepal Agricultural Census 2078 or latest MoALD reports.
2. PRIMARY CONTEXTUAL MERMAID DIAGRAM:
   - High-density, multi-line descriptive cards (separated by \\n) with embedded contextual policy mandates.
3. SECONDARY ANALYTICAL VISUAL:
   - Subject-specific 2x2 Matrix, SWOT, Decision Tree, or Graph Blueprint (labeled X/Y axes and threshold curves).
4. 45-SECOND EXAM HAND-DRAWN BLUEPRINT:
   - Clean ASCII sketch matching the exact topic for immediate answer-sheet reproduction.
5. CONTEXTUAL POLICY & TECHNICAL MATRIX:
   - Structured table connecting figure nodes to exact technical parameters and what the relevant law specifically mandates.
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
    
    # 1. Replace <br> tags with \n
    code = re.sub(r'<br\s*/?>', r'\\n', code, flags=re.IGNORECASE)
    
    # 2. Strip any remaining HTML tags
    code = re.sub(r'<[^>]+>', '', code)
    
    # 3. Replace smart quotes
    code = code.replace("‘", "'").replace("’", "'").replace("“", "'").replace("”", "'")
    
    # 4. Replace unicode superscripts
    superscripts = {"⁰":"0", "¹":"1", "²":"2", "³":"3", "⁴":"4", "⁵":"5", "⁶":"6", "⁷":"7", "⁸":"8", "⁹":"9", "⁻":"-", "⁺":"+"}
    for k, v in superscripts.items():
        code = code.replace(k, v)
    code = code.replace("ha-1", "/ha").replace("kg-1", "/kg")
    
    # 5. Line-by-line syntax fixing
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

def sanitize_markdown_text(text: str) -> str:
    if not text:
        return ""
    return re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)

def generate_highres_image_url(mermaid_code: str) -> str:
    encoded = base64.b64encode(mermaid_code.encode("utf-8")).decode("ascii")
    return f"https://mermaid.ink/img/{encoded}?bgColor=white&scale=3"

# ---------------------------------------------------------
# Top Header Banner
# ---------------------------------------------------------
st.markdown("""
<div class="hero-banner">
    <h1>🌱 Loksewa Agri Officer: Master Visual Engine</h1>
    <p>Context-Adaptive Visuals • Domain-Specific Nepal Policies • Clean Mermaid (No &lt;br&gt;) • In-System Vault</p>
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
        placeholder="Type any specific syllabus question (e.g., Training and Pruning Systems in Deciduous Fruit Trees; Biological Nitrogen Fixation Mechanism and Biofertilizer Policies; Law of Diminishing Marginal Returns in Input Allocation)...",
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
            
            STRICT EXECUTION DIRECTIVES:
            1. NO PRESET OR RECYCLED BOILERPLATE: Identify the exact discipline and tailor all standards, indicators, and baseline data specifically to this topic.
            2. CONTEXTUAL POLICY CITATION: Cite ONLY the acts, guidelines, and targets that legally apply to this specific subject matter. Detail WHAT the policy prescribes.
            3. ZERO <br> TAGS: Use \\n for line breaks inside Mermaid node strings.
            4. DYNAMIC DIAGRAM LOGIC: Pick the model from your 30-archetype taxonomy that reflects the true technical mechanics of this topic.
            5. Provide Primary Mermaid Diagram, Secondary Analytical Visual, 45-second ASCII Exam Blueprint, and Policy Matrix.
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
            st.markdown('<div class="diagram-title">🎨 Context-Specific Visual Model (Technical Mechanics & Relevant Laws)</div>', unsafe_allow_html=True)
            
            # Fetch high-res PNG for rendering without browser font glitches
            try:
                img_data = requests.get(st.session_state["current_img_url"], timeout=10)
                if img_data.status_code == 200:
                    st.image(img_data.content, use_container_width=True)
                else:
                    st.markdown(f"```mermaid\n{st.session_state['current_mermaid']}\n```")
            except Exception:
                st.markdown(f"```mermaid\n{st.session_state['current_mermaid']}\n```")
                
            st.caption("Dynamically constructed based on the technical mechanics of the question with context-specific legal mandates.")
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

                if item_url:
                    st.markdown('<div class="diagram-frame">', unsafe_allow_html=True)
                    try:
                        img_data = requests.get(item_url, timeout=8)
                        if img_data.status_code == 200:
                            st.image(img_data.content, use_container_width=True)
                        elif item_mmd:
                            st.markdown(f"```mermaid\n{item_mmd}\n```")
                    except Exception:
                        if item_mmd:
                            st.markdown(f"```mermaid\n{item_mmd}\n```")
                    st.markdown('</div>', unsafe_allow_html=True)

                st.markdown(item_ans)
