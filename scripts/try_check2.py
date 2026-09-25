# scripts/try_check2.py   Run with: python -m scripts.try_check2
import numpy as np
from src.data import load, split
from src.familiarity import Familiarity

df = load()
train, val, test, strangers = split(df)
print("sizes:", len(train), len(val), len(test), len(strangers))

fam = Familiarity().fit(train)

d_val, _ = fam.distance(val)
d_strangers, _ = fam.distance(strangers)
print("val median distance:", round(np.median(d_val), 2))
print("strangers median distance:", round(np.median(d_strangers), 2))

applicant = df.loc[[34771]]
dist, _ = fam.distance(applicant)
print("applicant 34771 distance:", round(dist[0], 2))
print("applicant 34771 reasons:", fam.reasons(applicant.iloc[0]))
