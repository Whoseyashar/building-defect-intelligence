import fitz
import re
import json
import os

def extract_text_from_pdf(filepath):
    """Extract raw text from PDF page by page."""
    doc = fitz.open(filepath)
    pages = []
    for page_num, page in enumerate(doc, 1):
        text = page.get_text()
        pages.append({"page": page_num, "raw_text": text})
    doc.close()
    return pages

def clean_text(text):
    """Clean raw extracted PDF text."""
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'[^\x00-\x7F\n]+', ' ', text)
    text = re.sub(r'\.(?=[A-Z])', '. ', text)
    text = re.sub(r' {2,}', ' ', text)
    lines = [line.strip() for line in text.split('\n')]
    return '\n'.join(line for line in lines if line).strip()

def chunk_text(text, chunk_size=500, overlap=50):
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = ' '.join(words[start:end])
        if len(chunk) > 100:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def detect_source_type(text):
    """Detect whether report is synthetic or real public."""
    if any(kw in text.upper() for kw in ["SECO GROUP", "LUXEMBOURG",
                                           "JEAN-PIERRE", "MARCO ROSSI"]):
        return "synthetic"
    return "real_public"

def process_pdf(filepath):
    """Full pipeline: extract, clean, chunk, tag."""
    pages = extract_text_from_pdf(filepath)
    raw_text = '\n'.join(p['raw_text'] for p in pages)
    clean = clean_text(raw_text)
    chunks = chunk_text(clean)
    return {
        "filename": os.path.basename(filepath),
        "filepath": filepath,
        "source_type": detect_source_type(clean),
        "num_pages": len(pages),
        "raw_length": len(raw_text),
        "clean_length": len(clean),
        "num_chunks": len(chunks),
        "clean_text": clean,
        "chunks": chunks
    }
