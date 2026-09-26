"""
app/db.py — Database abstraction layer for TrustLend.

All SQL lives here. No other file imports psycopg2 directly.

Tables:
  review_cases  — one row per REVIEW case, full lifecycle
  audit_logs    — append-only ledger (automatic + human decisions)

Credentials are read from st.secrets["database"]["DATABASE_URL"]
or the DATABASE_URL environment variable. If neither is set,
all functions return empty/None (degraded mode).

Connection strategy: fresh connection per call, closed immediately after.
This is correct for Supabase Transaction Pooler — the pooler manages
server-side connection reuse; long-lived client connections cause stale
cursor errors and silent write failures.
"""

import os
import traceback
from typing import Optional

# ── credentials ────────────────────────────────────────────────────────────

def _get_url() -> Optional[str]:
    try:
        import streamlit as st
        return st.secrets["database"]["DATABASE_URL"]
    except Exception:
        pass
    return os.environ.get("DATABASE_URL")


def _open() -> Optional[object]:
    """
    Open and return a fresh psycopg2 connection with autocommit=True.
    Returns None if DATABASE_URL is unavailable or connection fails.
    """
    url = _get_url()
    if not url:
        return None
    try:
        import psycopg2
        if "sslmode" not in url:
            url += ("&" if "?" in url else "?") + "sslmode=require"
        conn = psycopg2.connect(url, connect_timeout=10)
        conn.autocommit = True
        return conn
    except Exception:
        traceback.print_exc()
        return None


# ── schema init ────────────────────────────────────────────────────────────

DDL = """
CREATE TABLE IF NOT EXISTS review_cases (
    id                      SERIAL PRIMARY KEY,
    file_no                 TEXT        NOT NULL,
    applicant_name          TEXT        NOT NULL,
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
    model_says              TEXT        NOT NULL,
    p_default               REAL        NOT NULL,
    trustlend_decision      TEXT        NOT NULL,
    unsure                  BOOLEAN     NOT NULL,
    unfamiliar              BOOLEAN     NOT NULL,
    familiarity_distance    REAL        NOT NULL,
    reasons                 TEXT,
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


def init_db() -> bool:
    """Create tables if they don't exist. Safe to call on every startup."""
    conn = _open()
    if conn is None:
        print("[db] No DATABASE_URL — skipping init_db()")
        return False
    try:
        with conn.cursor() as cur:
            cur.execute(DDL)
        return True
    except Exception:
        traceback.print_exc()
        return False
    finally:
        conn.close()


# ── review cases ───────────────────────────────────────────────────────────

def create_review_case(file_no: str, applicant_name: str,
                       applicant: dict, result: dict) -> Optional[int]:
    """
    Insert a new pending review case.
    Returns the new row id, or None on failure.
    """
    conn = _open()
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
    finally:
        conn.close()


def get_pending_reviews() -> list:
    """Return all pending review cases, oldest first."""
    conn = _open()
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
    finally:
        conn.close()


def complete_review(case_id: int, decision: str,
                    note: str = "", reviewer: str = "human reviewer") -> bool:
    """Mark a review case as approved or denied."""
    conn = _open()
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
    finally:
        conn.close()


def count_pending_reviews() -> int:
    """Return number of pending review cases (used by sidebar badge)."""
    conn = _open()
    if conn is None:
        return 0
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM review_cases WHERE status = 'pending';")
            return cur.fetchone()[0]
    except Exception:
        return 0
    finally:
        try:
            conn.close()
        except Exception:
            pass


# ── audit logs ─────────────────────────────────────────────────────────────

def create_audit_entry(applicant: str, result: dict,
                       final: str, decided_by: str, note: str = "") -> bool:
    """Append one row to the audit_logs table."""
    conn = _open()
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
    finally:
        conn.close()


def get_audit_history(limit: int = 500) -> list:
    """Return audit log rows, newest first."""
    conn = _open()
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
    finally:
        conn.close()
