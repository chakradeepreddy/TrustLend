"""
app/db.py — Database abstraction layer for TrustLend.

All SQL lives here. No other file imports psycopg2 directly.

Tables:
  review_cases  — one row per REVIEW case, full lifecycle
  audit_logs    — append-only ledger (automatic + human decisions)

Credentials are read from st.secrets["database"]["DATABASE_URL"]
or the DATABASE_URL environment variable. If neither is set,
all functions return empty/None and log a warning (degraded mode).
"""

import os
import traceback
from datetime import datetime
from typing import Optional

import streamlit as st

# ── connection ─────────────────────────────────────────────────────────────

def _get_url() -> Optional[str]:
    try:
        return st.secrets["database"]["DATABASE_URL"]
    except Exception:
        pass
    return os.environ.get("DATABASE_URL")


@st.cache_resource
def _get_conn():
    """Return a single shared psycopg2 connection (cached for the app lifetime)."""
    url = _get_url()
    if not url:
        return None
    try:
        import psycopg2
        # Supabase Transaction Pooler requires sslmode=require
        if "sslmode" not in url:
            url += ("&" if "?" in url else "?") + "sslmode=require"
        conn = psycopg2.connect(url, connect_timeout=10)
        conn.autocommit = True   # required for Supabase Transaction Pooler
        return conn
    except Exception:
        traceback.print_exc()
        return None


def _conn():
    """Return connection, reconnecting if it was dropped."""
    conn = _get_conn()
    if conn is None:
        return None
    try:
        import psycopg2
        if conn.closed:
            # clear cache so next call re-opens
            _get_conn.clear()
            return _get_conn()
        # lightweight ping
        conn.cursor().execute("SELECT 1")
        conn.commit()
    except Exception:
        try:
            _get_conn.clear()
            conn = _get_conn()
        except Exception:
            return None
    return conn


# ── schema init ────────────────────────────────────────────────────────────

DDL = """
CREATE TABLE IF NOT EXISTS review_cases (
    id                      SERIAL PRIMARY KEY,
    file_no                 TEXT        NOT NULL,
    applicant_name          TEXT        NOT NULL,

    -- applicant features
    age                     REAL,
    monthly_income          REAL,
    debt_ratio              REAL,
    revolving_utilization   REAL,
    num_open_credit_lines   REAL,
    num_real_estate_loans   REAL,
    num_dependents          REAL,
    times_30_59_late        REAL,
    times_60_89_late        REAL,
    times_90_late           REAL,

    -- model outputs
    model_says              TEXT        NOT NULL,
    p_default               REAL        NOT NULL,
    trustlend_decision      TEXT        NOT NULL,
    unsure                  BOOLEAN     NOT NULL,
    unfamiliar              BOOLEAN     NOT NULL,
    familiarity_distance    REAL        NOT NULL,
    reasons                 TEXT,

    -- review lifecycle
    status                  TEXT        NOT NULL DEFAULT 'pending',
    reviewer_identity       TEXT,
    reviewer_decision       TEXT,
    reviewer_note           TEXT,
    reviewed_at             TIMESTAMPTZ,

    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_review_cases_status
    ON review_cases (status);

CREATE TABLE IF NOT EXISTS audit_logs (
    id          SERIAL PRIMARY KEY,
    time        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    applicant   TEXT        NOT NULL,
    ai_said     TEXT        NOT NULL,
    risk        REAL        NOT NULL,
    trustlend   TEXT        NOT NULL,
    final       TEXT        NOT NULL,
    decided_by  TEXT        NOT NULL,
    reasons     TEXT,
    note        TEXT
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_time
    ON audit_logs (time DESC);
"""


def init_db():
    """Create tables if they don't exist. Safe to call on every startup."""
    conn = _conn()
    if conn is None:
        print("[db] No DATABASE_URL — skipping init_db()")
        return False
    try:
        with conn.cursor() as cur:
            cur.execute(DDL)
        # autocommit=True so no explicit commit needed
        return True
    except Exception:
        traceback.print_exc()
        return False


# ── review cases ───────────────────────────────────────────────────────────

def create_review_case(file_no: str, applicant_name: str,
                       applicant: dict, result: dict) -> Optional[int]:
    """
    Insert a new pending review case.
    Returns the new row id, or None on failure.
    """
    conn = _conn()
    if conn is None:
        return None
    sql = """
        INSERT INTO review_cases (
            file_no, applicant_name,
            age, monthly_income, debt_ratio, revolving_utilization,
            num_open_credit_lines, num_real_estate_loans, num_dependents,
            times_30_59_late, times_60_89_late, times_90_late,
            model_says, p_default, trustlend_decision,
            unsure, unfamiliar, familiarity_distance, reasons
        ) VALUES (
            %s, %s,
            %s, %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s,
            %s, %s, %s, %s
        )
        RETURNING id;
    """
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (
                file_no, applicant_name,
                applicant.get("age"),
                applicant.get("MonthlyIncome"),
                applicant.get("DebtRatio"),
                applicant.get("RevolvingUtilizationOfUnsecuredLines"),
                applicant.get("NumberOfOpenCreditLinesAndLoans"),
                applicant.get("NumberRealEstateLoansOrLines"),
                applicant.get("NumberOfDependents"),
                applicant.get("NumberOfTime30-59DaysPastDueNotWorse"),
                applicant.get("NumberOfTime60-89DaysPastDueNotWorse"),
                applicant.get("NumberOfTimes90DaysLate"),
                result["model_says"],
                result["p_default"],
                result["decision"],
                result["unsure"],
                result["unfamiliar"],
                result["familiarity_distance"],
                " | ".join(result.get("reasons", [])),
            ))
            row_id = cur.fetchone()[0]
        return row_id
    except Exception:
        traceback.print_exc()
        return None


def get_pending_reviews() -> list:
    """Return all pending review cases, oldest first."""
    conn = _conn()
    if conn is None:
        return []
    sql = """
        SELECT id, file_no, applicant_name,
               age, monthly_income, debt_ratio, revolving_utilization,
               num_open_credit_lines, num_real_estate_loans, num_dependents,
               times_30_59_late, times_60_89_late, times_90_late,
               model_says, p_default, trustlend_decision,
               unsure, unfamiliar, familiarity_distance, reasons,
               created_at
        FROM review_cases
        WHERE status = 'pending'
        ORDER BY created_at ASC;
    """
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    except Exception:
        traceback.print_exc()
        return []


def complete_review(case_id: int, decision: str,
                    note: str = "", reviewer: str = "human reviewer") -> bool:
    """Mark a review case as approved or denied."""
    conn = _conn()
    if conn is None:
        return False
    sql = """
        UPDATE review_cases
        SET status            = %s,
            reviewer_decision = %s,
            reviewer_note     = %s,
            reviewer_identity = %s,
            reviewed_at       = NOW()
        WHERE id = %s;
    """
    status = "approved" if decision == "APPROVE" else "denied"
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (status, decision, note, reviewer, case_id))
        return True
    except Exception:
        traceback.print_exc()
        return False


def count_pending_reviews() -> int:
    """Return number of pending review cases (used by sidebar badge)."""
    conn = _conn()
    if conn is None:
        return 0
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM review_cases WHERE status = 'pending';")
            return cur.fetchone()[0]
    except Exception:
        return 0


# ── audit logs ─────────────────────────────────────────────────────────────

def create_audit_entry(applicant: str, result: dict,
                       final: str, decided_by: str, note: str = "") -> bool:
    """Append one row to the audit_logs table."""
    conn = _conn()
    if conn is None:
        return False
    sql = """
        INSERT INTO audit_logs
            (applicant, ai_said, risk, trustlend, final, decided_by, reasons, note)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
    """
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (
                applicant,
                result["model_says"],
                result["p_default"],
                result["decision"],
                final,
                decided_by,
                " | ".join(result.get("reasons", [])),
                note,
            ))
        return True
    except Exception:
        traceback.print_exc()
        return False


def get_audit_history(limit: int = 500) -> list:
    """Return audit log rows, newest first."""
    conn = _conn()
    if conn is None:
        return []
    sql = """
        SELECT time, applicant, ai_said, risk, trustlend, final,
               decided_by, reasons, note
        FROM audit_logs
        ORDER BY time DESC
        LIMIT %s;
    """
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (limit,))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
    except Exception:
        traceback.print_exc()
        return []
