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

        print("Training and calibrating model...")
        model = train_model(train)

        print("Calculating validation AUC...")
        p_val = risk(model, val)
        auc = roc_auc_score(val[TARGET], p_val)

        print(f"\nSUCCESS! Model trained successfully.")
        print(f"Validation AUC: {auc:.4f}")

        os.makedirs("artifacts", exist_ok=True)
        artifact_path = "artifacts/model.joblib"
        joblib.dump(model, artifact_path)
        print(f"Trained model saved to {artifact_path}")
