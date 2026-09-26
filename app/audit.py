"""
app/audit.py — Write audit entries to PostgreSQL (primary) and CSV (backup).

The CSV at artifacts/audit_log.csv is kept as a local backup only.
PostgreSQL is the source of truth for the deployed application.
"""

import csv
import os
from datetime import datetime

LOG = "artifacts/audit_log.csv"
COLUMNS = ["time", "applicant", "ai_said", "risk", "trustlend", "final", "decided_by", "reasons", "note"]


def log(applicant, result, final, decided_by, note=""):
    # ── 1. PostgreSQL (primary) ─────────────────────────────────────────
    try:
        from db import create_audit_entry
        create_audit_entry(applicant, result, final, decided_by, note)
    except Exception as e:
        import traceback
        traceback.print_exc()
        # degraded mode — fall through to CSV

    # ── 2. CSV backup (local only) ─────────────────────────────────────
    try:
        os.makedirs("artifacts", exist_ok=True)
        new = not os.path.exists(LOG)
        with open(LOG, "a", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(COLUMNS)
            w.writerow([
                datetime.now().isoformat(timespec="seconds"),
                applicant,
                result["model_says"],
                f"{result['p_default']:.3f}",
                result["decision"],
                final,
                decided_by,
                " | ".join(result["reasons"]),
                note
            ])
    except Exception:
        pass
