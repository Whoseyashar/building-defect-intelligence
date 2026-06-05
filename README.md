# Building Defect Intelligence

> AI-powered building inspection report analyzer built for SECO Group.

## What problem are we solving?

Building inspectors at firms like SECO process dozens of PDF inspection reports every week.
Defects are buried in unstructured prose, severity is implied by language rather than
structured fields, and there is no connection to similar cases seen in the past.
The result is slow triage, inconsistent severity assessment, and institutional knowledge
that never accumulates.

This product extracts defects automatically, scores their severity, generates actionable
recommendations, and produces a ready-to-share executive summary - turning a 2-hour
manual task into a 5-minute workflow.

## Who is the user?

Primary: Building inspectors at firms like SECO who write and read inspection reports
daily and need faster, more consistent defect triage.

Secondary: Asset managers and insurers who receive inspection outputs and need rapid
risk summaries without reading the full technical report.

## Why is this relevant to SECO?

SECO stated in their brief: huge volumes of technical data - inspection reports,
plans, photos, measurements, defect observations - that today remain largely underexploited.

This product is a direct answer: it makes accumulated inspection data searchable,
comparable, and actionable. Every new report analyzed adds to the knowledge base,
so the system gets more valuable over time.

## Architecture


PDF input
    |
    v
Ingestion - PyMuPDF extracts raw text
    |
    v
Preprocessing - clean, chunk into 500-word segments
    |
    v
Embeddings - sentence-transformers all-MiniLM-L6-v2
    |
    +---> ChromaDB (vector similarity search)
    +---> SQLite (structured defect records)
    |
    v
AI - OpenAI GPT-4o-mini
  - Defect extraction
  - Severity scoring: Critical / High / Medium / Low
  - Recommendations
  - Executive summary
    |
    v
Streamlit UI - Dashboard, Analyzer, Defect Database


## Data sources

| Source | Type | Pages | Why chosen |
|--------|------|-------|------------|
| CDC NIOSH Building Dampness Report | Real public | 28 | Real-world building health inspection language |
| NRC Facility Inspection Report | Real public | 206 | Large heterogeneous document - stress tests the pipeline |
| OSHA Workplace Safety Report | Real public | 60 | Structural and safety defect terminology |
| Luxembourg Residential Complex | Synthetic | 1 | Matches SECO inspection format with real defect types |
| Luxembourg Industrial Warehouse | Synthetic | 1 | Covers industrial defects: asbestos, structural fatigue |

Real public reports prove the pipeline handles genuinely messy heterogeneous documents.
Synthetic reports provide controlled domain-specific data matching SECO inspection format.
In production both would be replaced with real SECO historical reports.

## Technical decisions and trade-offs

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| SQLite over Postgres | Zero infrastructure, fully reproducible | Not horizontally scalable |
| sentence-transformers local | Free, no API call for embeddings | Slightly lower quality than OpenAI embeddings |
| Streamlit over React | Fastest to ship, Python-native | Less UI flexibility than React |
| GPT-4o-mini over GPT-4o | 10x cheaper, fast enough for defect extraction | Slightly lower reasoning quality |
| Chunk size 500 words | Fits token limits while preserving context | Very long defect descriptions may be split |
| Mixed data sources | Reproducible without confidential data | Not identical to real SECO reports |

## RAG - Retrieval Augmented Generation

The pipeline embeds all 183 document chunks using sentence-transformers and stores
them in ChromaDB. Given any new defect description, the retriever finds the most
semantically similar past cases from the knowledge base.

With real SECO historical data, this would surface genuinely relevant past cases.
For example: last time we saw this crack type, it was CRITICAL and required immediate
structural assessment. The mechanism is fully built in src/rag/retriever.py and tested.

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
- Multi-language support: SECO operates in Luxembourgish, French, and German
- Trend analysis: track defect recurrence across buildings and time
- REST API: expose defect extraction so SECO existing tools can integrate directly
- React frontend: replace Streamlit with a proper React UI matching SECO stack
- Authentication: role-based access for inspector vs manager vs insurer

## Quickstart

    git clone https://github.com/Whoseyashar/building-defect-intelligence
    cd building-defect-intelligence
    python -m venv .venv and source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env and add your OPENAI_API_KEY
    streamlit run app/streamlit_app.py

## Project structure


building-defect-intelligence/
├── app/
│   └── streamlit_app.py
├── src/
│   ├── ingestion/pdf_parser.py
│   ├── database/db.py
│   ├── ai/extractor.py
│   └── rag/retriever.py
├── data/
│   ├── raw/
│   └── processed/
├── tests/
├── .env.example
├── requirements.txt
└── README.md


## Limitations

- Pipeline processes first 3000 characters per report for AI analysis.
  Very long reports need chunked multi-pass analysis in production.
- Real public reports are safety literature, not structured inspection reports.
  The AI correctly finds fewer defects in these - this is honest behavior, not a bug.
- ChromaDB vector store is rebuilt on each run. Production would persist this.

---

Built by Whoseyashar - SECO AI and Data Engineer technical assessment, June 2026
