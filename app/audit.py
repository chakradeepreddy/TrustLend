import csv
import os
from datetime import datetime

LOG = "artifacts/audit_log.csv"
COLUMNS = ["time", "applicant", "ai_said", "risk", "trustlend", "final", "decided_by", "reasons", "note"]

def log(applicant, result, final, decided_by, note=""):
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
