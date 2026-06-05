
import streamlit as st
import sqlite3
import json
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from openai import OpenAI
import fitz

st.set_page_config(
    page_title="Building Defect Intelligence | SECO",
    page_icon="🏗️",
    layout="wide"
)

st.markdown("""
<style>
/* Global */
[data-testid="stAppViewContainer"] { background: #f4f6fa; }
[data-testid="stSidebar"] { background: #1e3c72 !important; }
[data-testid="stSidebar"] * { color: white !important; }
[data-testid="stSidebar"] .stRadio label { 
    background: rgba(255,255,255,0.08);
    border-radius: 8px;
    padding: 8px 14px;
    margin: 4px 0;
    display: block;
    transition: background 0.2s;
}
[data-testid="stSidebar"] .stRadio label:hover { background: rgba(255,255,255,0.18); }

/* Severity badges */
.badge-CRITICAL{background:#dc3545;color:white;padding:4px 12px;border-radius:20px;font-weight:700;font-size:11px;letter-spacing:1px;}
.badge-HIGH{background:#e67e22;color:white;padding:4px 12px;border-radius:20px;font-weight:700;font-size:11px;letter-spacing:1px;}
.badge-MEDIUM{background:#f39c12;color:white;padding:4px 12px;border-radius:20px;font-weight:700;font-size:11px;letter-spacing:1px;}
.badge-LOW{background:#27ae60;color:white;padding:4px 12px;border-radius:20px;font-weight:700;font-size:11px;letter-spacing:1px;}

/* KPI cards */
.kpi-card {
    background: white;
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.07);
    border-left: 4px solid #1e3c72;
    margin-bottom: 8px;
}
.kpi-label { font-size: 12px; color: #6c757d; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 4px; }
.kpi-value { font-size: 36px; font-weight: 800; color: #1e3c72; line-height: 1; }
.kpi-card.critical { border-left-color: #dc3545; }
.kpi-card.critical .kpi-value { color: #dc3545; }
.kpi-card.high { border-left-color: #e67e22; }
.kpi-card.high .kpi-value { color: #e67e22; }

/* Summary box */
.summary-box {
    background: linear-gradient(135deg, #f0f4ff 0%, #e8eeff 100%);
    border-left: 4px solid #1e3c72;
    padding: 20px;
    border-radius: 8px;
    margin: 16px 0;
}

/* Page header */
.page-header {
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    color: white;
    padding: 24px 32px;
    border-radius: 12px;
    margin-bottom: 24px;
}
.page-header h1 { color: white; margin: 0; font-size: 28px; }
.page-header p { color: rgba(255,255,255,0.8); margin: 4px 0 0; font-size: 14px; }
</style>
""", unsafe_allow_html=True)

DB_PATH = "data/building_intelligence.db"

def get_conn():
    return sqlite3.connect(DB_PATH)

def badge(severity):
    s = severity.upper()
    return f'<span class="badge-{s}">{s}</span>'

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

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("""
<div style="text-align:center; padding: 24px 0 16px;">
    <svg width="64" height="64" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
      <!-- Building base -->
      <rect x="10" y="24" width="44" height="34" rx="2" fill="rgba(255,255,255,0.15)" stroke="rgba(255,255,255,0.4)" stroke-width="1.5"/>
      <!-- Windows row 1 -->
      <rect x="16" y="30" width="8" height="7" rx="1" fill="rgba(255,255,255,0.6)"/>
      <rect x="28" y="30" width="8" height="7" rx="1" fill="rgba(255,200,100,0.9)"/>
      <rect x="40" y="30" width="8" height="7" rx="1" fill="rgba(255,255,255,0.6)"/>
      <!-- Windows row 2 -->
      <rect x="16" y="42" width="8" height="7" rx="1" fill="rgba(255,200,100,0.9)"/>
      <rect x="28" y="42" width="8" height="7" rx="1" fill="rgba(255,255,255,0.6)"/>
      <rect x="40" y="42" width="8" height="7" rx="1" fill="rgba(255,200,100,0.9)"/>
      <!-- Door -->
      <rect x="26" y="50" width="12" height="8" rx="1" fill="rgba(255,255,255,0.3)"/>
      <!-- Roof -->
      <polygon points="32,6 8,26 56,26" fill="rgba(255,255,255,0.25)" stroke="rgba(255,255,255,0.5)" stroke-width="1.5" stroke-linejoin="round"/>
      <!-- Magnifier overlay -->
      <circle cx="46" cy="18" r="10" fill="rgba(30,60,114,0.85)" stroke="rgba(255,255,255,0.6)" stroke-width="1.5"/>
      <circle cx="46" cy="18" r="6" fill="none" stroke="rgba(255,255,255,0.9)" stroke-width="1.5"/>
      <line x1="50.2" y1="22.2" x2="54" y2="26" stroke="rgba(255,255,255,0.9)" stroke-width="2" stroke-linecap="round"/>
    </svg>
    <div style="font-size:12px; font-weight:300; letter-spacing:3px; opacity:0.65; text-transform:uppercase; margin-top:10px;">SECO Group</div>
    <div style="font-size:20px; font-weight:800; letter-spacing:0.5px; margin-top:2px;">Building Defect</div>
    <div style="font-size:20px; font-weight:800; letter-spacing:0.5px;">Intelligence</div>
    <div style="width:40px; height:2px; background:rgba(255,255,255,0.35); margin:10px auto 0; border-radius:2px;"></div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("""
<style>
div[data-testid="stSidebar"] .stRadio > div {
    display: flex;
    flex-direction: column;
    gap: 4px;
}
div[data-testid="stSidebar"] .stRadio > div > label {
    background: rgba(255,255,255,0.07) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px !important;
    padding: 10px 16px !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    letter-spacing: 0.3px !important;
    transition: all 0.2s !important;
    cursor: pointer !important;
}
div[data-testid="stSidebar"] .stRadio > div > label:hover {
    background: rgba(255,255,255,0.15) !important;
    border-color: rgba(255,255,255,0.3) !important;
}
div[data-testid="stSidebar"] .stRadio > div > label[data-selected="true"] {
    background: rgba(255,255,255,0.2) !important;
    border-color: rgba(255,255,255,0.5) !important;
    font-weight: 700 !important;
}
</style>
""", unsafe_allow_html=True)

page = st.sidebar.radio("", [
    "📊  Dashboard",
    "🔍  Analyze Report", 
    "🗄️  Defect Database",
    "ℹ️  About"
])
page = page.split("  ")[1]

st.sidebar.markdown("""
<hr style="border-color:rgba(255,255,255,0.15); margin:24px 0 12px;">
<div style="font-size:11px; opacity:0.5; text-align:center; line-height:1.8;">
    AI & Data Engineer Assessment<br>June 2026
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "Dashboard":
    st.markdown("""
    <div class="page-header">
        <h1>🏗️ Building Defect Intelligence</h1>
        <p>Real-time overview of all inspected buildings and detected defects — powered by AI</p>
    </div>
    """, unsafe_allow_html=True)

    conn = get_conn()
    total_reports  = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
    total_defects  = conn.execute("SELECT COUNT(*) FROM defects").fetchone()[0]
    critical_count = conn.execute("SELECT COUNT(*) FROM defects WHERE severity='CRITICAL'").fetchone()[0]
    high_count     = conn.execute("SELECT COUNT(*) FROM defects WHERE severity='HIGH'").fetchone()[0]
    severity_data  = conn.execute("""
        SELECT severity, COUNT(*) FROM defects GROUP BY severity
        ORDER BY CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END
    """).fetchall()
    source_data = conn.execute("SELECT source_type, COUNT(*) FROM reports GROUP BY source_type").fetchall()
    recent_defects = conn.execute("""
        SELECT d.severity, d.title, d.description, d.recommendation, r.filename, r.location
        FROM defects d JOIN reports r ON d.report_id=r.id
        ORDER BY CASE d.severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END
        LIMIT 20
    """).fetchall()
    conn.close()

    # KPI Cards
    c1,c2,c3,c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">📁 Reports Analyzed</div>
            <div class="kpi-value">{total_reports}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">⚠️ Total Defects</div>
            <div class="kpi-value">{total_defects}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="kpi-card critical">
            <div class="kpi-label">🔴 Critical</div>
            <div class="kpi-value">{critical_count}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="kpi-card high">
            <div class="kpi-label">🟠 High Risk</div>
            <div class="kpi-value">{high_count}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Defects by Severity")
        if severity_data:
            labels = [r[0] for r in severity_data]
            values = [r[1] for r in severity_data]
            colors_map = {"CRITICAL":"#dc3545","HIGH":"#e67e22","MEDIUM":"#f39c12","LOW":"#27ae60"}
            bar_colors = [colors_map.get(l,"#999") for l in labels]
            fig, ax = plt.subplots(figsize=(5,3.2))
            bars = ax.bar(labels, values, color=bar_colors, edgecolor="white",
                         linewidth=1.5, width=0.55, zorder=3)
            ax.set_ylabel("Number of defects", fontsize=10, color="#6c757d")
            ax.set_facecolor("#f8f9fa")
            fig.patch.set_facecolor("#f8f9fa")
            ax.yaxis.grid(True, color="white", linewidth=1.5, zorder=0)
            ax.set_axisbelow(True)
            for bar, val in zip(bars, values):
                ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.05,
                        str(val), ha="center", va="bottom",
                        fontweight="bold", fontsize=12, color="#333")
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)
            ax.spines["left"].set_visible(False)
            ax.tick_params(colors="#6c757d")
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

    with col2:
        st.markdown("#### Reports by Source Type")
        if source_data:
            labels = [r[0].replace("_"," ").title() for r in source_data]
            values = [r[1] for r in source_data]
            fig, ax = plt.subplots(figsize=(5,3.2))
            wedges, texts, autotexts = ax.pie(
                values, labels=labels, autopct="%1.0f%%",
                colors=["#1e3c72","#4a90d9","#82b4e8"],
                startangle=90,
                wedgeprops={"edgecolor":"white","linewidth":2},
                textprops={"fontsize":11}
            )
            for at in autotexts:
                at.set_fontweight("bold")
                at.set_color("white")
            fig.patch.set_facecolor("#f8f9fa")
            plt.tight_layout()
            st.pyplot(fig)
            plt.close()

    st.markdown("---")
    st.markdown("#### All Defects — sorted by severity")
    severity_icons = {"CRITICAL":"🔴","HIGH":"🟠","MEDIUM":"🟡","LOW":"🟢"}
    for severity, title, description, recommendation, filename, location in recent_defects:
        icon = severity_icons.get(severity, "⚪")
        with st.expander(f"{icon} {title} — {filename}"):
            st.markdown(badge(severity), unsafe_allow_html=True)
            st.markdown(f"**📍 Location:** {location or 'N/A'}")
            st.markdown(f"**🔍 Found:** {description}")
            if recommendation:
                st.markdown(f"**Recommendation:** {recommendation}")

# ══════════════════════════════════════════════════════════════════════════════
# ANALYZE REPORT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Analyze Report":
    st.markdown("""
    <div class="page-header">
        <h1>🔍 Analyze Inspection Report</h1>
        <p>Upload a PDF or paste text to get an instant AI-powered defect analysis</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["📄 Upload PDF", "📝 Paste Text"])
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
            if st.button("🤖 Analyze with AI", key="btn_pdf", type="primary"):
                with st.spinner("AI is reading the report..."):
                    result = analyze_with_ai(text)
                if result:
                    st.session_state["result"] = result
    with tab2:
        st.info("💡 Paste any building inspection report text below to see the AI extract defects instantly.")
        pasted = st.text_area("Paste report text here", height=250,
            placeholder="Paste inspection report content here...")
        if st.button("🤖 Analyze with AI", key="btn_text", type="primary") and pasted.strip():
            with st.spinner("AI is reading the report..."):
                result = analyze_with_ai(pasted)
            if result:
                st.session_state["result"] = result

    if "result" in st.session_state:
        result = st.session_state["result"]
        st.markdown("---")
        col1, col2 = st.columns([2,1])
        with col1:
            st.markdown(f"### 🏢 {result.get('building_name','Unknown Building')}")
            st.markdown(f"📍 **Location:** {result.get('location','N/A')}")
            st.markdown(f"👤 **Inspector:** {result.get('inspector','N/A')}")
            st.markdown(f"📅 **Date:** {result.get('date','N/A')}")
        with col2:
            risk = result.get("overall_risk","LOW")
            st.markdown("**Overall Risk Level**")
            st.markdown(badge(risk), unsafe_allow_html=True)

        st.markdown(
            f'<div class="summary-box">📋 <b>Executive Summary</b><br><br>{result.get("executive_summary","")}</div>',
            unsafe_allow_html=True
        )

        st.markdown(f"### Found {len(result.get('defects',[]))} Defects")
        severity_icons = {"CRITICAL":"🔴","HIGH":"🟠","MEDIUM":"🟡","LOW":"🟢"}
        for i, defect in enumerate(result.get("defects",[]), 1):
            icon = severity_icons.get(defect["severity"],"⚪")
            with st.expander(f"{icon} {i}. {defect['title']}"):
                st.markdown(badge(defect["severity"]), unsafe_allow_html=True)
                st.markdown(f"**🔍 Found:** {defect['description']}")
                st.markdown(f"**Recommendation:** {defect['recommendation']}")
                st.markdown(f"**⏰ Urgency:** {defect['urgency']}")

        col1, col2 = st.columns([1,4])
        with col1:
            if st.button("💾 Save to Database", type="primary"):
                save_to_db(result)
                st.success("Saved to database!")
                del st.session_state["result"]

# ══════════════════════════════════════════════════════════════════════════════
# DEFECT DATABASE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Defect Database":
    st.markdown("""
    <div class="page-header">
        <h1>🗄️ Defect Database</h1>
        <p>All defects extracted from inspected buildings — searchable and filterable</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        severity_filter = st.selectbox("🔍 Filter by severity",
                                        ["ALL","CRITICAL","HIGH","MEDIUM","LOW"])
    with col2:
        search = st.text_input("🔎 Search defects",
                                placeholder="e.g. crack, water, fire, asbestos...")

    conn = get_conn()
    rows = conn.execute("""
        SELECT d.severity, d.title, d.description, d.recommendation,
               d.urgency, r.filename, r.location
        FROM defects d JOIN reports r ON d.report_id=r.id
        ORDER BY CASE d.severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END
    """).fetchall()
    conn.close()

    filtered = [r for r in rows if
                (severity_filter=="ALL" or r[0]==severity_filter) and
                (not search or search.lower() in (r[1]+r[2]).lower())]

    severity_icons = {"CRITICAL":"🔴","HIGH":"🟠","MEDIUM":"🟡","LOW":"🟢"}
    st.markdown(f"**Showing {len(filtered)} defects**")
    for severity, title, description, recommendation, urgency, filename, location in filtered:
        icon = severity_icons.get(severity,"⚪")
        with st.expander(f"{icon} [{severity}] {title} — {filename}"):
            st.markdown(badge(severity), unsafe_allow_html=True)
            st.markdown(f"**📍 Location:** {location or 'N/A'}")
            st.markdown(f"**🔍 Description:** {description}")
            if recommendation:
                st.markdown(f"**Recommendation:** {recommendation}")
            if urgency:
                st.markdown(f"**⏰ Urgency:** {urgency}")

# ══════════════════════════════════════════════════════════════════════════════
# ABOUT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "About":
    st.markdown("""
    <div class="page-header">
        <h1>ℹ️ About This Product</h1>
        <p>Building Defect Intelligence — SECO AI & Data Engineer Assessment</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
### 🎯 Problem
Building inspectors process dozens of PDF reports weekly.
Defects are buried in unstructured prose, severity is implied
rather than structured, and there is no connection to similar
past cases. The result is slow triage and inconsistent assessment.

### 💡 Solution
This tool automatically:
- Extracts text from any PDF inspection report
- Uses AI to identify and classify every defect
- Scores severity: Critical / High / Medium / Low
- Generates actionable recommendations per defect
- Produces executive summaries for non-technical stakeholders
- Stores all findings in a searchable database
- Finds similar past cases using RAG vector search
        """)
    with col2:
        st.markdown("""
### 🛠️ Tech Stack
| Component | Technology |
|-----------|------------|
| PDF parsing | PyMuPDF |
| AI extraction | OpenAI GPT-4o-mini |
| Embeddings | sentence-transformers |
| Vector search | ChromaDB |
| Database | SQLite |
| UI | Streamlit |

### 📊 Data Sources
| Source | Type | Pages |
|--------|------|-------|
| CDC NIOSH Report | Real public | 28 |
| NRC Inspection | Real public | 206 |
| OSHA Safety | Real public | 60 |
| Luxembourg Residential | Synthetic | 1 |
| Luxembourg Industrial | Synthetic | 1 |
        """)
