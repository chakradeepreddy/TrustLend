"""
TrustLend Evaluation Harness Module.

Provides evaluation routines, metric summaries, risk-coverage trade-off curves,
and deferral breakdown calculations based on the TrustLend specification.

Shared decide interface contract:
    decide(applicant: dict) -> dict
Expected return fields:
    - decision: "APPROVE" | "DENY" | "REVIEW"
    - model_says: "APPROVE" | "DENY"
    - p_default: float
    - unsure: bool
    - unfamiliar: bool
    - familiarity_distance: float
    - reasons: list
    - neighbours: list
"""

from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd

try:
    from src.data import FEATURES, TARGET
except ImportError:
    TARGET = "SeriousDlqin2yrs"
    FEATURES = [
        "RevolvingUtilizationOfUnsecuredLines",
        "age",
        "NumberOfTime30-59DaysPastDueNotWorse",
        "DebtRatio",
        "MonthlyIncome",
        "NumberOfOpenCreditLinesAndLoans",
        "NumberOfTimes90DaysLate",
        "NumberRealEstateLoansOrLines",
        "NumberOfTime60-89DaysPastDueNotWorse",
        "NumberOfDependents",
    ]


class CostResult(dict):
    """
    Container for classification cost results.

    Supports dict access (cost['total_cost']), attribute access (cost.total_cost),
    tuple unpacking (total, avg = cost), and float casting (float(cost)).
    """

    def __init__(self, total_cost: float, average_cost: float):
        super().__init__(
            total_cost=total_cost,
            average_cost=average_cost,
            total=total_cost,
            average=average_cost,
        )
        self.total_cost = float(total_cost)
        self.average_cost = float(average_cost)
        self.total = float(total_cost)
        self.average = float(average_cost)

    def __float__(self) -> float:
        return self.total_cost

    def __iter__(self):
        return iter((self.total_cost, self.average_cost))

    def __repr__(self) -> str:
        return f"CostResult(total_cost={self.total_cost:.2f}, average_cost={self.average_cost:.4f})"


def evaluate_rows(
    rows: pd.DataFrame,
    decide_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
) -> pd.DataFrame:
    """
    Evaluate a set of applicant rows against the decide function.

    Parameters:
        rows: DataFrame containing applicant feature columns and TARGET.
        decide_fn: Function taking an applicant dict and returning decision metadata.

    Returns:
        DataFrame containing evaluation results, decision metadata, true labels,
        and preserved applicant features.
    """
    feature_cols = [c for c in FEATURES if c in rows.columns]
    if not feature_cols:
        feature_cols = [c for c in rows.columns if c != TARGET]

    records = rows.to_dict(orient="records")
    eval_records: List[Dict[str, Any]] = []

    for idx, record in zip(rows.index, records):
        applicant = {k: record[k] for k in feature_cols if k in record}
        decision_output = decide_fn(applicant)

        decision = decision_output.get("decision", "REVIEW")
        model_says = decision_output.get("model_says", "DENY")
        p_default = float(decision_output.get("p_default", 0.5))
        unsure = bool(decision_output.get("unsure", False))
        unfamiliar = bool(decision_output.get("unfamiliar", False))
        fam_dist = float(decision_output.get("familiarity_distance", 0.0))
        y_true = record.get(TARGET, np.nan)
        automatically_decided = bool(decision != "REVIEW")

        eval_row = {
            "p_default": p_default,
            "model_says": model_says,
            "decision": decision,
            "unsure": unsure,
            "unfamiliar": unfamiliar,
            "familiarity_distance": fam_dist,
            "y_true": y_true,
            "automatically_decided": automatically_decided,
        }

        # Preserve key demographic/feature columns for subsequent group analyses
        for col in feature_cols:
            if col not in eval_row:
                eval_row[col] = record.get(col, np.nan)

        eval_records.append(eval_row)

    return pd.DataFrame(eval_records, index=rows.index)


def classification_cost(
    y_true: Union[pd.Series, np.ndarray, List[Any]],
    decisions: Union[pd.Series, np.ndarray, List[Any]],
) -> CostResult:
    """
    Calculate classification cost based on the project cost matrix:
        - missed default / false approval (y_true == 1, decision == 'APPROVE') = 5
        - wrong denial (y_true == 0, decision == 'DENY') = 1
        - correct decisions = 0
        - REVIEW is deferred to human review and incurs 0 automatic classification cost.

    Returns:
        CostResult containing total_cost and average_cost.
    """
    y = pd.Series(y_true).reset_index(drop=True)
    d = pd.Series(decisions).reset_index(drop=True)

    costs = np.zeros(len(y), dtype=float)

    # Missed default / False approval: Cost = 5
    false_approval_mask = (y == 1) & (d == "APPROVE")
    costs[false_approval_mask] = 5.0

    # Wrong denial: Cost = 1
    wrong_denial_mask = (y == 0) & (d == "DENY")
    costs[wrong_denial_mask] = 1.0

    total_cost = float(costs.sum())
    avg_cost = float(costs.mean()) if len(costs) > 0 else 0.0

    return CostResult(total_cost=total_cost, average_cost=avg_cost)


def summary_metrics(evaluated_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute summary performance and safety metrics for an evaluated dataset.

    Calculates:
        - total applicants
        - sent to humans (REVIEW count / total)
        - deferral rate
        - automatic coverage (decisions made without human review)
        - plain model classification cost
        - TrustLend automatic-decision classification cost
        - confidently wrong cases for plain model
        - confidently wrong cases for TrustLend automatic decisions

    'Confidently wrong' is defined as:
        - APPROVE with p_default > 0.90 when y_true == 1
        - DENY with p_default < 0.10 when y_true == 0
    """
    n_total = len(evaluated_df)
    if n_total == 0:
        return {
            "total_applicants": 0,
            "sent_to_humans": 0.0,
            "sent_to_humans_count": 0,
            "deferral_rate": 0.0,
            "automatic_coverage": 0.0,
            "plain_model_cost": 0.0,
            "plain_model_average_cost": 0.0,
            "trustlend_cost": 0.0,
            "trustlend_automatic_decision_cost": 0.0,
            "trustlend_average_cost": 0.0,
            "confidently_wrong_plain_model": 0,
            "confidently_wrong_trustlend": 0,
        }

    is_review = evaluated_df["decision"] == "REVIEW"
    review_count = int(is_review.sum())
    deferral_rate = float(review_count / n_total)
    automatic_coverage = float(1.0 - deferral_rate)

    # Plain model cost vs TrustLend automatic cost
    y_true = evaluated_df["y_true"]
    plain_cost_res = classification_cost(y_true, evaluated_df["model_says"])
    trustlend_cost_res = classification_cost(y_true, evaluated_df["decision"])

    p_def = evaluated_df["p_default"]
    model_says = evaluated_df["model_says"]
    decision = evaluated_df["decision"]

    # Confidently wrong cases for plain model
    cw_plain = (
        ((y_true == 1) & (model_says == "APPROVE") & (p_def > 0.90))
        | ((y_true == 0) & (model_says == "DENY") & (p_def < 0.10))
    )
    confidently_wrong_plain = int(cw_plain.sum())

    # Confidently wrong cases for TrustLend automatic decisions (excluding REVIEW)
    cw_tl = (
        ((y_true == 1) & (decision == "APPROVE") & (p_def > 0.90))
        | ((y_true == 0) & (decision == "DENY") & (p_def < 0.10))
    )
    confidently_wrong_trustlend = int(cw_tl.sum())

    return {
        "total_applicants": n_total,
        "sent_to_humans": deferral_rate,
        "sent_to_humans_count": review_count,
        "deferral_rate": deferral_rate,
        "automatic_coverage": automatic_coverage,
        "plain_model_cost": plain_cost_res.total_cost,
        "plain_model_average_cost": plain_cost_res.average_cost,
        "trustlend_cost": trustlend_cost_res.total_cost,
        "trustlend_automatic_decision_cost": trustlend_cost_res.total_cost,
        "trustlend_average_cost": trustlend_cost_res.average_cost,
        "confidently_wrong_plain_model": confidently_wrong_plain,
        "confidently_wrong_trustlend": confidently_wrong_trustlend,
        "plain_model": {
            "cost": plain_cost_res.total_cost,
            "average_cost": plain_cost_res.average_cost,
            "confidently_wrong": confidently_wrong_plain,
        },
        "trustlend": {
            "cost": trustlend_cost_res.total_cost,
            "average_cost": trustlend_cost_res.average_cost,
            "confidently_wrong": confidently_wrong_trustlend,
            "coverage": automatic_coverage,
            "deferral_rate": deferral_rate,
        },
    }


def evaluate_test_sets(
    familiar: pd.DataFrame,
    strangers: pd.DataFrame,
    corrupted: pd.DataFrame,
    decide_fn: Callable[[Dict[str, Any]], Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """
    Evaluate familiar, strangers, and corrupted datasets using decide_fn.

    Note on Corrupted Rows:
        The expected safe behavior for corrupted or adversarial inputs is
        REVIEW (human deferral). This function measures empirical behavior
        rather than assuming safe deferral occurred.

    Returns:
        Structured dictionary with sections 'familiar', 'strangers', 'corrupted'.
    """
    evaluated_familiar = evaluate_rows(familiar, decide_fn)
    evaluated_strangers = evaluate_rows(strangers, decide_fn)
    evaluated_corrupted = evaluate_rows(corrupted, decide_fn)

    return {
        "familiar": {
            "evaluated": evaluated_familiar,
            "summary": summary_metrics(evaluated_familiar),
            "deferral_rates": deferral_rates(evaluated_familiar),
        },
        "strangers": {
            "evaluated": evaluated_strangers,
            "summary": summary_metrics(evaluated_strangers),
            "deferral_rates": deferral_rates(evaluated_strangers),
        },
        "corrupted": {
            "evaluated": evaluated_corrupted,
            "summary": summary_metrics(evaluated_corrupted),
            "deferral_rates": deferral_rates(evaluated_corrupted),
        },
    }


def risk_coverage_curve(
    evaluated_df: pd.DataFrame,
    cutoff: float = 0.5,
    n_points: int = 100,
    seed: int = 42,
) -> pd.DataFrame:
    """
    Generate risk-coverage data for three decision deferral strategies:
        1. Random baseline:
           Randomly chooses applicants for automatic decision.
        2. Confidence only (Check 1 only):
           Orders applicants by confidence: larger |p_default - cutoff| is prioritized.
        3. TrustLend (Check 1 + Check 2):
           Prioritizes familiar applicants first (unfamiliar == False). Within each
           group, prioritizes applicants with higher confidence: larger |p_default - cutoff|.

    Coverage: Fraction of total applicants receiving an automatic decision.
    Risk: Average classification cost among automatically decided cases.

    Returns:
        Tidy pandas DataFrame with columns:
        ['strategy', 'coverage', 'num_decided', 'risk', 'total_cost']
    """
    n_total = len(evaluated_df)
    if n_total == 0:
        return pd.DataFrame(
            columns=["strategy", "coverage", "num_decided", "risk", "total_cost"]
        )

    # Compute individual applicant misclassification costs when decided by model_says
    y = evaluated_df["y_true"].to_numpy()
    m = evaluated_df["model_says"].to_numpy()
    p_def = evaluated_df["p_default"].to_numpy()
    unfam = evaluated_df["unfamiliar"].to_numpy()

    costs = np.zeros(n_total, dtype=float)
    costs[(y == 1) & (m == "APPROVE")] = 5.0
    costs[(y == 0) & (m == "DENY")] = 1.0

    confidence = np.abs(p_def - cutoff)

    # 1. Random ordering
    rng = np.random.default_rng(seed)
    random_order = rng.permutation(n_total)

    # 2. Confidence-only ordering (highest distance from cutoff first)
    conf_order = np.argsort(-confidence)

    # 3. TrustLend ordering:
    #    Primary key: familiar first (unfamiliar == False)
    #    Secondary key: highest confidence first
    #    lexsort sorts by last key first, so pass (secondary, primary):
    trustlend_order = np.lexsort((-confidence, unfam.astype(int)))

    # Coverage sample points (from 1 decided case to n_total cases)
    k_steps = np.unique(np.linspace(1, n_total, min(n_points, n_total), dtype=int))

    strategies = [
        ("Random Baseline", random_order),
        ("Confidence Only", conf_order),
        ("TrustLend", trustlend_order),
    ]

    records = []
    for strategy_name, order in strategies:
        ordered_costs = costs[order]
        cum_costs = np.cumsum(ordered_costs)

        for k in k_steps:
            tot_cost_k = float(cum_costs[k - 1])
            risk_k = tot_cost_k / float(k)
            cov_k = float(k / n_total)

            records.append(
                {
                    "strategy": strategy_name,
                    "coverage": cov_k,
                    "num_decided": int(k),
                    "risk": risk_k,
                    "total_cost": tot_cost_k,
                }
            )

    return pd.DataFrame(records)


def deferral_rates(evaluated_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate deferral rates overall, by age group, and by number-of-dependents group.

    Documented Bins:
        - Age: '<30', '30-44', '45-59', '60+'
        - NumberOfDependents: '0', '1', '2', '3+', 'Missing'

    Returns:
        Structured dictionary containing overall and subgroup deferral rates.
    """
    if len(evaluated_df) == 0:
        return {"overall": 0.0, "by_age": {}, "by_dependents": {}}

    is_review = evaluated_df["decision"] == "REVIEW"
    overall_rate = float(is_review.mean())

    # Age bands
    by_age: Dict[str, float] = {}
    if "age" in evaluated_df.columns:
        age_bins = [0, 30, 45, 60, 150]
        age_labels = ["<30", "30-44", "45-59", "60+"]
        binned_age = pd.cut(
            evaluated_df["age"],
            bins=age_bins,
            labels=age_labels,
            right=False,
        )
        for label in age_labels:
            mask = binned_age == label
            count = int(mask.sum())
            if count > 0:
                by_age[str(label)] = float(is_review[mask].mean())
            else:
                by_age[str(label)] = 0.0

    # Number of Dependents bands
    by_dependents: Dict[str, float] = {}
    if "NumberOfDependents" in evaluated_df.columns:
        deps = evaluated_df["NumberOfDependents"]

        # Missing
        missing_mask = deps.isna()
        if missing_mask.sum() > 0:
            by_dependents["Missing"] = float(is_review[missing_mask].mean())

        # Categorical numeric bands
        dep_conditions = [
            ("0", deps == 0),
            ("1", deps == 1),
            ("2", deps == 2),
            ("3+", deps >= 3),
        ]
        for label, cond in dep_conditions:
            mask = (~missing_mask) & cond
            if mask.sum() > 0:
                by_dependents[label] = float(is_review[mask].mean())
            else:
                by_dependents[label] = 0.0

    return {
        "overall": overall_rate,
        "by_age": by_age,
        "by_dependents": by_dependents,
    }
