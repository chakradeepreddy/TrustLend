import json
import joblib
import pandas as pd
from src.data import FEATURES, TARGET
from src.model import CUTOFF

model = joblib.load("artifacts/model.joblib")
fam = joblib.load("artifacts/familiarity.joblib")
T = json.load(open("artifacts/thresholds.json"))

def decide(applicant: dict) -> dict:
    """applicant: one row, with the same column names as the CSV."""
    row = pd.DataFrame([applicant]).reindex(columns=FEATURES).astype(float)
    p = float(model.predict_proba(row)[0, 1])            # the AI: one number
    model_says = "DENY" if p >= CUTOFF else "APPROVE"    # the plain decision

    unsure = abs(p - CUTOFF) < T["band"]                 # Check 1 looks at the risk
    dist, idx = fam.distance(row)                        # Check 2 looks at the person
    unfamiliar = bool(dist[0] > T["fam_threshold"])

    reasons = []
    if unsure:
        reasons.append(f"Risk {p:.1%} is close to the {CUTOFF:.0%} line")
    if unfamiliar:
        reasons += fam.reasons(row.iloc[0])

    near = fam.ref_rows.iloc[idx[0][:5]]                 # 5 most similar people
    neighbours = [{"age": int(r["age"]),
                   "MonthlyIncome": None if pd.isna(r["MonthlyIncome"]) else float(r["MonthlyIncome"]),
                   "outcome": "did not repay" if r[TARGET] == 1 else "repaid"}
                  for _, r in near.iterrows()]

    return {"decision": "REVIEW" if (unsure or unfamiliar) else model_says,
            "model_says": model_says, "p_default": p,
            "unsure": bool(unsure), "unfamiliar": unfamiliar,
            "familiarity_distance": float(dist[0]),
            "reasons": reasons, "neighbours": neighbours}
