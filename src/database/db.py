import sqlite3
import json
import os

DB_PATH = "data/building_intelligence.db"

def get_connection():
    """Return a connection to the SQLite database."""
    return sqlite3.connect(DB_PATH)

def init_database():
    """Create tables if they do not exist."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS reports (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            filename    TEXT NOT NULL,
            source_type TEXT NOT NULL,
            location    TEXT,
            inspector   TEXT,
            date        TEXT,
            num_pages   INTEGER,
            num_chunks  INTEGER,
            full_text   TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS defects (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id   INTEGER NOT NULL,
            severity    TEXT NOT NULL,
            title       TEXT NOT NULL,
            description TEXT,
            recommendation TEXT,
            urgency     TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (report_id) REFERENCES reports(id)
        );

        CREATE TABLE IF NOT EXISTS chunks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id   INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL,
            text        TEXT NOT NULL,
            FOREIGN KEY (report_id) REFERENCES reports(id)
        );
    """)
    conn.commit()
    conn.close()

def insert_report(filename, source_type, location, inspector,
                  date, num_pages, num_chunks, full_text):
    """Insert a report and return its id."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reports
        (filename, source_type, location, inspector, date, num_pages, num_chunks, full_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (filename, source_type, location, inspector,
          date, num_pages, num_chunks, full_text))
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return report_id

def insert_defect(report_id, severity, title, description,
                  recommendation, urgency):
    """Insert a defect record."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO defects
        (report_id, severity, title, description, recommendation, urgency)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (report_id, severity, title, description, recommendation, urgency))
    conn.commit()
    conn.close()

def insert_chunk(report_id, chunk_index, text):
    """Insert a text chunk."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO chunks (report_id, chunk_index, text)
        VALUES (?, ?, ?)
    """, (report_id, chunk_index, text))
    conn.commit()
    conn.close()

def get_all_defects():
    """Return all defects with their report filename."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT d.id, d.severity, d.title, d.description,
               d.recommendation, d.urgency, r.filename, r.location
        FROM defects d
        JOIN reports r ON d.report_id = r.id
        ORDER BY CASE d.severity
            WHEN 'CRITICAL' THEN 1
            WHEN 'HIGH'     THEN 2
            WHEN 'MEDIUM'   THEN 3
            ELSE 4 END
    """).fetchall()
    conn.close()
    return rows

def get_all_reports():
    """Return all reports summary."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT id, filename, source_type, location,
               inspector, date, num_pages, num_chunks
        FROM reports
        ORDER BY id
    """).fetchall()
    conn.close()
    return rows

def get_defect_stats():
    """Return defect counts by severity."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT severity, COUNT(*) as count
        FROM defects
        GROUP BY severity
        ORDER BY CASE severity
            WHEN 'CRITICAL' THEN 1
            WHEN 'HIGH'     THEN 2
            WHEN 'MEDIUM'   THEN 3
            ELSE 4 END
    """).fetchall()
    conn.close()
    return dict(rows)
