import json
import os
import joblib
from sklearn.metrics import roc_auc_score
from src.data import load, split, TARGET
from src.model import train_model, risk
from src.familiarity import Familiarity
from src.policy import choose_thresholds

os.makedirs("artifacts", exist_ok=True)
train, val, test, strangers = split(load())
print("sizes:", len(train), len(val), len(test), len(strangers))

model = train_model(train)
fam = Familiarity().fit(train)

p_val = risk(model, val)
d_val, _ = fam.distance(val)             # validation, never train
print("validation AUC:", round(roc_auc_score(val[TARGET], p_val), 3))

T = choose_thresholds(p_val, d_val, val[TARGET].values)
print("thresholds:", T)

joblib.dump(model, "artifacts/model.joblib")
joblib.dump(fam, "artifacts/familiarity.joblib")
json.dump(T, open("artifacts/thresholds.json", "w"), indent=2)
