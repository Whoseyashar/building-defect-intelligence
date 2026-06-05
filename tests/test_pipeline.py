import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingestion.pdf_parser import clean_text, chunk_text, detect_source_type


def test_clean_text_removes_extra_whitespace():
    dirty = "Hello   World\n\n\nThis is a test"
    result = clean_text(dirty)
    assert "   " not in result
    assert "\n\n\n" not in result


def test_clean_text_removes_standalone_page_numbers():
    text = "Some content\n42\nMore content"
    result = clean_text(text)
    assert "\n42\n" not in result


def test_chunk_text_splits_correctly():
    words = " ".join([f"word{i}" for i in range(1000)])
    chunks = chunk_text(words, chunk_size=100, overlap=10)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk) > 0


def test_chunk_text_overlap():
    words = " ".join([f"word{i}" for i in range(200)])
    chunks = chunk_text(words, chunk_size=100, overlap=20)
    assert len(chunks) >= 2


def test_detect_source_type_synthetic():
    text = "SECO GROUP - TECHNICAL INSPECTION REPORT Luxembourg"
    assert detect_source_type(text) == "synthetic"


def test_detect_source_type_real():
    text = "Department of Health and Human Services occupational safety"
    assert detect_source_type(text) == "real_public"


def test_clean_text_preserves_content():
    text = "Structural crack in load-bearing wall requires immediate attention"
    result = clean_text(text)
    assert "Structural crack" in result
    assert "immediate attention" in result


def test_chunk_text_minimum_length():
    short_text = "Too short"
    chunks = chunk_text(short_text, chunk_size=500, overlap=50)
    assert len(chunks) == 0
