import numpy as np
from src.model import CUTOFF, COST_MISSED_DEFAULT, COST_WRONG_DENIAL

BUDGET = 0.15      # at most 15% of applicants go to a human

def avg_cost(y, p):
    deny = p >= CUTOFF
    missed = (~deny) & (y == 1)        # approved, didn't repay
    wrong = deny & (y == 0)            # denied, would have repaid
    return float((COST_MISSED_DEFAULT * missed + COST_WRONG_DENIAL * wrong).mean())

def choose_thresholds(p_val, d_val, y_val):
    best = None
    for band in [0.0, 0.02, 0.04, 0.06, 0.08, 0.10]:
        for q in [0.90, 0.95, 0.975, 0.99, 1.0]:
            t = float(np.quantile(d_val, q))
            review = (np.abs(p_val - CUTOFF) < band) | (d_val > t)
            if review.mean() > BUDGET:
                continue                           # too many for the humans
            cost = avg_cost(y_val[~review], p_val[~review])
            if best is None or cost < best["cost"]:
                best = {"band": band, "percentile": q, "fam_threshold": t,
                        "cost": cost, "review_rate": float(review.mean())}
    return best
