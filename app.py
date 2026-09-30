import streamlit as st
from groq import Groq
import re
import base64
import requests
import os

# Page Configuration - Clean, full-width interface
st.set_page_config(
    page_title="Loksewa Agri Officer Engine",
    page_icon="🌾",
    layout="wide"
)

# Fetch API key directly from secrets or environment (No sidebar inputs)
api_key = st.secrets.get("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", None))

# Master system prompt enforcing descriptive, card-style diagrams with embedded policies
SYSTEM_PROMPT = """
You are an expert Nepalese Agriculture Officer, Loksewa answer evaluator, policy analyst, and examination answer-writing specialist.
Your mission is to produce a HIGH-SCORING, 10-MARK answer specifically tailored for the Nepal Public Service Commission (Gazetted 3rd Class Agriculture Officer) examination.

CRITICAL MANDATE - DESCRIPTIVE DIAGRAMS (NO ONE-WORD LABELS):
- Evaluators award marks based on the technical substance within diagrams.
- NEVER use generic, single-word or two-word labels (NEVER write: A[Harvest] --> B[Transport] --> C[Market]).
- EVERY box/node in the diagram (both Mermaid and ASCII) MUST be a multi-line descriptive technical card containing:
    1. Operational Title (Bold)
    2. Concrete Technical Action & Standards (e.g., harvesting at 75-80% maturity, pre-cooling to 10-12°C, 4R stewardship, moisture < 12%)
    3. Operational Agent & Measurable Impact (e.g., Palika Agriculture Section, transit loss drops from 30% to <8%)
    4. Exact Nepal Policy / Act / Legal Clause (e.g., [Act: Food Hygiene & Quality Act 2081, Sec. 12], [Policy: ADS Commercialization Pillar])

DYNAMIC VISUAL TAXONOMY (Dynamically pick the 2 most logical models):
[Flowchart, Cycle Diagram, Cause–Effect Diagram, Fishbone (Ishikawa), Problem Tree, Solution Tree / Objective Tree, Pyramid Diagram, Venn Diagram, Mind Map, Concept Map, Tree Diagram, Input–Output Model, Value Chain Diagram, SWOT Analysis, 2×2 Matrix, Timeline, Decision Tree, Comparison Matrix, Resource Flow Diagram, Infographic, Bar Graph Blueprint, Line Graph Blueprint, Pie Chart Blueprint, Scatter Plot, Spider/Radar Diagram, Process Diagram, Hierarchy Diagram, Network Diagram, Funnel Diagram, Circular Flow Diagram]

ANSWER STRUCTURE FOR 10 MARKS:
1. Concise Introduction with Key Nepal Agricultural Census 2078 Data
2. Primary Descriptive Mermaid Diagram (with policies inside the nodes)
3. 45-Second Exam Hand-Drawn Blueprint (Descriptive ASCII box diagram for paper answer sheet)
4. Comprehensive Technical & Policy Matrix
5. High-Impact Action Interventions (Technical terminology: GAP, SPS, IPNM, RBPR, AESA, cold grid)
6. Conclusion

LEGAL & POLICY REPOSITORY:
- Constitution of Nepal (Art 36: Food Sovereignty, Art 51)
- Food Hygiene and Quality Act 2081 (खाद्य स्वच्छता तथा गुणस्तर ऐन, २०८१)
- 16th Periodic Plan (2081/82 - 2085/86)
- Agriculture Development Strategy (ADS 2015-2035)
- Seeds Act 2045 (Amended 2079) & National Seed Vision
- Pesticides Management Act 2076 & Plant Protection Act 2064
- 7th National Agricultural Census 2078 data (4.13M holdings, 2.21M ha, 0.55 ha avg holding size)
"""

def extract_mermaid(text: str) -> str:
    """Safely extracts the first mermaid code block."""
    pattern = r"```(?:mermaid|Mermaid)\s*([\s\S]*?)\s*```"
    match = re.search(pattern, text)
    if match:
        return match.group(1).strip()
    return ""

def fetch_highres_diagram_png(mermaid_code: str):
    """Fetches a high-resolution, readable PNG from mermaid.ink (scale 2, white background)."""
    try:
        encoded = base64.b64encode(mermaid_code.encode("utf-8")).decode("ascii")
        url = f"https://mermaid.ink/img/{encoded}?bgColor=white&scale=2"
        res = requests.get(url, timeout=15)
        if res.status_code == 200:
            return res.content
        return None
    except Exception:
        return None

# --- Main App Interface (No Sidebar) ---
st.title("🌾 Loksewa Agriculture Officer Examination Engine")
st.caption("10-Mark Answer Architect | Descriptive Policy-Embedded Visuals | Exam Hall Blueprints")

# Input Box
user_query = st.text_area(
    "Enter Loksewa Question / Syllabus Topic:",
    placeholder="e.g., Analyze the persistent challenges of post-harvest loss in perishable vegetables in Nepal. Formulate an integrated supply chain strategy linking the Food Hygiene and Quality Act 2081 and prevailing periodic plans. (10 Marks)",
    height=110
)

col_btn, _ = st.columns([1, 4])
with col_btn:
    submit_btn = st.button("Generate Answer & Visuals", type="primary", use_container_width=True)

# Processing
if submit_btn:
    if not api_key:
        st.error("⚠️ GROQ_API_KEY is not set. Please add it to your Streamlit App Settings -> Secrets.")
    elif not user_query.strip():
        st.warning("⚠️ Please enter a question or topic.")
    else:
        client = Groq(api_key=api_key)
        
        prompt_payload = f"""
        Provide a complete, top-tier Loksewa Gazetted 3rd Class Agriculture Officer answer for:
        QUESTION: {user_query}
        WEIGHTAGE: 10 Marks
        
        Ensure:
        - The diagram nodes are DESCRIPTIVE MINI-CARDS (not simple keywords).
        - Every node explicitly specifies standards, operators, impacts, and Nepal Acts/Policies.
        - Include the 45-second ASCII blueprint for exam paper drawing.
        """
        
        with st.spinner("Analyzing question, building descriptive visual capsules, and linking verified policies..."):
            try:
                # Uses Groq Llama 3.3 70B directly
                completion = client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt_payload}
                    ],
                    model="llama-3.3-70b-versatile",
                    temperature=0.2,
                    max_tokens=4096
                )
                
                answer_content = completion.choices[0].message.content
                mermaid_code = extract_mermaid(answer_content)
                
                # --- Diagram & Download Section ---
                if mermaid_code:
                    st.markdown("### 🖼️ Descriptive Visual Model")
                    png_bytes = fetch_highres_diagram_png(mermaid_code)
                    
                    if png_bytes:
                        c_img, c_btn = st.columns([3, 1])
                        with c_img:
                            st.image(
                                png_bytes,
                                caption="Descriptive Policy & Technical Model (High-Res 2x Scale)",
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
                                label="Download Mermaid Code (.mmd)",
                                data=mermaid_code,
                                file_name="diagram.mmd",
                                mime="text/plain",
                                use_container_width=True
                            )
                            st.info("💡 **Exam Hall Tip:** Replicate the 45-second ASCII blueprint (below) directly on your answer sheet.")
                    else:
                        st.markdown(f"```mermaid\n{mermaid_code}\n```")
                    st.markdown("---")

                # --- Complete Loksewa Answer Display ---
                st.markdown("### 📝 Complete 10-Mark Loksewa Answer Sheet")
                st.markdown(answer_content)
                
                st.markdown("---")
                st.download_button(
                    label="📥 Download Full Exam Answer (Markdown)",
                    data=answer_content,
                    file_name="loksewa_10_marks_answer.md",
                    mime="text/markdown"
                )

            except Exception as err:
                st.error(f"Error communicating with Groq: {str(err)}")
