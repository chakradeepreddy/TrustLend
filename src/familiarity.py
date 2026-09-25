import numpy as np
import pandas as pd
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import RobustScaler
from src.data import FEATURES

SKEWED = ["RevolvingUtilizationOfUnsecuredLines", "DebtRatio", "MonthlyIncome"]

class Familiarity:
    """Check 2: how far is this applicant from the people the AI learned from?"""

    def fit(self, train, k=10, ref_size=30_000, seed=0):
        ref = train.sample(min(ref_size, len(train)), random_state=seed)
        self.medians = ref[FEATURES].median()
        self.bounds = {c: (ref[c].quantile(0.005), ref[c].quantile(0.995))
                       for c in FEATURES}                  # for the reasons
        Z = self._prep(ref)
        self.scaler = RobustScaler().fit(Z)
        self.nn = NearestNeighbors(n_neighbors=k).fit(self.scaler.transform(Z))
        self.ref_rows = ref.reset_index(drop=True)
        return self

    def _prep(self, X):
        Z = X[FEATURES].copy()
        Z["income_missing"] = Z["MonthlyIncome"].isna().astype(float)
        Z = Z.fillna(self.medians)
        for c in SKEWED:                                   # squash huge values
            Z[c] = np.log1p(Z[c].clip(lower=0))
        return Z

    def distance(self, X):
        d, idx = self.nn.kneighbors(self.scaler.transform(self._prep(X)))
        return d.mean(axis=1), idx      # average distance to the 10 nearest

    def reasons(self, row):
        out = []
        for c in FEATURES:
            v = row[c]
            if pd.isna(v):
                continue
            lo, hi = self.bounds[c]
            if v > hi:
                out.append(f"{c} is higher than 99.5% of past applicants")
            elif v < lo:
                out.append(f"{c} is lower than 99.5% of past applicants")
        return out or ["Unusual combination of values, even though each one looks normal"]
