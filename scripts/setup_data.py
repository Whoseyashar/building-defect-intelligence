"""
Run this once after cloning to download public reports,
process them through the pipeline, and populate the database.

Usage: python scripts/setup_data.py
"""

import os
import sys
import re
import json
import sqlite3
import urllib.request

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 55)
print("BUILDING DEFECT INTELLIGENCE - SETUP")
print("=" * 55)

# ── Step 1: Create folders ─────────────────────────────────
os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)
print("\n[1/5] Folders ready")

# ── Step 2: Download real public reports ───────────────────
print("\n[2/5] Downloading public reports...")
sources = [
    ("data/raw/report_001.pdf",
     "https://www.cdc.gov/niosh/docs/2013-102/pdfs/2013-102.pdf",
     "CDC NIOSH Building Dampness Report"),
    ("data/raw/report_002.pdf",
     "https://www.nrc.gov/docs/ML1233/ML12333A170.pdf",
     "NRC Facility Inspection Report"),
    ("data/raw/report_003.pdf",
     "https://www.osha.gov/sites/default/files/publications/OSHA3148.pdf",
     "OSHA Workplace Safety Report"),
]

for path, url, name in sources:
    if os.path.exists(path) and os.path.getsize(path) > 5000:
        print(f"  SKIP (already exists): {name}")
        continue
    try:
        print(f"  Downloading: {name}...")
        urllib.request.urlretrieve(url, path)
        size = os.path.getsize(path)
        if size > 5000:
            print(f"  OK: {size/1024:.0f} KB")
        else:
            os.remove(path)
            print(f"  Failed - file too small")
    except Exception as e:
        print(f"  Failed: {e}")

# ── Step 3: Generate synthetic reports ─────────────────────
print("\n[3/5] Generating synthetic Luxembourg inspection reports...")
try:
    from fpdf import FPDF

    synthetic = [
        {
            "filename": "data/raw/report_004.pdf",
            "title": "Inspection Report - Residential Complex Luxembourg",
            "date": "15 March 2024",
            "inspector": "Jean-Pierre Muller",
            "location": "12 Rue des Fleurs, Luxembourg City",
            "defects": [
                ("CRITICAL", "Structural crack in load-bearing wall",
                 "A 15mm diagonal crack in eastern load-bearing wall at basement B1. "
                 "Foundation movement suspected. Risk of partial collapse if untreated."),
                ("HIGH", "Water infiltration in roof structure",
                 "Water staining on 3rd floor ceiling. Roof membrane damaged near north parapet. "
                 "Mold growth detected. Estimated affected area 45 square meters."),
                ("MEDIUM", "Deteriorated window seals on south facade",
                 "Window seals on floors 2 and 3 show advanced deterioration. "
                 "Air infiltration at 1.8 m3/h per window. Affects 12 units."),
                ("LOW", "Surface cracks in exterior render",
                 "Hairline cracks in exterior render on west facade. "
                 "No structural implication. Aesthetic deterioration only."),
            ]
        },
        {
            "filename": "data/raw/report_005.pdf",
            "title": "Inspection Report - Industrial Warehouse Differdange",
            "date": "8 May 2024",
            "inspector": "Marco Rossi",
            "location": "Zone Industrielle, Differdange, Luxembourg",
            "defects": [
                ("CRITICAL", "Fire safety door non-compliant",
                 "Emergency exit door on level 4 does not close automatically. "
                 "Non-compliant with EN 1634-1. Occupancy permit at risk."),
                ("HIGH", "Roof structure fatigue in steel purlins",
                 "Three steel purlins in grid C4-D4 show deflection exceeding L/200. "
                 "Overloading from rooftop equipment suspected."),
                ("HIGH", "Asbestos-containing materials identified",
                 "Suspected asbestos insulation around heating pipes in room TR-01. "
                 "Area cordoned off. Asbestos management plan required."),
                ("MEDIUM", "Inadequate drainage in loading bay",
                 "Standing water after rainfall. Channels blocked with debris. "
                 "Slip hazard and freeze damage risk in winter."),
            ]
        },
    ]

    colors = {"CRITICAL":(220,50,50),"HIGH":(230,126,34),
               "MEDIUM":(200,160,0),"LOW":(46,160,80)}

    for report in synthetic:
        if os.path.exists(report["filename"]) and os.path.getsize(report["filename"]) > 1000:
            print(f"  SKIP (already exists): {report['filename']}")
            continue
        pdf = FPDF()
        pdf.add_page()
        pdf.set_fill_color(30, 60, 114)
        pdf.rect(0, 0, 210, 35, "F")
        pdf.set_font("Helvetica", "B", 16)
        pdf.set_text_color(255, 255, 255)
        pdf.set_xy(10, 8)
        pdf.cell(0, 8, "SECO GROUP - TECHNICAL INSPECTION REPORT")
        pdf.set_font("Helvetica", "", 10)
        pdf.set_xy(10, 22)
        pdf.cell(0, 8, report["title"])
        pdf.set_text_color(0, 0, 0)
        pdf.set_y(45)
        for label, value in [("Date:", report["date"]),
                              ("Inspector:", report["inspector"]),
                              ("Location:", report["location"])]:
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(40, 8, label, new_x="RIGHT", new_y="TOP")
            pdf.set_font("Helvetica", "", 11)
            pdf.cell(0, 8, value, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)
        pdf.set_font("Helvetica", "B", 13)
        pdf.cell(0, 10, "Defect Observations", new_x="LMARGIN", new_y="NEXT")
        for i, (severity, title, description) in enumerate(report["defects"], 1):
            r, g, b = colors[severity]
            pdf.set_fill_color(r, g, b)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Helvetica", "B", 9)
            pdf.cell(24, 7, severity, fill=True, new_x="RIGHT", new_y="TOP")
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "B", 11)
            pdf.cell(5, 7, "", new_x="RIGHT", new_y="TOP")
            pdf.cell(0, 7, f"{i}. {title}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("Helvetica", "", 10)
            pdf.set_x(10)
            pdf.multi_cell(0, 6, description)
            pdf.ln(3)
        pdf.output(report["filename"])
        print(f"  Created: {report['filename']}")

except ImportError:
    print("  fpdf2 not installed - run: pip install fpdf2")

# ── Step 4: Run cleaning pipeline ──────────────────────────
print("\n[4/5] Processing PDFs through cleaning pipeline...")

import fitz

def clean_text(text):
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"[^\x00-\x7F\n]+", " ", text)
    text = re.sub(r" {2,}", " ", text)
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(line for line in lines if line).strip()

def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        if len(chunk) > 100:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def detect_source(text):
    if any(k in text.upper() for k in ["SECO GROUP","LUXEMBOURG","JEAN-PIERRE","MARCO ROSSI"]):
        return "synthetic"
    return "real_public"

processed = []
for filename in sorted(os.listdir("data/raw")):
    if not filename.endswith(".pdf"):
        continue
    filepath = f"data/raw/{filename}"
    doc = fitz.open(filepath)
    raw = "\n".join(page.get_text() for page in doc)
    pages = doc.page_count
    doc.close()
    clean = clean_text(raw)
    chunks = chunk_text(clean)
    result = {
        "filename": filename,
        "source_type": detect_source(clean),
        "num_pages": pages,
        "clean_text": clean,
        "chunks": chunks,
        "num_chunks": len(chunks)
    }
    processed.append(result)
    out = f"data/processed/{filename.replace('.pdf', '.json')}"
    with open(out, "w") as f:
        json.dump(result, f)
    print(f"  {filename}: {pages} pages, {len(chunks)} chunks ({result['source_type']})")

# ── Step 5: Build database ──────────────────────────────────
print("\n[5/5] Building SQLite database...")

conn = sqlite3.connect("data/building_intelligence.db")
cursor = conn.cursor()

cursor.executescript("""
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT, source_type TEXT, location TEXT,
        inspector TEXT, date TEXT, num_pages INTEGER,
        num_chunks INTEGER, full_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    CREATE TABLE IF NOT EXISTS defects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_id INTEGER, severity TEXT, title TEXT,
        description TEXT, recommendation TEXT, urgency TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (report_id) REFERENCES reports(id)
    );
    CREATE TABLE IF NOT EXISTS chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_id INTEGER, chunk_index INTEGER, text TEXT,
        FOREIGN KEY (report_id) REFERENCES reports(id)
    );
""")

for data in processed:
    existing = conn.execute(
        "SELECT id FROM reports WHERE filename=?", (data["filename"],)
    ).fetchone()
    if existing:
        print(f"  SKIP (already in DB): {data['filename']}")
        continue

    text = data["clean_text"]
    location, inspector, date = "N/A", "N/A", "N/A"
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("Location:"):
            location = line.replace("Location:", "").strip()
        elif line.startswith("Inspector:"):
            inspector = line.replace("Inspector:", "").strip()
        elif line.startswith("Date:"):
            date = line.replace("Date:", "").strip()

    cursor.execute("""
        INSERT INTO reports (filename, source_type, location, inspector,
                             date, num_pages, num_chunks, full_text)
        VALUES (?,?,?,?,?,?,?,?)
    """, (data["filename"], data["source_type"], location, inspector,
          data["num_pages"], data["num_chunks"], text))
    report_id = cursor.lastrowid

    for i, chunk in enumerate(data["chunks"]):
        cursor.execute(
            "INSERT INTO chunks (report_id, chunk_index, text) VALUES (?,?,?)",
            (report_id, i, chunk)
        )
    conn.commit()
    print(f"  Stored: {data['filename']}")

total_reports = conn.execute("SELECT COUNT(*) FROM reports").fetchone()[0]
total_chunks  = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
conn.close()

print(f"\n{'='*55}")
print("SETUP COMPLETE")
print(f"{'='*55}")
print(f"Reports in database : {total_reports}")
print(f"Chunks in database  : {total_chunks}")
print(f"\nNow run: streamlit run app/streamlit_app.py")
print(f"Then open: http://localhost:8501")
