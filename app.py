import streamlit as st
from groq import Groq
import re
import base64
import requests
import os

# ---------------------------------------------------------
# Page Configuration (Clean, full-width, no sidebar clutter)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Loksewa Agri Officer Engine",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for crisp, readable typography and visual cards
st.markdown("""
<style>
    .block-container { padding-top: 1.8rem; padding-bottom: 3rem; }
    .figure-frame {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 18px;
        background-color: #ffffff;
        margin-bottom: 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }
    .figure-label {
        font-weight: 700;
        font-size: 1.05rem;
        color: #1b5e20;
        margin-bottom: 10px;
        display: inline-block;
    }
    .policy-tag {
        background-color: #e8f5e9;
        color: #2e7d32;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.85rem;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# API Key & Model Configuration (Automatic - No Sidebar)
# ---------------------------------------------------------
api_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
ACTIVE_MODEL = "llama-3.3-70b-versatile"

# ---------------------------------------------------------
# Master System Prompt: Descriptive Diagrams & Policies
# ---------------------------------------------------------
SYSTEM_PROMPT = """
You are a senior Nepalese Agriculture Officer, Loksewa answer evaluator, policy specialist, and visual answer architect.
Your mission is to produce a HIGH-SCORING, 10-MARK answer for the Nepal Public Service Commission (Gazetted 3rd Class Agriculture Officer) examination.

CRITICAL MANDATE - DESCRIPTIVE DIAGRAMS (NO ONE-WORD LABELS):
- Evaluators award marks based on the technical substance shown directly inside the diagrams.
- NEVER use generic, single-word or two-word labels (NEVER write: A[Harvest] --> B[Transport] --> C[Market]).
- EVERY box/node in the diagram (both Mermaid and ASCII) MUST be a multi-line descriptive technical card containing:
    1. Operational Title (Bold)
    2. Concrete Technical Action & Standards (e.g., harvesting at 75-80% maturity, pre-cooling to 10-12°C, 4R fertilizer timing, seed purity >98%)
    3. Operational Agent & Measurable Impact (e.g., Palika Agriculture Section, transit loss drops from 30% to <8%)
    4. Exact Nepal Policy / Act / Legal Clause (e.g., [Act: Food Hygiene & Quality Act 2081, Sec. 12], [Policy: ADS Commercialization Pillar])

DYNAMIC VISUAL TAXONOMY (Dynamically select the 2 most logical models):
[Flowchart, Cycle Diagram, Cause–Effect Diagram, Fishbone (Ishikawa), Problem Tree, Solution Tree / Objective Tree, Pyramid Diagram, Venn Diagram, Mind Map, Concept Map, Tree Diagram, Input–Output Model, Value Chain Diagram, SWOT Analysis, 2×2 Matrix, Timeline, Decision Tree, Comparison Matrix, Resource Flow Diagram, Infographic, Bar Graph Blueprint, Line Graph Blueprint, Pie Chart Blueprint, Scatter Plot, Spider/Radar Diagram, Process Diagram, Hierarchy Diagram, Network Diagram, Funnel Diagram, Circular Flow Diagram]

MANDATORY 10-MARK ANSWER STRUCTURE:
1. Concise Introduction with Key Nepal Agricultural Census 2078 Data (4.13M holdings, 2.21M ha operated land, 0.55 ha avg holding size).
2. Primary Descriptive Mermaid Diagram:
   - Valid Mermaid code inside ```mermaid ... ```.
   - Use line breaks (<br/>) inside quoted strings for multi-line descriptive cards.
   - Every node MUST cite the relevant Act, Policy, or Guidelines.
3. 45-Second Exam Hand-Drawn Blueprint:
   - A clean ASCII box diagram that candidates can draw with pen/pencil in 45 seconds on their answer sheet.
   - Nodes must include technical standards and policy citations.
4. Comprehensive Technical & Policy Matrix:
   - Tabular comparison connecting problem nodes, technical standards, indicators, and responsible legal acts.
5. High-Impact Action Interventions:
   - Bulleted technical actions using precise terminology (GAP, SPS measures, IPNM, RBPR, AESA, cold-chain grid, farm-to-fork traceability).
6. Conclusion:
   - Strategic summary linking the Constitution of Nepal (Art 36 & 51) and the 16th Periodic Plan.

POLICY REPOSITORY:
- Constitution of Nepal (Art 36: Food Sovereignty, Art 51)
- Food Hygiene and Quality Act 2081 (खाद्य स्वच्छता तथा गुणस्तर ऐन, २०८१)
- 16th Periodic Plan (2081/82 - 2085/86)
- Agriculture Development Strategy (ADS 2015-2035)
- Seeds Act 2045 (Amended 2079) & National Seed Vision
- Pesticides Management Act 2076 & Plant Protection Act 2064
- PMAMP, Subsidized Chemical Fertilizer Procedures, Agricultural Insurance Subsidies
- 7th National Agricultural Census 2078 Data
"""

# ---------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------
def extract_mermaid_code(text: str) -> str:
    """Extracts the first valid mermaid block from response text."""
    pattern = r"```(?:mermaid|Mermaid)\s*([\s\S]*?)\s*```"
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    return ""

def fetch_highres_diagram_png(mermaid_code: str):
    """
    Downloads high-resolution PNG from mermaid.ink.
    Uses scale=2 and pure white background for clear readability.
    """
    try:
        encoded = base64.b64encode(mermaid_code.encode("utf-8")).decode("ascii")
        url = f"https://mermaid.ink/img/{encoded}?bgColor=white&scale=2"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.content
        return None
    except Exception:
        return None

# ---------------------------------------------------------
# User Interface (Direct, Full-Screen)
# ---------------------------------------------------------
st.title("🌾 Loksewa Agriculture Officer Examination Engine")
st.markdown("Generates **10-Mark Loksewa Answers** featuring **descriptive, policy-embedded visual cards**, 45-second exam blueprints, and **high-res PNG downloads**.")

sample_topics = [
    "Select or type an exam question...",
    "Analyze the structural bottlenecks in the vegetable value chain leading to high consumer prices and low farm-gate prices. Formulate an integrated post-harvest & marketing strategy linking the Food Hygiene and Quality Act 2081. (10 Marks)",
    "Explain the epidemiology and integrated management of Citrus Greening (Huanglongbing) disease in Nepal. Highlight institutional quarantine mechanisms. (10 Marks)",
    "Discuss the declining soil fertility in mid-hills of Nepal. Design an Integrated Plant Nutrient Management (IPNM) framework referencing recent government subsidy and soil policies. (10 Marks)",
    "Examine the challenges in achieving seed self-sufficiency in Nepal. Detail the varietal release, certification, and seed replacement procedures under current acts. (10 Marks)"
]

selected_sample = st.selectbox("Quick-Load Sample Question:", sample_topics, index=0)
default_query = "" if selected_sample == sample_topics[0] else selected_sample

user_query = st.text_area(
    "Enter Question / Syllabus Topic (10 Marks):",
    value=default_query,
    placeholder="Type any topic from Paper I or Paper II (Extension, Economics, Soil, Agronomy, Horticulture, Plant Protection)...",
    height=100
)

col_run, _ = st.columns([1, 4])
with col_run:
    submit_btn = st.button("Generate Answer & Visuals", type="primary", use_container_width=True)

# ---------------------------------------------------------
# Execution & Rendering Pipeline
# ---------------------------------------------------------
if submit_btn:
    if not api_key:
        st.error("⚠️ GROQ_API_KEY is not set. Please add it to your Streamlit Community Cloud Settings -> Secrets.")
    elif not user_query.strip():
        st.warning("⚠️ Please enter an exam question or topic.")
    else:
        client = Groq(api_key=api_key)
        
        full_prompt = f"""
        Provide a complete, top-tier Loksewa Gazetted 3rd Class Agriculture Officer answer for:
        QUESTION: {user_query}
        WEIGHTAGE: 10 Marks
        
        MANDATORY REQUIREMENTS:
        - The diagram nodes must be DESCRIPTIVE MINI-CARDS (not one-word labels).
        - Every node must explicitly state: Operational Title, Technical Standard, Field Implementer, Impact, and Nepal Policy/Act.
        - Dynamically select the best visual models from the 30-model taxonomy.
        - Provide the 45-second ASCII exam blueprint, technical-policy matrix, and concise action points.
        """
        
        with st.spinner("Analyzing question, generating descriptive diagram cards, and linking verified policies..."):
            try:
                completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": full_prompt}
                    ],
                    model=ACTIVE_MODEL,
                    temperature=0.2,
                    max_tokens=4096
                )
                
                answer_content = completion.choices[0].message.content
                mermaid_code = extract_mermaid_code(answer_content)
                
                # -----------------------------------------------------
                # Section A: Descriptive Visual & PNG Download Center
                # -----------------------------------------------------
                if mermaid_code:
                    st.markdown('<div class="figure-frame"><span class="figure-label">🖼️ Descriptive Visual Model (Policy & Standard Embedded)</span>', unsafe_allow_html=True)
                    
                    png_bytes = fetch_highres_diagram_png(mermaid_code)
                    
                    if png_bytes:
                        c_img, c_btn = st.columns([3, 1])
                        with c_img:
                            st.image(
                                png_bytes,
                                caption="Descriptive Technical Diagram (High-Res 2x Scale, Pure White Canvas)",
                                use_container_width=True
                            )
                        with c_btn:
                            st.write("#### 📥 Download Diagram")
                            st.download_button(
                                label="Download Image (PNG)",
                                data=png_bytes,
                                file_name="loksewa_descriptive_diagram.png",
                                mime="image/png",
                                use_container_width=True
                            )
                            st.download_button(
                                label="Download Code (.mmd)",
                                data=mermaid_code,
                                file_name="diagram.mmd",
                                mime="text/plain",
                                use_container_width=True
                            )
                            st.caption("✅ High-contrast diagram with multi-line operational descriptions.")
                    else:
                        st.markdown(f"```mermaid\n{mermaid_code}\n```")
                        st.download_button(
                            label="Download Code (.mmd)",
                            data=mermaid_code,
                            file_name="diagram.mmd",
                            mime="text/plain"
                        )
                    st.markdown('</div>', unsafe_allow_html=True)

                # -----------------------------------------------------
                # Section B: Full Loksewa Answer Sheet
                # -----------------------------------------------------
                st.markdown("### 📝 Complete 10-Mark Loksewa Examination Sheet")
                st.markdown(answer_content)
                
                # -----------------------------------------------------
                # Section C: Download Full Answer Sheet
                # -----------------------------------------------------
                st.markdown("---")
                st.download_button(
                    label="📥 Download Full Exam Answer (Markdown)",
                    data=answer_content,
                    file_name="loksewa_agri_officer_answer_10_marks.md",
                    mime="text/markdown"
                )

            except Exception as err:
                st.error(f"Error communicating with Groq API: {str(err)}")
