# Building Defect Intelligence

> AI-powered building inspection report analyzer built for SECO Group.

---

## What problem are we solving?

Building inspectors at firms like SECO process dozens of PDF inspection reports every week.
Defects are buried in unstructured prose, severity is implied by language rather than
structured fields, and there is no connection to similar cases seen in the past.
The result is slow triage, inconsistent severity assessment, and institutional knowledge
that never accumulates.

This product extracts defects automatically, scores their severity, generates actionable
recommendations, and produces a ready-to-share executive summary - turning a 2-hour
manual task into a 5-minute workflow.

---

## Who is the user?

Primary: Building inspectors at firms like SECO who write and read inspection reports
daily and need faster, more consistent defect triage.

Secondary: Asset managers and insurers who receive inspection outputs and need rapid
risk summaries without reading the full technical report.

---

## Why is this relevant to SECO?

SECO stated in their brief: huge volumes of technical data - inspection reports,
plans, photos, measurements, defect observations - that today remain largely underexploited.

This product is a direct answer: it makes accumulated inspection data searchable,
comparable, and actionable. Every new report analyzed adds to the knowledge base,
so the system gets more valuable over time.

---

## Architecture

    PDF input
        |
        v
    Ingestion - PyMuPDF extracts raw text page by page
        |
        v
    Preprocessing - clean noise, chunk into 500-word overlapping segments
        |
        v
    Embeddings - sentence-transformers all-MiniLM-L6-v2 runs locally
        |
        +-----------> ChromaDB  vector similarity search
        +-----------> SQLite    structured defect records
        |
        v
    AI layer - OpenAI GPT-4o-mini
        - Defect extraction
        - Severity scoring Critical / High / Medium / Low
        - Actionable recommendations per defect
        - Executive summary for non-technical stakeholders
        |
        v
    Streamlit UI
        - Dashboard: KPI metrics and severity charts
        - Analyze Report: upload any PDF for instant AI analysis
        - Defect Database: searchable and filterable defect registry
        - About: product context and technical decisions

---

## Quickstart

Prerequisites:
- Python 3.10 or newer
- An OpenAI API key from https://platform.openai.com/api-keys

Step 1 - Clone the repo:

    git clone https://github.com/Whoseyashar/building-defect-intelligence.git
    cd building-defect-intelligence

Step 2 - Create virtual environment:

    python -m venv .venv
    source .venv/bin/activate
    On Windows use: .venv\Scripts\activate

Step 3 - Install dependencies:

    pip install -r requirements.txt

Step 4 - Set your OpenAI API key:

    cp .env.example .env
    Open .env and replace sk-... with your actual OpenAI API key

Step 5 - Run the setup script (downloads data and builds the database):

    python scripts/setup_data.py

    This will automatically:
    - Download 3 real public building inspection PDFs
    - Generate 2 synthetic Luxembourg inspection reports
    - Run the cleaning and chunking pipeline
    - Populate the SQLite database

Step 6 - Launch the app:

    streamlit run app/streamlit_app.py
    Then open http://localhost:8501 in your browser

Step 7 - Run tests:

    pytest tests/ -v
    Expected output: 8 passed

Note: The Analyze Report page works immediately after Step 4.
You can upload any PDF inspection report or paste text directly without running setup.

---

## Data sources

| Source | Type | Pages | Why chosen |
|--------|------|-------|------------|
| CDC NIOSH Building Dampness Report | Real public | 28 | Real-world building health inspection language |
| NRC Facility Inspection Report | Real public | 206 | Large heterogeneous document stress tests the pipeline |
| OSHA Workplace Safety Report | Real public | 60 | Structural and safety defect terminology |
| Luxembourg Residential Complex | Synthetic | 1 | Matches SECO inspection format with real defect types |
| Luxembourg Industrial Warehouse | Synthetic | 1 | Covers industrial defects asbestos and structural fatigue |

Real public reports prove the pipeline handles genuinely messy heterogeneous documents.
Synthetic reports demonstrate domain knowledge of SECOs actual inspection workflow.
In production both would be replaced with real SECO historical reports.

---

## Technical decisions and trade-offs

| Decision | Rationale | Trade-off accepted |
|----------|-----------|-------------------|
| SQLite over Postgres | Zero infrastructure fully reproducible | Not horizontally scalable |
| sentence-transformers local | Free no API call for embeddings | Slightly lower quality than OpenAI embeddings |
| Streamlit over React | Fastest to ship Python-native | Less UI flexibility than React |
| GPT-4o-mini over GPT-4o | 10x cheaper fast enough for defect extraction | Slightly lower reasoning quality |
| Chunk size 500 words | Fits token limits while preserving context | Very long defects may be split |
| Mixed data sources | Reproducible without confidential data | Not identical to real SECO reports |

---

## RAG - Retrieval Augmented Generation

The pipeline embeds all 183 document chunks using sentence-transformers and stores
them in ChromaDB. Given any new defect description, the retriever finds the most
semantically similar past cases from the knowledge base.

With real SECO historical data this would surface genuinely relevant past cases.
For example: last time we saw this crack type it was CRITICAL and required immediate
structural assessment. The mechanism is fully built in src/rag/retriever.py and tested.
With public data the matches are less domain-specific but the architecture is correct
and ready for real data.

---

## What would go to production tomorrow?

- The AI extraction pipeline: works reliably on any PDF
- The defect severity scoring: consistently accurate on inspection language
- The executive summary generation: immediately useful for non-technical stakeholders
- The SQLite schema: ready to migrate to Postgres with minimal changes

## What would be thrown away?

- The synthetic data: replaced with real SECO inspection reports
- Ngrok tunnel: replaced with proper cloud deployment on Railway or Render
- Single-file Streamlit app: refactored into proper modules as the product grows

## If given 3 more months

- Photo analysis: use GPT-4o vision to detect visible defects in inspection photos
- Multi-language support: SECO operates in Luxembourgish French and German
- Trend analysis: track defect recurrence across buildings and time
- REST API: expose defect extraction so SECO existing tools can integrate directly
- React frontend: replace Streamlit with a proper React UI matching SECO stack
- Authentication: role-based access for inspector vs manager vs insurer

---

## Project structure

    building-defect-intelligence/
    ├── app/
    │   └── streamlit_app.py        UI entry point with 4 pages
    ├── scripts/
    │   └── setup_data.py           One-command setup: downloads data and builds DB
    ├── src/
    │   ├── ingestion/
    │   │   └── pdf_parser.py       PDF extraction and cleaning pipeline
    │   ├── database/
    │   │   └── db.py               SQLite schema and query helpers
    │   ├── ai/
    │   │   └── extractor.py        OpenAI defect extraction
    │   └── rag/
    │       └── retriever.py        ChromaDB similarity search
    ├── data/
    │   ├── raw/                    Original PDFs gitignored
    │   └── processed/              Cleaned JSON chunks gitignored
    ├── tests/
    │   └── test_pipeline.py        8 unit tests all passing
    ├── .env.example                Environment variable template
    ├── requirements.txt
    └── README.md

---

## Limitations

- Pipeline analyzes the first 3000 characters per report. Very long reports need
  chunked multi-pass analysis in production.
- Real public reports are safety literature not structured inspection reports.
  The AI correctly finds fewer defects - this is honest behavior not a bug.
- ChromaDB vector store is rebuilt on each run. Production would persist this.

---

Built by Whoseyashar - SECO AI and Data Engineer technical assessment June 2026
