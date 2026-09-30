import streamlit as st
from groq import Groq
import re
import base64
import requests

# Page setup optimized for diagram clarity
st.set_page_config(
    page_title="Loksewa Agri Officer: Descriptive Visual Answer Engine",
    page_icon="🌾",
    layout="wide"
)

# ---------------------------------------------------------
# Sidebar Controls
# ---------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Engine Control")
    api_key = st.secrets.get("GROQ_API_KEY", None)
    if not api_key:
        api_key = st.text_input("Enter Groq API Key:", type="password")

    selected_model = st.selectbox(
        "Groq Model Engine:",
        ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
        index=0
    )
    
    st.markdown("---")
    st.markdown("### 📊 Descriptive Visual Taxonomy")
    st.caption(
        "Flowchart, Cycle, Cause–Effect, Fishbone (Ishikawa), Problem Tree, "
        "Solution Tree, Pyramid, Venn, Mind Map, Concept Map, Tree, Input–Output, "
        "Value Chain, SWOT, 2×2 Matrix, Timeline, Decision Tree, Comparison Matrix, "
        "Resource Flow, Infographic, Bar/Line/Pie/Scatter Blueprints, Spider/Radar, "
        "Process, Hierarchy, Network, Funnel, Circular Flow."
    )
    st.markdown("---")
    st.markdown("### 📜 Core Policy Anchors")
    st.caption(
        "• Constitution of Nepal (Art 36: Food Sovereignty, Art 51: State Policies)\n"
        "• Food Hygiene & Quality Act 2081 (खाद्य स्वच्छता तथा गुणस्तर ऐन २०८१)\n"
        "• 16th Periodic Plan (2081/82 - 2085/86)\n"
        "• Agriculture Development Strategy (ADS 2015-2035)\n"
        "• Seeds Act 2045 (Amended 2079) & National Seed Vision\n"
        "• Pesticides Management Act 2076 & Plant Protection Act 2064\n"
        "• National Agricultural Census 2078 Data"
    )

# ---------------------------------------------------------
# Descriptive Master System Prompt
# ---------------------------------------------------------
DESCRIPTIVE_SYSTEM_PROMPT = """
You are a senior Nepalese Agriculture Officer, Loksewa answer evaluator, policy analyst, and technical answer-writing specialist.
Your task is to write an EXAM-WINNING, 10-MARK answer for the Nepal Public Service Commission (Gazetted 3rd Class Agriculture Officer) examination.

CRITICAL RULE: DESCRIPTIVE NODES IN DIAGRAMS (NO ONE-WORD LABELS)
- Evaluators award marks when the diagram itself demonstrates complete technical depth.
- NEVER use generic, single-word or two-word labels (e.g., NEVER write `A[Harvesting] --> B[Transport] --> C[Market]`).
- EVERY node/box inside the diagrams (both Mermaid and ASCII) MUST be a multi-line descriptive capsule containing:
    1. Operational Title (Bold)
    2. Concrete Technical Action & Standard (e.g., harvesting at 75-80% maturity, pre-cooling at 10-12°C, 4R fertilizer timing, seed purity >98%)
    3. Operational Agent / Quantitative Impact (e.g., Palika Agri Section, loss reduction from 30% to <10%)
    4. Exact Nepal Policy / Legal Clause (e.g., [Act: Food Hygiene & Quality Act 2081, Sec. 12], [Policy: ADS Productivity Pillar])

VISUAL TAXONOMY INVENTORY (Select 2-3 Dynamically):
[Flowchart, Cycle Diagram, Cause–Effect Diagram, Fishbone (Ishikawa), Problem Tree, Solution Tree / Objective Tree, Pyramid Diagram, Venn Diagram, Mind Map, Concept Map, Tree Diagram, Input–Output Model, Value Chain Diagram, SWOT Analysis, 2×2 Matrix, Timeline, Decision Tree, Comparison Matrix, Resource Flow Diagram, Infographic, Bar Graph, Line Graph, Pie Chart, Scatter Plot, Spider/Radar Diagram, Process Diagram, Hierarchy Diagram, Network Diagram, Funnel Diagram, Circular Flow Diagram]

DYNAMIC EXECUTION ARCHITECTURE (10-MARK LOKSEWA WEIGHTAGE):
1. QUESTION DIAGNOSTICS & DYNAMIC MODEL SELECTION:
   - Identify the command word (Analyze, Evaluate, Compare, Formulate, Suggest).
   - Select the 2 most powerful visual models from the taxonomy above that match the problem logic.

2. PRIMARY DESCRIPTIVE MERMAID DIAGRAM:
   - Output valid Mermaid syntax enclosed in ```mermaid ... ```.
   - Use descriptive text with line breaks (`<br/>`) inside quotes.
   - Ensure syntax safety: Avoid unescaped double quotes inside node strings; use single quotes if needed.

3. EXAM-HALL HAND-DRAWN DESCRIPTIVE BLUEPRINT:
   - An ASCII box-diagram format that candidates can sketch in 45-60 seconds on their paper.
   - Must also contain descriptive operational details and policy codes inside the text boxes.

4. COMPREHENSIVE TECHNICAL & POLICY MATRIX:
   - A structured table comparing problems, technical solutions, field indicators, and responsible legal acts.

5. HIGH-DENSITY ACTION POINTS:
   - Bulleted technical interventions using exact terminology (IPNM, GAP, SPS measures, RBPR, AESA, Cold-chain grid, Farm-to-Fork traceability).

6. LATEST AUTHENTIC NEPAL DATA:
   - Ground points in verified statistics: National Agricultural Census 2078 (4.13M holdings, 2.21M ha operated area, 0.55 ha avg holding size), 16th Periodic Plan growth and commercialization targets.
"""

# ---------------------------------------------------------
# Helper Functions: Extract Mermaid & Fetch High-Res PNG
# ---------------------------------------------------------
def extract_mermaid_code(text: str) -> str:
    """Extracts the first mermaid code block safely."""
    pattern = r"```(?:mermaid|Mermaid)\s*([\s\S]*?)\s*```"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""

def get_mermaid_image_bytes(mermaid_code: str) -> bytes:
    """
    Encodes Mermaid code and downloads high-resolution PNG from mermaid.ink.
    Uses scale=2 and pure white background for crisp, legible text.
    """
    try:
        # Base64 encode the diagram definition
        encoded = base64.b64encode(mermaid_code.encode("utf-8")).decode("ascii")
        url = f"https://mermaid.ink/img/{encoded}?bgColor=white&scale=2"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.content
        return None
    except Exception:
        return None

# ---------------------------------------------------------
# Main UI Interface
# ---------------------------------------------------------
st.title("🌾 Loksewa Agri Officer: Descriptive Visual Answer Engine")
st.markdown(
    "Produces high-scoring **10-Mark Loksewa Answers** where every diagram node is a "
    "**descriptive technical capsule** integrated with Nepal policies, acts, and field parameters."
)

sample_questions = [
    "Select or type an exam question...",
    "Analyze the structural bottlenecks in the vegetable value chain leading to high consumer prices and low farm-gate prices. Formulate an integrated post-harvest & marketing strategy linking prevailing policies. (10 Marks)",
    "Explain the epidemiology and integrated management of Citrus Greening (Huanglongbing) disease in Nepal. Highlight institutional quarantine mechanisms. (10 Marks)",
    "Discuss the declining soil fertility in mid-hills of Nepal. Design an Integrated Plant Nutrient Management (IPNM) framework referencing recent government subsidy and soil policies. (10 Marks)",
    "Examine the challenges in achieving seed self-sufficiency in Nepal. Detail the varietal release, certification, and seed replacement procedures under current acts. (10 Marks)"
]

selected_sample = st.selectbox("Quick-Load Sample Question:", sample_questions, index=0)

default_text = "" if selected_sample == sample_questions[0] else selected_sample
user_question = st.text_area(
    "Enter Question / Syllabus Topic (10 Marks):",
    value=default_text,
    placeholder="e.g., Formulate an Integrated Pest Management (IPM) strategy for Fall Armyworm (Spodoptera frugiperda) in maize under the Pesticides Management Act 2076... (10 Marks)",
    height=90
)

col_run, _ = st.columns([1, 4])
with col_run:
    generate_btn = st.button("Generate Descriptive Visual Answer", type="primary", use_container_width=True)

# ---------------------------------------------------------
# Execution & Rendering Pipeline
# ---------------------------------------------------------
if generate_btn:
    if not api_key:
        st.error("⚠️ Please enter your Groq API Key in the sidebar or setup secrets.toml.")
    elif not user_question.strip():
        st.warning("⚠️ Please provide an exam question or topic.")
    else:
        client = Groq(api_key=api_key)
        
        full_query = f"""
        Provide a complete, top-tier Loksewa Gazetted 3rd Class Agriculture Officer examination answer for:
        QUESTION: {user_question}
        WEIGHTAGE: 10 Marks
        
        CRITICAL EXECUTION MANDATE:
        - The Mermaid diagram and ASCII blueprint must have DESCRIPTIVE NODES (not single words).
        - Each node must explain the technical standard, field operator, measurable impact, and exact Nepal policy/Act clause.
        - Dynamically select the best models from your 30-model inventory.
        - Provide the 45-second exam hand-drawn blueprint, technical-policy matrix, and crisp action points.
        """
        
        with st.spinner("Analyzing question, building descriptive visual capsules, and linking verified policies..."):
            try:
                response = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": DESCRIPTIVE_SYSTEM_PROMPT},
                        {"role": "user", "content": full_query}
                    ],
                    model=selected_model,
                    temperature=0.2,
                    max_tokens=4096
                )
                
                output_text = response.choices[0].message.content
                mermaid_code = extract_mermaid_code(output_text)
                
                # ---------------------------------------------------------
                # Section A: Descriptive Visual & Image Download Card
                # ---------------------------------------------------------
                if mermaid_code:
                    st.subheader("🖼️ Descriptive Diagram & Visual Architecture")
                    
                    img_bytes = get_mermaid_image_bytes(mermaid_code)
                    
                    if img_bytes:
                        col_img, col_dl = st.columns([3, 1])
                        with col_img:
                            st.image(
                                img_bytes,
                                caption="Descriptive Technical Diagram (High-Res 2x Scale, Pure White Canvas)",
                                use_column_width=True
                            )
                        with col_dl:
                            st.write("### 📥 Save Visual")
                            st.download_button(
                                label="Download Diagram (PNG)",
                                data=img_bytes,
                                file_name="descriptive_agri_diagram.png",
                                mime="image/png",
                                use_container_width=True
                            )
                            st.download_button(
                                label="Download Raw Code (.mmd)",
                                data=mermaid_code,
                                file_name="diagram.mmd",
                                mime="text/plain",
                                use_container_width=True
                            )
                            st.success("✅ **Readable Card Layout**: Every node contains standards, impacts, and legal clauses.")
                    else:
                        st.markdown(f"```mermaid\n{mermaid_code}\n```")
                        st.download_button(
                            label="Download Raw Mermaid Code (.mmd)",
                            data=mermaid_code,
                            file_name="diagram.mmd",
                            mime="text/plain"
                        )
                    st.markdown("---")

                # ---------------------------------------------------------
                # Section B: Full Examination Sheet
                # ---------------------------------------------------------
                st.subheader("📝 Complete 10-Mark Loksewa Examination Sheet")
                st.markdown(output_text)
                
                # ---------------------------------------------------------
                # Section C: Download Complete Answer Sheet
                # ---------------------------------------------------------
                st.markdown("---")
                st.download_button(
                    label="📥 Download Complete Exam Answer Sheet (Markdown)",
                    data=output_text,
                    file_name="loksewa_exam_answer_10_marks.md",
                    mime="text/markdown"
                )
                
            except Exception as e:
                st.error(f"Error communicating with Groq API: {str(e)}")
