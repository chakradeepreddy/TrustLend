import numpy as np
import pandas as pd

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


def load(path="data/cs-training.csv"):
    """
    Load the Give Me Some Credit dataset from CSV, set the index column,
    and remove the single row where age is 0.
    """
    df = pd.read_csv(path, index_col=0)
    df = df[df["age"] != 0]
    return df


def split(df, seed=42):
    """
    Split the dataset into familiar (train, val, test) and strangers (top 5% MonthlyIncome).
    """
    limit = df["MonthlyIncome"].quantile(0.95)

    strangers = df[df["MonthlyIncome"] > limit]
    familiar = df[df["MonthlyIncome"].isna() | (df["MonthlyIncome"] <= limit)]

    familiar_shuffled = familiar.sample(frac=1, random_state=seed)

    n = len(familiar_shuffled)
    n_train = int(0.60 * n)
    n_val = int(0.20 * n)

    train = familiar_shuffled.iloc[:n_train]
    val = familiar_shuffled.iloc[n_train:n_train + n_val]
    test = familiar_shuffled.iloc[n_train + n_val:]

    return train, val, test, strangers


def corrupt(rows, seed=0):
    """
    Apply one of three random corruption types to each row:
    - type 0: MonthlyIncome *= 1000
    - type 1: age *= 10
    - type 2: swap DebtRatio and MonthlyIncome
    """
    r = rows.copy()
    rng = np.random.default_rng(seed)

    corruption_types = rng.integers(0, 3, size=len(r))

    mask_0 = corruption_types == 0
    mask_1 = corruption_types == 1
    mask_2 = corruption_types == 2

    r.loc[mask_0, "MonthlyIncome"] = r.loc[mask_0, "MonthlyIncome"] * 1000
    r.loc[mask_1, "age"] = r.loc[mask_1, "age"] * 10

    if np.any(mask_2):
        debt_vals = r.loc[mask_2, "DebtRatio"].to_numpy()
        income_vals = r.loc[mask_2, "MonthlyIncome"].to_numpy()
        r.loc[mask_2, "DebtRatio"] = income_vals
        r.loc[mask_2, "MonthlyIncome"] = debt_vals

    return r
