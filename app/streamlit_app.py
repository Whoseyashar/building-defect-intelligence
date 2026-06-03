
import streamlit as st
import sqlite3
import json
import os
from openai import OpenAI
import fitz

st.set_page_config(
    page_title="Building Defect Intelligence | SECO",
    page_icon="🏗️",
    layout="wide"
)

st.markdown("""
<style>
.severity-CRITICAL { background:#dc3545; color:white; padding:3px 10px; border-radius:4px; font-weight:bold; font-size:12px; }
.severity-HIGH     { background:#e67e22; color:white; padding:3px 10px; border-radius:4px; font-weight:bold; font-size:12px; }
.severity-MEDIUM   { background:#f39c12; color:white; padding:3px 10px; border-radius:4px; font-weight:bold; font-size:12px; }
.severity-LOW      { background:#27ae60; color:white; padding:3px 10px; border-radius:4px; font-weight:bold; font-size:12px; }
.summary-box { background:#f0f4ff; border-left:4px solid #1e3c72; padding:16px; border-radius:4px; margin:12px 0; }
</style>
""", unsafe_allow_html=True)

DB_PATH = "data/building_intelligence.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

def badge(severity):
    s = severity.upper()
    return f'<span class="severity-{s}">{s}</span>'

def analyze_with_ai(text):
    api_key = os.environ.get("OPENAI_API_KEY","")
    if not api_key:
        st.error("OPENAI_API_KEY not set.")
        return None
    client = OpenAI(api_key=api_key)
    prompt = f"""You are a senior building inspector at SECO Group.
Analyze this inspection report and return ONLY valid JSON:
{{
  "building_name": "name of building",
  "location": "address or Unknown",
  "inspector": "name or Unknown",
  "date": "date or Unknown",
  "overall_risk": "CRITICAL or HIGH or MEDIUM or LOW",
  "defects": [
    {{
      "severity": "CRITICAL or HIGH or MEDIUM or LOW",
      "title": "defect title",
      "description": "what was found",
      "recommendation": "action to take",
      "urgency": "Immediate or Within 7 days or Within 30 days or Next maintenance cycle"
    }}
  ],
  "executive_summary": "2-3 sentence summary for a non-technical manager"
}}
REPORT:
{text[:3000]}"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role":"user","content":prompt}],
        temperature=0
    )
    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json","").replace("```","").strip()
    return json.loads(raw)

def save_to_db(result):
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO reports (filename, source_type, location, inspector, date, num_pages, num_chunks, full_text) VALUES (?,?,?,?,?,?,?,?)",
        (result.get("building_name","Unknown"), "user_upload",
         result.get("location",""), result.get("inspector",""),
         result.get("date",""), 1, 1, ""))
    report_id = cursor.lastrowid
    for d in result.get("defects",[]):
        cursor.execute(
            "INSERT INTO defects (report_id, severity, title, description, recommendation, urgency) VALUES (?,?,?,?,?,?)",
            (report_id, d.get("severity","LOW"), d.get("title",""),
             d.get("description",""), d.get("recommendation",""), d.get("urgency","")))
    conn.commit()
    conn.close()

st.sidebar.title("🏗️ Building Defect Intelligence")
st.sidebar.caption("SECO Group — AI-powered inspection analysis")
st.sidebar.divider()
page = st.sidebar.radio("Navigation", ["Dashboard", "Analyze Report", "Defect Database", "About"])

if page == "Dashboard":
    st.title("Building Defect Intelligence Dashboard")
    st.caption("Real-time overview of all inspected buildings and detected defects")
    conn = get_conn()
    total_reports  = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    total_defects  = conn.execute("SELECT COUNT(*) FROM defects").fetchone()[0]
    critical_count = conn.execute("SELECT COUNT(*) FROM defects WHERE severity='CRITICAL'").fetchone()[0]
    high_count     = conn.execute("SELECT COUNT(*) FROM defects WHERE severity='HIGH'").fetchone()[0]
    conn.close()
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Reports Analyzed", total_reports)
    c2.metric("Total Defects", total_defects)
    c3.metric("Critical", critical_count)
    c4.metric("High Risk", high_count)
    st.divider()
    conn = get_conn()
    recent_defects = conn.execute("""
        SELECT d.severity, d.title, d.description, d.recommendation, r.filename, r.location
        FROM defects d JOIN reports r ON d.report_id=r.id
        ORDER BY CASE d.severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END
        LIMIT 20
    """).fetchall()
    conn.close()
    st.subheader("All Defects — sorted by severity")
    for severity, title, description, recommendation, filename, location in recent_defects:
        with st.expander(f"{title} — {filename}"):
            st.markdown(badge(severity), unsafe_allow_html=True)
            st.write(f"**Location:** {location or 'N/A'}")
            st.write(f"**Found:** {description}")
            if recommendation:
                st.write(f"**Recommendation:** {recommendation}")

elif page == "Analyze Report":
    st.title("Analyze Inspection Report")
    st.write("Upload a PDF or paste text to get an instant AI-powered defect analysis.")
    tab1, tab2 = st.tabs(["Upload PDF", "Paste Text"])
    with tab1:
        uploaded = st.file_uploader("Upload inspection report (PDF)", type="pdf")
        if uploaded:
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded.read())
                tmp_path = tmp.name
            doc = fitz.open(tmp_path)
            text = "".join(p.get_text() for p in doc)
            doc.close()
            st.success(f"Extracted {len(text):,} characters from PDF")
            if st.button("Analyze with AI", key="btn_pdf"):
                with st.spinner("AI is reading the report..."):
                    result = analyze_with_ai(text)
                if result:
                    st.session_state["result"] = result
    with tab2:
        pasted = st.text_area("Paste report text here", height=250)
        if st.button("Analyze with AI", key="btn_text") and pasted.strip():
            with st.spinner("AI is reading the report..."):
                result = analyze_with_ai(pasted)
            if result:
                st.session_state["result"] = result
    if "result" in st.session_state:
        result = st.session_state["result"]
        st.divider()
        col1, col2 = st.columns([2,1])
        with col1:
            st.subheader(result.get("building_name","Unknown Building"))
            st.write(f"**Location:** {result.get('location','N/A')}")
            st.write(f"**Inspector:** {result.get('inspector','N/A')}")
            st.write(f"**Date:** {result.get('date','N/A')}")
        with col2:
            risk = result.get("overall_risk","LOW")
            st.markdown("**Overall Risk**")
            st.markdown(badge(risk), unsafe_allow_html=True)
        st.markdown(f'<div class="summary-box">📋 <b>Executive Summary</b><br><br>{result.get("executive_summary","")}</div>', unsafe_allow_html=True)
        st.subheader(f"Defects Found: {len(result.get('defects',[]))}")
        for i, defect in enumerate(result.get("defects",[]), 1):
            with st.expander(f"{i}. {defect['title']}"):
                st.markdown(badge(defect["severity"]), unsafe_allow_html=True)
                st.write(f"**Found:** {defect['description']}")
                st.write(f"**Recommendation:** {defect['recommendation']}")
                st.write(f"**Urgency:** {defect['urgency']}")
        if st.button("Save to Database"):
            save_to_db(result)
            st.success("Saved to database!")
            del st.session_state["result"]

elif page == "Defect Database":
    st.title("Defect Database")
    col1, col2 = st.columns(2)
    with col1:
        severity_filter = st.selectbox("Filter by severity", ["ALL","CRITICAL","HIGH","MEDIUM","LOW"])
    with col2:
        search = st.text_input("Search defects", placeholder="e.g. crack, water, fire...")
    conn = get_conn()
    rows = conn.execute("""
        SELECT d.severity, d.title, d.description, d.recommendation,
               d.urgency, r.filename, r.location
        FROM defects d JOIN reports r ON d.report_id=r.id
        ORDER BY CASE d.severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END
    """).fetchall()
    conn.close()
    filtered = [r for r in rows if
                (severity_filter == "ALL" or r[0] == severity_filter) and
                (not search or search.lower() in (r[1]+r[2]).lower())]
    st.write(f"Showing {len(filtered)} defects")
    for severity, title, description, recommendation, urgency, filename, location in filtered:
        with st.expander(f"[{severity}] {title} — {filename}"):
            st.markdown(badge(severity), unsafe_allow_html=True)
            st.write(f"**Location:** {location or 'N/A'}")
            st.write(f"**Description:** {description}")
            if recommendation:
                st.write(f"**Recommendation:** {recommendation}")
            if urgency:
                st.write(f"**Urgency:** {urgency}")

elif page == "About":
    st.title("About This Product")
    st.markdown("""
## Building Defect Intelligence
Built for **SECO Group** as part of the AI & Data Engineer technical assessment.

### Problem
Building inspectors process dozens of PDF reports weekly. Defects are buried in unstructured prose,
severity is implied rather than structured, and there is no connection to similar past cases.

### Solution
This tool automatically extracts defects from any PDF inspection report, scores severity,
generates recommendations, and produces an executive summary — turning a 2-hour manual
task into a 5-minute workflow.

### Tech Stack
- **PDF parsing**: PyMuPDF
- **AI extraction**: OpenAI GPT-4o-mini
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **Vector search**: ChromaDB
- **Database**: SQLite
- **UI**: Streamlit
    """)
