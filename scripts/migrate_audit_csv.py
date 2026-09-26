"""
scripts/migrate_audit_csv.py

One-time migration: import existing audit_log.csv records into PostgreSQL.

Safe to run multiple times — uses ON CONFLICT DO NOTHING to avoid duplicates
(keyed on time + applicant + decided_by).

Usage:
    cd /path/to/TrustLend
    conda run -n trustlend python scripts/migrate_audit_csv.py
"""

import sys
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "app")]

LOG = ROOT / "artifacts" / "audit_log.csv"

if not LOG.exists():
    print(f"[migrate] {LOG} not found — nothing to migrate.")
    sys.exit(0)

# ── load and clean CSV ──────────────────────────────────────────────────────
import pandas as pd
import io

raw = LOG.read_bytes().decode("utf-8", errors="replace")

# Fix known corruption: rows concatenated without newline (e.g. line 31)
# Split on the pattern  ",\n2026-"  and ensure each record is on its own line
import re
raw = re.sub(r"(?<!\n)(20\d\d-\d\d-\d\dT\d\d:\d\d:\d\d)", r"\n\1", raw)

try:
    df = pd.read_csv(io.StringIO(raw))
except Exception as e:
    print(f"[migrate] Failed to parse CSV: {e}")
    sys.exit(1)

EXPECTED = ["time", "applicant", "ai_said", "risk", "trustlend", "final", "decided_by", "reasons", "note"]
for col in EXPECTED:
    if col not in df.columns:
        df[col] = None

df = df[EXPECTED].copy()
df["risk"] = pd.to_numeric(df["risk"], errors="coerce")
df["time"] = pd.to_datetime(df["time"], errors="coerce")
df = df[df["time"].notna()]   # drop rows with unparseable timestamps
df["reasons"] = df["reasons"].fillna("")
df["note"] = df["note"].fillna("")

print(f"[migrate] {len(df)} clean rows found in {LOG.name}")

# ── connect ─────────────────────────────────────────────────────────────────
url = None
try:
    import streamlit as st
    url = st.secrets["database"]["DATABASE_URL"]
except Exception:
    url = os.environ.get("DATABASE_URL")

if not url:
    print("[migrate] ERROR: DATABASE_URL not found in secrets or environment.")
    sys.exit(1)

import psycopg2
conn = psycopg2.connect(url, connect_timeout=10)
conn.autocommit = False

SQL = """
    INSERT INTO audit_logs (time, applicant, ai_said, risk, trustlend, final, decided_by, reasons, note)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT DO NOTHING;
"""

# Supabase doesn't have a unique constraint by default, so we add one first
try:
    with conn.cursor() as cur:
        cur.execute("""
            ALTER TABLE audit_logs
            ADD CONSTRAINT uq_audit_time_applicant_by
            UNIQUE (time, applicant, decided_by);
        """)
    conn.commit()
    print("[migrate] Unique constraint created.")
except Exception:
    conn.rollback()
    print("[migrate] Unique constraint already exists (or skipped).")

imported = 0
skipped = 0

with conn.cursor() as cur:
    for _, row in df.iterrows():
        try:
            cur.execute(SQL, (
                row["time"].isoformat(),
                str(row["applicant"]) if pd.notna(row["applicant"]) else "",
                str(row["ai_said"])   if pd.notna(row["ai_said"])   else "",
                float(row["risk"])    if pd.notna(row["risk"])       else None,
                str(row["trustlend"]) if pd.notna(row["trustlend"]) else "",
                str(row["final"])     if pd.notna(row["final"])     else "",
                str(row["decided_by"]) if pd.notna(row["decided_by"]) else "",
                str(row["reasons"])   if pd.notna(row["reasons"])   else "",
                str(row["note"])      if pd.notna(row["note"])      else "",
            ))
            imported += 1
        except Exception as e:
            skipped += 1
            print(f"  [skip] row {_}: {e}")

conn.commit()
conn.close()

print(f"[migrate] Done. Imported: {imported}  Skipped/duplicate: {skipped}")
print("[migrate] The original CSV is untouched.")
