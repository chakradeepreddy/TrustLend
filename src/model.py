"""
Chakradeep's loan model component for TrustLend / Second Look.
This module trains the baseline loan/default-risk model using a calibrated
HistGradientBoostingClassifier, calculates the cost-based cutoff, and
implements Check 1 (uncertainty detection).
"""

import os
import joblib
import pandas as pd
import numpy as np
from typing import Any
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression

# Cost constants for the bank
COST_MISSED_DEFAULT = 5
COST_WRONG_DENIAL = 1

# Cutoff calculation based on costs
# If p is risk of default, approve if expected loss of approval < expected loss of denial
# p * COST_MISSED_DEFAULT < (1 - p) * COST_WRONG_DENIAL
CUTOFF = COST_WRONG_DENIAL / (COST_MISSED_DEFAULT + COST_WRONG_DENIAL)  # 1/6 ~ 0.1667

TARGET = "SeriousDlqin2yrs"

# Actual column names verified from the CSV
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
    "NumberOfDependents"
]

def train_logistic_baseline(train: pd.DataFrame) -> Any:
    """
    Train a simple logistic regression baseline with median imputation and scaling.
    """
    pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler()),
        ('classifier', LogisticRegression(random_state=0, max_iter=1000))
    ])
    pipeline.fit(train[FEATURES], train[TARGET])
    return pipeline


def train_model(train: pd.DataFrame) -> Any:
    """
    Train the calibrated HistGradientBoostingClassifier.
    """
    model = CalibratedClassifierCV(
        estimator=HistGradientBoostingClassifier(random_state=0),
        method="isotonic",
        cv=5
    )
    model.fit(train[FEATURES], train[TARGET])
    return model


def risk(model: Any, X: pd.DataFrame) -> np.ndarray:
    """
    Return the predicted probability of default.
    """
    return model.predict_proba(X[FEATURES])[:, 1]


def plain_decision(p: float) -> str:
    """
    Return "DENY" when p >= CUTOFF, otherwise "APPROVE".
    """
    return "DENY" if p >= CUTOFF else "APPROVE"


def check1_unsure(p: float, band: float) -> bool:
    """
    Return True when the probability is too close to the cutoff, meaning Check 1 fails.
    """
    return abs(p - CUTOFF) < band


if __name__ == "__main__":
    # TEMPORARY DEVELOPMENT MODE
    import plotly.graph_objects as go
    from sklearn.calibration import calibration_curve

    # This block allows independent testing until src/data.py is implemented by Tanush.
    data_path = "data/cs-training.csv"

    if not os.path.exists(data_path):
        print(f"Error: Dataset not found at {data_path}. Please download it first.")
    else:
        print("Loading dataset...")
        df = pd.read_csv(data_path, index_col=0) # Index col is Unnamed: 0

        print("Creating temporary train/validation split...")
        # Note: This is a temporary split just to unblock model development.
        # It does NOT represent the final test/stranger/corrupted sets.
        train, val = train_test_split(df, stratify=df[TARGET], random_state=42)

        print("Training logistic baseline...")
        log_model = train_logistic_baseline(train)
        p_val_log = log_model.predict_proba(val[FEATURES])[:, 1]
        log_auc = roc_auc_score(val[TARGET], p_val_log)

        print("Training raw model...")
        raw_model = HistGradientBoostingClassifier(random_state=0)
        raw_model.fit(train[FEATURES], train[TARGET])
        p_val_raw = raw_model.predict_proba(val[FEATURES])[:, 1]
        raw_auc = roc_auc_score(val[TARGET], p_val_raw)

        print("Training and calibrating model...")
        model = train_model(train)
        p_val_calibrated = risk(model, val)
        calibrated_auc = roc_auc_score(val[TARGET], p_val_calibrated)

        print(f"\nLogistic baseline validation AUC: {log_auc:.4f}")
        print(f"Raw model validation AUC: {raw_auc:.4f}")
        print(f"Calibrated model validation AUC: {calibrated_auc:.4f}")

        print("\nCreating reliability diagram...")
        prob_true_raw, prob_pred_raw = calibration_curve(
            val[TARGET], p_val_raw, n_bins=10, strategy="uniform"
        )
        prob_true_cal, prob_pred_cal = calibration_curve(
            val[TARGET], p_val_calibrated, n_bins=10, strategy="uniform"
        )

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], mode="lines", name="Perfectly calibrated", line=dict(dash="dot", color="black")))
        fig.add_trace(go.Scatter(x=prob_pred_raw, y=prob_true_raw, mode="lines+markers", name="Raw model"))
        fig.add_trace(go.Scatter(x=prob_pred_cal, y=prob_true_cal, mode="lines+markers", name="Calibrated model"))

        fig.update_layout(
            title="Reliability Diagram: Raw vs Calibrated Default Probabilities",
            xaxis_title="Mean predicted probability",
            yaxis_title="Fraction of positives",
            width=800,
            height=600
        )

        os.makedirs("artifacts", exist_ok=True)
        chart_path = "artifacts/reliability_diagram.png"
        fig.write_image(chart_path)
        print(f"Reliability diagram saved to {chart_path}")

        artifact_path = "artifacts/model.joblib"
        joblib.dump(model, artifact_path)
        print(f"Trained calibrated model saved to {artifact_path}")
