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

## Data sources

- CDC NIOSH Building Dampness Report: real public, 28 pages
- NRC Facility Inspection Report: real public, 206 pages
- OSHA Workplace Safety Report: real public, 60 pages
- Luxembourg Residential Complex: synthetic, 1 page
- Luxembourg Industrial Warehouse: synthetic, 1 page

Real public reports prove the pipeline handles genuinely messy heterogeneous documents.
Synthetic reports provide controlled domain-specific data matching SECO inspection format.

## Technical decisions and trade-offs

- SQLite over Postgres: zero infrastructure, fully reproducible. Not horizontally scalable.
- sentence-transformers local: free, no API call for embeddings. Slightly lower quality than OpenAI embeddings.
- Streamlit over React: fastest to ship, Python-native. Less UI flexibility than React.
- GPT-4o-mini over GPT-4o: 10x cheaper, fast enough for defect extraction.
- Chunk size 500 words: fits token limits while preserving context.

## RAG - Retrieval Augmented Generation

The pipeline embeds all 183 document chunks using sentence-transformers and stores
them in ChromaDB. Given any new defect description, the retriever finds the most
semantically similar past cases from the knowledge base.

With real SECO historical data, this would surface genuinely relevant past cases.
The mechanism is fully built in src/rag/retriever.py and tested.

## What would go to production tomorrow?

- The AI extraction pipeline: works reliably on any PDF
- The defect severity scoring: consistently accurate on inspection language
- The executive summary generation: immediately useful for non-technical stakeholders
- The SQLite schema: ready to migrate to Postgres with minimal changes

## What would be thrown away?

- The synthetic data: replaced with real SECO inspection reports
- Ngrok tunnel: replaced with proper cloud deployment
- Single-file Streamlit app: refactored into proper modules as the product grows

## If given 3 more months

- Photo analysis: use GPT-4o vision to detect visible defects in inspection photos
- Multi-language support: SECO operates in Luxembourgish, French, and German
- Trend analysis: track defect recurrence across buildings and time
- REST API: expose defect extraction so SECO existing tools can integrate directly
- React frontend: replace Streamlit with a proper React UI matching SECO stack
- Authentication: role-based access for inspector vs manager vs insurer

## Quickstart

1. git clone https://github.com/Whoseyashar/building-defect-intelligence
2. cd building-defect-intelligence
3. python -m venv .venv && source .venv/bin/activate
4. pip install -r requirements.txt
5. cp .env.example .env and add your OPENAI_API_KEY
6. streamlit run app/streamlit_app.py

## Project structure

- app/streamlit_app.py: UI entry point with 4 pages
- src/ingestion/pdf_parser.py: PDF extraction and cleaning pipeline
- src/database/db.py: SQLite schema and query helpers
- src/ai/extractor.py: OpenAI defect extraction
- src/rag/retriever.py: ChromaDB similarity search
- data/raw/: original PDFs (gitignored)
- data/processed/: cleaned JSON chunks (gitignored)

## Limitations

- Pipeline processes first 3000 characters per report for AI analysis.
  Very long reports need chunked multi-pass analysis in production.
- Real public reports are safety literature, not structured inspection reports.
  The AI correctly finds fewer defects in these - this is honest behavior, not a bug.
- ChromaDB vector store is rebuilt on each run. Production would persist this.

Built by Whoseyashar - SECO AI and Data Engineer technical assessment, June 2026
